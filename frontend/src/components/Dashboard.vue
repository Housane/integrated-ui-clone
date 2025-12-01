<template>
  <div class="dashboard-page">
    <!--top header, title (investor dashboard) on LHS, profile on RHS-->
    <header class="dashboard-header">
      <div class="title-with-favourite">

        <h1 class="page-title">{{ symbolInput }} Details</h1>
        <button 
          class="favourite-btn"
          @click="toggleFavourite"
          :class="{ 'is-favourite': isFavourite }"
          :aria-label="isFavourite ? 'Remove from favourites' : 'Add to favourites'"
          :title="isFavourite ? 'Remove from favourites' : 'Add to favourites'"
        >
          {{ isFavourite ? '❤️' : '🤍' }}
        </button>

        <router-link 
          :to="{ 
            name: 'StockComments', 
            params: { symbol: symbolInput }
          }"
          class="comments-btn"
          title="See comments about this stock"
        >
          See Comments about This Stock
        </router-link>
      </div>
      
      <div class="profile-container">
        <button class="profile-button" @click="toggleProfile">
          My Profile
        </button>

          <div
            v-if="profileVisible"
            class="profile-menu"
            @click.self="closeDropdown"
          >
            <div class="profile-details">
              <p class="profile-line">
                <strong>User: </strong>
                <span>{{ currentUser?.email || 'No email available' }}</span>
              </p>
              <p class="profile-line">
                <strong>Member since: </strong>
                <span>{{ memberSince || 'Unknown' }}</span>
              </p>
              <p class="profile-line" v-if="userProfile?.themePreference">
                <strong>Theme: </strong>
                <span>{{userProfile.themePreference }}</span>
              </p>

              <button
                class="profile-nav-button"
                @click="goToProfile"
              >
                View Profile
              </button>

              <button
                class="logout-button"
                @click="handleLogout"
                :disabled="loggingOut"
              >
                <span v-if="!loggingOut">Log Out</span>
                <span v-else>Logging out...</span>
              </button>
            </div>
          </div>
        </div>
      </header>

    <!--main dashboard area -->
    <section class="dashboard-content">
      <p>Welcome to your dashboard{{ userGreeting }}!</p>

      <!-- back to home button -->
      <div class="back-to-home">
        <button @click="goToHome" class="home-button">
          <span>← Back to Home</span>
        </button>
      </div>

      <!--ai pred panel-->
      <div class="prediction-panel">
        <h3>AI Stock Prediction</h3>
        <div class="prediction-controls">
          <button
            @click="getPrediction"
            :disabled="loadingPrediction"
            class="predict-button"
          >
          <!--if its loading-->
            <span v-if="!loadingPrediction">Get AI Prediction for {{ symbolInput }}</span>
            <span v-else>Analysing...</span>
          </button>
        </div>

        <!--if prediction is produced, show the scores-->
        <div v-if="predictionResult" class="prediction-result">
          <div class="prediction-header">
            <h4>Prediction for {{ predictionResult.symbol }}</h4>
            <span class="timestamp">{{ formatTimestamp(predictionResult.timestamp) }}</span>
          </div>

          <div class="prediction-main">
            <div :class="['prediction-badge', predictionResult.prediction.toLowerCase()]">
              {{ predictionResult.prediction }}
            </div>
            <div class="confidence-score"> <!-- Replaced with Probability for clarity -->
              Probability: {{ (predictionResult.confidence_scores[predictionResult.prediction] * 100).toFixed(1) }}%
            </div>
          </div>

          <div class="confidence-breakdown">
            <h5>Confidence Breakdown:</h5> <!-- Left like this in this case for clarity -->
            <div class="confidence-bars">
              <div v-for="(score, action) in predictionResult.confidence_scores" :key="action" class="confidence-bar">
                <span class="action-label">{{ action }}</span>
                <div class="bar-container">
                  <div
                    class="bar-fill"
                    :style="{ width: (score * 100) + '%' }"
                    :class="action.toLowerCase()"
                  ></div>
                </div>
                <span class="score-label">{{ (score * 100).toFixed(1) }}%</span>
              </div>
            </div>
          </div>
        </div>

        <!-- structure of the above: 
          "BUY": 0.75, with bars            
          "HOLD": 0.20,             
          "SELL": 0.05  
        -->

        <div v-if="predictionError" class="prediction-error">
          <h4> Prediction Error</h4>
          <p>{{ predictionError }}</p>
          <button @click="predictionError = null" class="dismiss-error">Dismiss</button>
        </div>
      </div>

      <!--price panel-->
      <div
        id="symbol-info-widget"
        class="symbol-info-container"
      ></div>

      <!--trading chart -->
      <div
        id="tradingview-widget"
        class="dashboard-image"
      ></div>

      <!--market news remember to convert symbol to all caps-->
      <section class="market-news">
        <h2 class="news-title">Related News for {{ symbolInput.toUpperCase() }}</h2>
        <div
          v-if="loadingNews"
          class="news-loading"
        >Loading news...</div>
        <div v-else>
          <div
            v-if="newsError"
            class="news-error">Failed to load news: {{ newsError }}
          </div>
          <div
            v-else
            class="news-grid"
          >
            <div v-for="item in stockNews" :key="item.link" class="news-card">
              <div class="news-thumb">
                <img :src="item.image || placeholderImage" alt="" />
              </div>
              <div class="news-content">
                <a :href="item.link" target="_blank" class="news-headline">{{ item.title }}</a>
                <p class="news-meta">{{ item.source }} • {{ item.timeAgo }}</p>
                <p v-if="item.sentiment !== null && !item.sentimentLoading" class="news-sentiment">
                  Sentiment Score: {{ item.sentiment.toFixed(2) }}
                </p>
                <p v-else-if="item.sentimentLoading" class="news-sentiment">Analysing sentiment...</p>
              </div>
            </div>
          </div>
        </div>
      </section>
    </section>
  </div>
</template>


<script>


import { ref, onMounted, onBeforeUnmount, computed, watch } from 'vue';
import axios from 'axios';
import { auth, db } from '../firebase';
import { onAuthStateChanged, signOut } from 'firebase/auth';
import { doc, getDoc, updateDoc, arrayUnion, arrayRemove } from 'firebase/firestore';
import { useRouter, useRoute } from 'vue-router';
import { initTheme, applyTheme } from '@/ThemeManager';

const apiBase = import.meta.env.VITE_API_BASE_URL;

export default {
  name: 'Dashboard',
  setup() {
    const router = useRouter();
    const route = useRoute();
    const currentUser = ref(null);
    const memberSince = ref('');
    const profileVisible = ref(false);
    const loggingOut = ref(false);
    const userProfile = ref(null);
    let unsubscribeAuth;

    const isFavourite = ref(false);
    const checkingFavourite = ref(false);

    const symbolInput = ref('SPY');
    const stockNews = ref([]);
    const loadingNews = ref(false);
    const newsError = ref('');
    const placeholderImage = '/placeholder.png';

    //default state for prediction 
    const predictionResult = ref(null);
    const predictionError = ref('');
    const loadingPrediction = ref(false);

    function formatTimeAgo(datetime) {
      // finnhub timestamp
      const diff = (Date.now() - new Date(datetime)) / 1000;
      if (diff < 60) return `${Math.floor(diff)}s ago`;
      if (diff < 3600) return `${Math.floor(diff / 60)}m ago`;
      if (diff < 86400) return `${Math.floor(diff / 3600)}h ago`;
      return `${Math.floor(diff / 86400)}d ago`;
    }

    function formatTimestamp(timestamp) {
      return new Date(timestamp).toLocaleString();
    }

    function goToHome() {
      router.push('/general');
    }

    async function checkFavouriteStatus() {
      if (!currentUser.value || !symbolInput.value) return;
      
      checkingFavourite.value = true;
      try {
        const userRef = doc(db, 'Investors', currentUser.value.uid);
        const userSnap = await getDoc(userRef);
        
        if (userSnap.exists() && userSnap.data().favourites) {
          const favourites = userSnap.data().favourites;
          isFavourite.value = favourites.some(fav => 
            fav.symbol.toLowerCase() === symbolInput.value.toLowerCase()
          );
        } else {
          isFavourite.value = false;
        }
      } catch (error) {
        console.error('Error checking favourite status:', error);
        isFavourite.value = false;
      } finally {
        checkingFavourite.value = false;
      }
    }

async function toggleFavourite() {
  if (!currentUser.value) {
    router.push('/login');
    return;
  }
  
  try {
    const userRef = doc(db, 'Investors', currentUser.value.uid);
    const userSnap = await getDoc(userRef);

    if (!userSnap.exists()) {
      console.error("User document doesn't exist");
      return;
    }

    let favourites = userSnap.data().favourites || [];

    const symbol = symbolInput.value.trim().toUpperCase();

    const existing = favourites.find(fav => fav.symbol.toUpperCase() === symbol);

    if (existing) {
      await updateDoc(userRef, {
        favourites: favourites.filter(fav => fav.symbol.toUpperCase() !== symbol)
      });
      isFavourite.value = false;
    } else {
      const newStock = {
        symbol,
        name: symbol, 
        addedAt: new Date().toISOString()
      };
      await updateDoc(userRef, {
        favourites: [...favourites, newStock]
      });
      isFavourite.value = true;
    }
  } catch (error) {
    console.error('Error updating favourites:', error);
  }
}


    // ai pred function 
    async function getPrediction() {
      if (!symbolInput.value) return;

      if (!/^[A-Z]{1,6}$/.test(symbolInput.value.trim())) {
        predictionError.value = 'Please enter a valid ticker symbol (1-6 uppercase letters, e.g. AAPL, MSFT, GOOGL)';
        return;
      }

      loadingPrediction.value = true;
      predictionError.value = '';
      predictionResult.value = null;

      try {
        const response = await axios.post(
          `${apiBase}/predict/`,
          //'http://127.0.0.1:8000/api/predict/',
          { symbol: symbolInput.value.trim().toUpperCase() },
          { timeout: 30000 } 
        );

        predictionResult.value = response.data;
        console.log('Prediction result:', response.data);

      } catch (error) {
        console.error('Prediction error:', error);
        if (error.response?.data?.error) {
          predictionError.value = error.response.data.error;
        } else if (error.code === 'ECONNABORTED') {
          predictionError.value = 'Request timeout. Please try again.';
        } else {
          predictionError.value = 'Unable to get prediction. Please try again later.';
        }
      } finally {
        loadingPrediction.value = false;
      }
    }

    //fetching news 
    async function fetchNews(timeWindowHours = 12, adjustAttempted = false) {
      if (!symbolInput.value) return;
      loadingNews.value = true;
      newsError.value = '';
      try {
        const apiKey = import.meta.env.VITE_FINNHUB_API_KEY;
        const now = new Date();
        const windowAgo = new Date(now.getTime() - timeWindowHours * 60 * 60 * 1000);

        const fromStr = windowAgo.toISOString().split('T')[0];
        const toStr = now.toISOString().split('T')[0];
        const resp = await axios.get('https://finnhub.io/api/v1/company-news', {
          params: {
            symbol: symbolInput.value,
            from: fromStr,
            to: toStr,
            token: apiKey
          }
        });

        //only include news from last 12/24 hrs
        let newsArr = resp.data
          .filter(a => {
            const newsTimeMs = a.datetime * 1000;
            return newsTimeMs >= windowAgo.getTime();
          })
          .map(a => ({
            title: a.headline,
            link: a.url,
            source: a.source,
            timeAgo: formatTimeAgo(a.datetime * 1000),
            image: a.image,
            summary: a.summary,
            sentiment: null,
            sentimentLoading: true
          }));

        //  window adjustment only once 
        if (!adjustAttempted) {
          if (newsArr.length > 10 && timeWindowHours > 6) {
            await fetchNews(6, true);
            return;
          }
          if (newsArr.length < 3 && timeWindowHours < 24) {
            await fetchNews(24, true);
            return;
          }
        }

        stockNews.value = newsArr;

        // for each news, call sentiment api
        await Promise.all(newsArr.map(async (item, idx) => {
          try {
            const sentimentResp = await axios.post(
              `${apiBase}/sentiment/`, //for local deployment, change all of these back to http://127.0.0.1:8000/api/sentiment/
              //'http://127.0.0.1:8000/api/sentiment/',
              {
                headline: item.title,
                summary: item.summary
              }
            );
            //stockNews.value[idx].sentiment = sentimentResp.data.final_sentiment_score;
            //stockNews.value[idx].sentimentLoading = false;
            stockNews.value.splice(idx, 1, {
              ...stockNews.value[idx],
              sentiment: sentimentResp.data.final_sentiment_score,
              sentimentLoading: false
            });

          } catch (e) {
            //stockNews.value[idx].sentiment = null;
            //stockNews.value[idx].sentimentLoading = false;
            stockNews.value.splice(idx, 1, {
              ...stockNews.value[idx],
              sentiment: null,
              sentimentLoading: false
            });
          }
        }));

      } catch (err) {
        console.error('Error fetching news:', err);
        newsError.value = err.message;
      } finally {
        loadingNews.value = false;
      }
    }

    function loadWidget() {
      if (typeof TradingView === 'undefined') return;
      const chartEl = document.getElementById('tradingview-widget');
      if (!chartEl) {
        console.warn('TradingView widget container not found');
        return;
      }
      chartEl.innerHTML = '';
      
      const theme = document.documentElement.getAttribute('data-theme') === 'dark' ? 'dark' : 'light';
      
      new TradingView.widget({
        container_id: 'tradingview-widget',
        autosize: true,
        symbol: symbolInput.value,
        interval: 'D',
        timezone: 'America/New_York', 
        theme: theme,
        style: '1',
        locale: 'en',
        toolbar_bg: theme === 'dark' ? '#333333' : '#f1f3f6',
        enable_publishing: false,
        allow_symbol_change: true,
        withdateranges: true,
        hide_side_toolbar: false,
        save_image: false,
      });
    }

    //stock price panel 
    function loadSymbolInfo() {
      const container = document.getElementById('symbol-info-widget');
      if (!container) {
        console.warn('Symbol info widget container not found');
        return;
      }
      container.innerHTML = '';
      
      const theme = document.documentElement.getAttribute('data-theme') === 'dark' ? 'dark' : 'light';

      const script = document.createElement('script');
      script.src = 'https://s3.tradingview.com/external-embedding/embed-widget-symbol-info.js';
      script.async = true;
      script.innerHTML = JSON.stringify({
        symbol: symbolInput.value,
        width: '100%',
        height: '120',
        locale: 'en',
        colorTheme: theme,
        isTransparent: false });
      container.appendChild(script);
    }

    function updateWidget() {
      loadSymbolInfo();
      loadWidget();
      fetchNews();
    }

    function injectTradingViewScript() {
      if (document.getElementById('tradingview-script')) {
        updateWidget();
        return; }
      const s = document.createElement('script');
      s.id = 'tradingview-script';
      s.src = 'https://s3.tradingview.com/tv.js';
      s.async = true;
      s.onload = () => updateWidget();
      document.head.appendChild(s);
    }

    const userGreeting = computed(() => userProfile.value?.firstname ? `, ${userProfile.value.firstname}` : '');
    function formatDate(iso) {
      const dt = new Date(iso);
      return `${String(dt.getDate()).padStart(2,'0')}/${String(dt.getMonth()+1).padStart(2,'0')}/${String(dt.getFullYear()).slice(-2)}`;
    }

    async function fetchUserProfile() {
      if (!currentUser.value) return;
      try {
        const docRef = doc(db, 'Investors', currentUser.value.uid);
        const snap = await getDoc(docRef);
        if (snap.exists()) {
          userProfile.value = snap.data();
          
          //if theme preference is set, apply it
          if (userProfile.value.themePreference) {
            applyTheme(userProfile.value.themePreference);
            //reload widget to apply theme 
            if (document.getElementById('tradingview-script')) {
              setTimeout(updateWidget, 300); //set time for theme to change 
            }
          }
        }
      } catch (err) {
        console.error("Error fetching user profile:", err);
      }
    }

    function goToProfile() {
      profileVisible.value = false;
      router.push('/account-settings');
    }

    function toggleProfile() {
      profileVisible.value = !profileVisible.value;
    }

    function closeDropdown() {
      profileVisible.value = false;
    }
    async function handleLogout() {
      loggingOut.value = true;
      await signOut(auth);
      router.push('/login');
      loggingOut.value = false;
    }

    // important, need this observer so that the widgets and graph will also change colour!
    const observeThemeChanges = () => {
      const observer = new MutationObserver((mutations) => {
        mutations.forEach((mutation) => {
          if (mutation.attributeName === 'data-theme') {
            if (document.getElementById('tradingview-script')) {
              setTimeout(updateWidget, 300); //update widgets when theme changes
            }
          }
        });
      });
      
      observer.observe(document.documentElement, { attributes: true });
      
      return () => observer.disconnect();
    };

    watch(symbolInput, () => {
      if (currentUser.value) {
        checkFavouriteStatus();
      }
    });

    onMounted(() => {
      unsubscribeAuth = onAuthStateChanged(auth, async user => {
        if (user) {
          currentUser.value = user;
          memberSince.value = formatDate(user.metadata.creationTime);
          await fetchUserProfile();
          checkFavouriteStatus();
        } else {
          currentUser.value = null;
          userProfile.value = null;
          memberSince.value = "";
          isFavourite.value = false;
        }
      });

      //check if we have a symbol from the query parameters
      if (route.query.symbol) {
        symbolInput.value = route.query.symbol;
        if (currentUser.value) {
          checkFavouriteStatus();
        }
      }

      injectTradingViewScript();
      
      //use the observer here 
      const cleanupObserver = observeThemeChanges();
      
      return () => {
        if (cleanupObserver) cleanupObserver();
      };
    });

    watch(symbolInput, () => {
      if (currentUser.value) {
        checkFavouriteStatus();
      }
    });

    onBeforeUnmount(() => unsubscribeAuth && unsubscribeAuth());

    return {
      currentUser,
      memberSince,
      profileVisible,
      loggingOut,
      userGreeting,
      userProfile,
      toggleProfile,
      closeDropdown,
      handleLogout,
      goToProfile,
      goToHome,
      symbolInput,
      stockNews,
      loadingNews,
      newsError,
      updateWidget,
      placeholderImage,
      predictionResult,
      predictionError,
      loadingPrediction,
      getPrediction,
      formatTimestamp,
      isFavourite,
      toggleFavourite,
    };
  }
};
</script>



<style scoped>
.dashboard-page { 
  display: flex;
  flex-direction: column;
  min-height: 100vh;
  background-color: var(--color-background);
  color: var(--color-text-primary);
}

.title-with-favourite {
  display: flex;
  align-items: center;
  gap: 12px;
}

.favourite-btn {
  background: transparent;
  border: none;
  cursor: pointer;
  padding: 5px;
  font-size: 1.4rem;
  color: var(--color-text-primary);
  transition: transform 0.2s, color 0.2s;
  display: flex;
  align-items: center;
  justify-content: center;
}

.favourite-btn:hover {
  transform: scale(1.2);
}

.favourite-btn.is-favourite {
  color: var(--color-danger); 
}

.dashboard-header { /*dashboard header only*/
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 16px 24px;
  background-color: var(--color-primary);
  position: sticky;
  top: 0;
  z-index: 100;
  width: 100%;
  box-sizing: border-box;
}

.page-title {
  font-size: 20px;
  margin: 0;
  color: var(--color-text-primary);
}

.profile-container {
  position: relative;
}

.profile-button {
  background: none;
  border: 2px solid var(--color-text-primary);
  border-radius: 4px;
  padding: 6px 10px;
  cursor: pointer;
  font-size: 17px;
  transition: background-color 0.2s;
  color: var(--color-text-primary);
}

.profile-button:hover {
  background-color: rgba(255, 255, 255, 0.1);
}

.profile-menu {
  position: absolute;
  right: 0;
  top: calc(100% + 8px);
  width: 220px;
  background-color: var(--color-surface);
  border: 1px solid var(--color-border);
  border-radius: 4px;
  z-index: 100;
  box-shadow: 0 2px 10px var(--color-card-shadow);
}

.profile-details {
  padding: 18px;
}

.profile-line {
  margin: 8px 0;
  font-size: 13px;
  color: var(--color-text-primary);
}

.profile-nav-button {
  margin-top: 8px;
  margin-bottom: 8px;
  width: 100%;
  background-color: var(--color-primary);
  color: var(--color-text-primary);
  border: none;
  padding: 8px;
  border-radius: 4px;
  cursor: pointer;
  font-size: 0.9rem;
  transition: background-color 0.2s;
}

.profile-nav-button:hover {
  background-color: var(--color-primary-hover);
}

/* use colour danger so that it changes when its dark or light mode*/ 
.logout-button {
  margin-top: 4px;
  width: 100%;
  background-color: var(--color-danger);
  color: #fff;
  border: none;
  padding: 8px;
  border-radius: 4px;
  cursor: pointer;
  font-size: 0.9rem;
  transition: background-color 0.2s;
}

.logout-button:hover:not(:disabled) {
  background-color: var(--color-danger-hover);
}

.logout-button:disabled {
  opacity: 0.6;
  cursor: not-allowed;
}

.dashboard-content { 
  flex: 1;
  padding: 14px;
}


.back-to-home {
  margin: 16px 0;
  display: flex;
  justify-content: flex-start;
}

.home-button {
  padding: 8px 16px;
  font-size: 16px;
  background-color: var(--color-input-bg);
  color: var(--color-text-primary);
  border: 1px solid var(--color-border);
  border-radius: 4px;
  cursor: pointer;
  transition: background-color 0.2s;
  display: flex;
  align-items: center;
}

.home-button:hover {
  background-color: var(--color-border);
}

.prediction-panel {
  background: var(--color-secondary);
  border-radius: 12px;
  padding: 24px;
  margin: 20px 0;
  color: white;
  box-shadow: 0 8px 32px var(--color-card-shadow);
}

.prediction-panel h3 {
  margin: 0 0 16px 0;
  font-size: 20px;
  font-weight: bold;
}

.prediction-controls {
  margin-bottom: 20px;
}

.predict-button {
  background: rgba(255,255,255,0.2);
  border: 2px solid rgba(255,255,255,0.3);
  color: white;
  padding: 12px 24px;
  border-radius: 8px;
  cursor: pointer;
  font-size: 16px;
  font-weight: 500;
  transition: all 0.3s ease;
}

.predict-button:hover:not(:disabled) {
  background: rgba(255,255,255,0.3);
  border-color: rgba(255,255,255,0.5);
  transform: translateY(-2px);
}

.predict-button:disabled {
  opacity: 0.6;
  cursor: not-allowed;
  transform: none;
}

.prediction-result {
  background: rgba(255,255,255,0.1);
  border-radius: 8px;
  padding: 20px;
  margin-top: 16px;
}

.prediction-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 16px;
}

.prediction-header h4 {
  margin: 0;
  font-size: 18px;
}

.timestamp {
  font-size: 12px;
  opacity: 0.8;
}

.prediction-main {
  display: flex;
  align-items: center;
  gap: 16px;
  margin-bottom: 20px;
}

.prediction-badge {
  font-size: 24px;
  font-weight: bold;
  padding: 8px 16px;
  border-radius: 6px;
  text-transform: uppercase;
}

.prediction-badge.buy {
  background-color: #27ae60;
  color: white;
}

.prediction-badge.hold {
  background-color: #f39c12;
  color: white;
}

.prediction-badge.sell {
  background-color: #e74c3c;
  color: white;
}

.confidence-score {
  font-size: 16px;
  font-weight: 500;
}

.confidence-breakdown h5 {
  margin: 0 0 12px 0;
  font-size: 14px;
  opacity: 0.9;
}

.confidence-bars {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.confidence-bar {
  display: flex;
  align-items: center;
  gap: 12px;
}

.action-label {
  min-width: 50px;
  font-size: 12px;
  font-weight: 500;
}

/*confidence levels presentation, background, shadows and texts need to be dynamic in colour for theme*/

.bar-container {
  flex: 1;
  height: 20px;
  background: rgba(255,255,255,0.2);
  border-radius: 10px;
  overflow: hidden;
}

.bar-fill {
  height: 100%;
  border-radius: 10px;
  transition: width 0.5s ease;
}

.bar-fill.buy {
  background-color: #27ae60;
}

.bar-fill.hold {
  background-color: #f39c12;
}

.bar-fill.sell {
  background-color: #e74c3c;
}

.score-label {
  min-width: 45px;
  font-size: 12px;
  text-align: right;
}

.prediction-error {
  background: rgba(231, 76, 60, 0.2);
  border: 1px solid rgba(231, 76, 60, 0.5);
  border-radius: 8px;
  padding: 16px;
  margin-top: 16px;
}

.prediction-error h4 {
  margin: 0 0 8px 0;
  color: #e74c3c;
}

.dismiss-error {
  background: #e74c3c;
  color: white;
  border: none;
  padding: 6px 12px;
  border-radius: 4px;
  cursor: pointer;
  margin-top: 8px;
}

.symbol-info-container {
  width: 560px;
  margin: 16px 0;
}

.dashboard-image {
  width: 80vw; 
  height: 600px;
  margin: 28px auto 0;
  border: 1px solid var(--color-border);
  border-radius: 4px;
  overflow: hidden;
}

.market-news {
  padding: 0 14px;
  margin-top: 2rem;
}

.news-title {
  color: var(--color-text-primary);
}

.news-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(280px, 1fr));
  gap: 1rem;
}

.news-card {
  display: flex;
  background: var(--color-surface);
  border-radius: 8px;
  overflow: hidden;
  box-shadow: 0 2px 8px var(--color-card-shadow);
  transition: transform 0.2s;
}

.news-card:hover {
  transform: translateY(-4px);
}

.news-thumb img {
  width: 100px;
  height: 100px;
  object-fit: cover;
}

.news-content {
  padding: 0.75rem;
  display: flex;
  flex-direction: column;
  justify-content: space-between;
}

.news-headline {
  font-size: 1rem;
  font-weight: 500;
  color: var(--color-secondary);
  line-height: 1.2;
  margin-bottom: 0.5rem;
  text-decoration: none;
}

.news-headline:hover {
  text-decoration: underline;
}

.news-meta {
  font-size: 0.8rem;
  color: var(--color-text-secondary);
}

.news-sentiment {
  font-size: 0.92rem;
  color: var(--color-text-secondary);
  margin-top: 0.2rem;
}

.news-loading,
.news-error {
  text-align: center;
  padding: 32px;
  color: var(--color-text-primary);
  flex: 1;
  display: flex;
  align-items: center;
  justify-content: center;
  min-height: 250px;
}

.comments-btn {
  background: transparent;
  border: 2px solid var(--color-text-primary);
  border-radius: 4px;
  padding: 6px 12px;
  margin-left: 16px;
  cursor: pointer;
  font-size: 14px;
  color: var(--color-text-primary);
  text-decoration: none;
  display: flex;
  align-items: center;
  gap: 6px;
  transition: background-color 0.2s;
}

.comments-btn:hover {
  background-color: rgba(255, 255, 255, 0.1);
}

/* for smaller screens like phone */
@media (max-width: 768px) {
  .news-grid {
    grid-template-columns: 1fr;
  }
 
  .symbol-info-container {
    width: 100%;
  }
  
  .dashboard-image {
    width: 100%;
    height: 400px;
  }
}
</style>