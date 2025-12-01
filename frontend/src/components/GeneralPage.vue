<template>
  <div class="general-page">
    <header class="dashboard-header">
      <h1 class="page-title">Stock Market News</h1>
      <div class="profile-container">

        <button 
          class="favourites-button"
          @click="goToFavourites"
          title="View My Favourites"
          aria-label="View My Favourites"
        >
          View My Favourites
        </button>


        <button class="profile-button" @click="toggleProfile">
          My Profile
        </button>

        <!--dropdown for profile details n click to see full profile-->
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
              <span>{{ userProfile.themePreference }}</span>
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

    <!--search button, need a func to push router to dashboard-->
    <section class="search-section">
      <div class="search-container">
        <input
          v-model="searchQuery"
          @keyup.enter="handleSearch" 
          @focus="showSearchHint = true"
          @blur="showSearchHint = false"
          placeholder="Search for a stock ticker symbol (e.g. AAPL, MSFT, GOOG)"
          class="search-input" />

         <div v-if="showSearchHint" class="search-hint-popup">
          <div class="hint-content">
            <p><strong>Please only input valid ticker symbols, not full company names</strong></p>
            <p>Example: MSFT (not Microsoft)!</p>
          </div>
         </div> 


        <!--it needs to work both when u click enter and the button -->
        <button
          @click="handleSearch"
          class="search-button"
        >
          Search
        </button>
      </div>
    </section>

    <!--market summary of stocks for birds eye view-->
    <section class="market-summary">
      <h2>Market Summary</h2>
      <div class="market-indices">
        <div class="index-card">
          <h3>S&P 500</h3>
          <p class="index-price">4,765.21</p>
          <p class="index-change positive">+0.45%</p>
        </div>
        <div class="index-card">
          <h3>Dow Jones</h3>
          <p class="index-price">38,173.09</p>
          <p class="index-change positive">+0.28%</p>
        </div>
        <div class="index-card">
          <h3>NASDAQ</h3>
          <p class="index-price">16,584.41</p>
          <p class="index-change positive">+0.65%</p>
        </div>
        <div class="index-card">
          <h3>Russell 2000</h3>
          <p class="index-price">2,082.62</p>
          <p class="index-change negative">-0.22%</p>
        </div>
      </div>
    </section>

    <!--news section before searching, general news-->
    <section class="general-news">
      <h2>Top Market News</h2>

      <!--what happens if its still loading? need placeholder here-->
      <div
        v-if="loadingNews"
        class="news-loading"
      >Loading news...</div>
      <div v-else>
        <!--edge case news got error-->
        <div
          v-if="newsError"
          class="news-error"
        >Failed to load news: {{ newsError }}
      </div>
        <div
          v-else
          class="news-grid"
        >
          <div v-for="item in generalNews" :key="item.link" class="news-card">
            <div class="news-thumb">
              <img :src="item.image || placeholderImage" alt="" />
            </div>
            
            <!--how the news card should look like-->
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

    <!--trending stocks different from market summary!-->
    <section class="trending-stocks">
      <h2>Trending Stocks</h2>
      <div class="stock-cards">
        <div class="stock-card">
          <div class="stock-header">
            <h3>AAPL</h3>
            <p>Apple Inc.</p>
          </div>
          <p class="stock-price">187.42</p>
          <p class="stock-change positive">+1.72 (+0.93%)</p>
        </div>
        <div class="stock-card">
          <div class="stock-header">
            <h3>MSFT</h3>
            <p>Microsoft Corp.</p>
          </div>
          <p class="stock-price">421.18</p>
          <p class="stock-change positive">+3.54 (+0.85%)</p>
        </div>
        <div class="stock-card">
          <div class="stock-header">
            <h3>TSLA</h3>
            <p>Tesla, Inc.</p>
          </div>
          <p class="stock-price">184.47</p>
          <p class="stock-change negative">-2.36 (-1.26%)</p>
        </div>
        <div class="stock-card">
          <div class="stock-header">
            <h3>AMZN</h3>
            <p>Amazon.com, Inc.</p>
          </div>
          <p class="stock-price">178.62</p>
          <p class="stock-change positive">+1.95 (+1.10%)</p>
        </div>
      </div>
    </section>
  </div>
</template>

<script>
import { ref, onMounted, onBeforeUnmount, computed } from 'vue';
import axios from 'axios';
import { auth, db } from '../firebase';
import { onAuthStateChanged, signOut } from 'firebase/auth';
import { doc, getDoc } from 'firebase/firestore';
import { useRouter } from 'vue-router';
import { applyTheme } from '@/ThemeManager';

export default {
  name: 'GeneralPage',
  setup() {
    const router = useRouter();
    const currentUser = ref(null);
    const memberSince = ref('');
    const profileVisible = ref(false);
    const loggingOut = ref(false);
    const userProfile = ref(null);
    let unsubscribeAuth;

    const searchQuery = ref('');
    const generalNews = ref([]);
    const loadingNews = ref(false);
    const newsError = ref('');
    const placeholderImage = '/placeholder.png';
    const showSearchHint = ref(false);

    function goToFavourites() {
      router.push('/favourites');
    }

    
    function formatTimeAgo(datetime) {
      //news timestamps
      const diff = (Date.now() - new Date(datetime)) / 1000;
      if (diff < 60) return `${Math.floor(diff)}s ago`;
      if (diff < 3600) return `${Math.floor(diff / 60)}m ago`;
      if (diff < 86400) return `${Math.floor(diff / 3600)}h ago`;
      return `${Math.floor(diff / 86400)}d ago`;
    }

    //handleSearch must redirect to dashboard after enter 
    function handleSearch() {
      const query = searchQuery.value.trim().toUpperCase()

      if (!query) return;

    if (!/^[A-Z]{1,6}$/.test(query)) {
      alert('Please enter a valid ticker symbol (1-6 uppercase letters, e.g. AAPL, MSFT, GOOG)');
      return;
    }

      router.push({
        path: '/dashboard',
        query: { symbol: query }
      });
    }

    //fetch general market news
    async function fetchGeneralMarketNews() {
      loadingNews.value = true;
      newsError.value = '';
      try {
        const apiKey = import.meta.env.VITE_FINNHUB_API_KEY;
        const now = new Date();
        const twoDaysAgo = new Date(now.getTime() - 2 * 24 * 60 * 60 * 1000);

        const fromStr = twoDaysAgo.toISOString().split('T')[0];
        const toStr = now.toISOString().split('T')[0];

        //use market news instead of specific stock news
        const resp = await axios.get('https://finnhub.io/api/v1/news', {
          params: {
            category: 'general',
            from: fromStr,
            to: toStr,
            token: apiKey
          }
        });

        //process news data
        let newsArr = resp.data
          .slice(0, 12) //limit 12 items 
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

        generalNews.value = newsArr;

        //for each news, call sentiment api
        //const apiBase = import.meta.env.VITE_API_BASE_URL;
        await Promise.all(newsArr.map(async (item, idx) => {
          try {
            const sentimentResp = await axios.post(
              //'http://127.0.1:8000/api/sentiment/',
              `${apiBase}/sentiment/`,
              {
                headline: item.title,
                summary: item.summary
              }
            );
            //add sentiment score to news
            generalNews.value[idx].sentiment = sentimentResp.data.final_sentiment_score;
            generalNews.value[idx].sentimentLoading = false;
          } catch (e) {
            generalNews.value[idx].sentiment = null;
            generalNews.value[idx].sentimentLoading = false;
          }
        }));
      } catch (err) {
        console.error('Error fetching general news:', err);
        newsError.value = err.message;
      } finally {
        loadingNews.value = false;
      }
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
          
          // Apply theme if available in profile
          if (userProfile.value.themePreference) {
            applyTheme(userProfile.value.themePreference);
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

    //change boolean here 
    function toggleProfile() {
      profileVisible.value = !profileVisible.value;
    }

    //sset boolean to false 
    function closeDropdown() {
      profileVisible.value = false;
    }

    async function handleLogout() {
      loggingOut.value = true;
      await signOut(auth);
      router.push('/login');
      loggingOut.value = false;
    }

    onMounted(() => {
      unsubscribeAuth = onAuthStateChanged(auth, async user => {
        if (user) {
          currentUser.value = user;
          memberSince.value = formatDate(user.metadata.creationTime);
          await fetchUserProfile();
        } else {
          currentUser.value = null;
          userProfile.value = null;
          memberSince.value = "";
        }
      });

      fetchGeneralMarketNews();
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
      searchQuery,
      generalNews,
      loadingNews,
      newsError,
      handleSearch,
      placeholderImage,
      showSearchHint,
      goToFavourites
    };
  }
};
</script>

<!--scrolling issues resolved, DO NOT TOUCH-->
<style>
body {
  display: block !important;
  place-items: unset !important;
  overflow-y: auto !important;
  min-height: 100vh;
  margin: 0;
}

#app {
  max-width: none !important;
  width: 100% !important;
  margin: 0 !important;
  padding: 0 !important;
  text-align: left !important;
  height: 100% !important;
}
</style>

<style scoped>
.general-page {
  display: flex;
  flex-direction: column;
  min-height: 100vh;
  width: 100%;
  background-color: var(--color-background);
  color: var(--color-text-primary);
}

.dashboard-header {
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
  display: flex;
  align-items: center;
  gap: 10px;

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

/*make the colour change less weird using transition*/
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

/*search section styles*/
.search-section {
  background-color: var(--color-background);
  padding: 24px 0;
  border-bottom: 1px solid var(--color-border);
  width: 100%;
  box-sizing: border-box;
}

.search-container {
  width: 800px;
  max-width: 90%;
  margin: 0 auto;
  display: flex;
  gap: 12px;
  padding: 0 16px;
  position: relative
}

.search-hint-popup {
  position: absolute;
  top: calc(100% + 8px);
  left: 0;
  width: 100%;
  background-color: var(--color-surface);
  border: 1px solid var(--color-border);
  border-radius: 6px;
  padding: 12px;
  box-shadow: 0 4px 12px var(--color-card-shadow);
  z-index: 100;
  padding: 12px;
  animation: fadeIn 0.3s ease-out;
}

.hint-content {
  color: var(--color-text-primary);
}

.hint-content p {
  margin: 6px 0;
  font-size: 14px;
}

.hint-content p:first-child {
  color: var(--color-secondary);
}


@keyframes fadeIn {
  from { opacity: 0; transform: translateY(-8px); }
  to { opacity: 1; transform: translateY(0); }
}


.search-input {
  flex: 1;
  padding: 14px 20px;
  font-size: 16px;
  border-radius: 30px;
  border: 1px solid var(--color-border);
  box-shadow: 0 2px 5px var(--color-card-shadow);
  background-color: var(--color-input-bg);
  color: var(--color-text-primary);
}

.search-button {
  padding: 14px 28px;
  font-size: 16px;
  background-color: var(--color-secondary);
  color: white;
  border: none;
  border-radius: 30px;
  cursor: pointer;
  transition: background-color 0.2s;
}

.search-button:hover {
  background-color: var(--color-secondary-hover);
}

/*market summary section*/
.market-summary {
  padding: 24px 16px;
  background-color: var(--color-surface);
  width: 100%;
  box-sizing: border-box;
}

.market-summary h2 {
  margin-bottom: 16px;
  font-size: 22px;
  color: var(--color-text-primary);
}

.market-indices {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(200px, 1fr));
  gap: 16px;
}

.index-card {
  background-color: var(--color-background);
  border-radius: 8px;
  padding: 16px;
  box-shadow: 0 2px 4px var(--color-card-shadow);
}

.index-card h3 {
  margin: 0 0 8px 0;
  font-size: 16px;
  color: var(--color-text-secondary);
}

.index-price {
  font-size: 20px;
  font-weight: bold;
  margin: 4px 0;
  color: var(--color-text-primary);
}

.index-change {
  font-size: 16px;
  margin: 0;
}

.positive {
  color: #16a34a;
}

.negative {
  color: #dc2626;
}

/*general news section*/
.general-news {
  padding: 24px 16px;
  background-color: var(--color-background);
  width: 100%;
  box-sizing: border-box;
}

.general-news h2 {
  margin-bottom: 16px;
  font-size: 22px;
  color: var(--color-text-primary);
}

.news-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(320px, 1fr));
  gap: 16px;
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
  padding: 12px;
  flex: 1;
}

.news-headline {
  font-size: 16px;
  font-weight: 500;

  color: var(--color-secondary);

  text-decoration: none; /*removes underline when not hovered, important*/
  display: block;
  margin-bottom: 8px;
  line-height: 1.3;
}

.news-headline:hover {
  text-decoration: underline;
}

.news-meta {
  font-size: 13px;
  color: var(--color-text-secondary);
  margin: 6px 0;
}

.news-sentiment {
  font-size: 14px;
  color: var(--color-text-secondary);
  margin-top: 4px;
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

/*trending stocks section */
.trending-stocks {
  padding: 24px 16px;
  background-color: var(--color-background);
  width: 100%;
  box-sizing: border-box;
}

.trending-stocks h2 {
  margin-bottom: 16px;
  font-size: 22px;
  color: var(--color-text-primary);
}

.stock-cards {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(200px, 1fr));
  gap: 16px;
}

.stock-card {
  background-color: var(--color-surface);
  border-radius: 8px;
  padding: 16px;
  box-shadow: 0 2px 4px var(--color-card-shadow);
  transition: transform 0.2s;
}

.stock-card:hover {
  transform: translateY(-4px);
}

/*stock fonts*/
.stock-header {
  margin-bottom: 8px;
}

.stock-header h3 {
  margin: 0;
  font-size: 18px;
  font-weight: bold;
  color: var(--color-text-primary);
}

.stock-header p {
  margin: 4px 0 0;
  font-size: 15px;
  color: var(--color-text-secondary);
  font-weight: bold;
}

.stock-price {
  font-size: 20px;
  font-weight: bold;
  margin: 8px 0 4px;
  color: var(--color-text-primary);
}

.stock-change {
  font-size: 15px;
  margin: 0;
}

/*for smaller screens like phone*/
@media (max-width: 768px) {
  .news-grid {
    grid-template-columns: 1fr;
  }
 
  .market-indices,
  .stock-cards {
    grid-template-columns: repeat(auto-fill, minmax(150px, 1fr));
  }
  .search-hint-popup {
    width: calc(100% - 32px);
  }
}

.favourites-button {
  background: none;
  border: 2px solid var(--color-danger);
  border-radius: 4px;
  padding: 6px 10px;
  cursor: pointer;
  font-size: 17px;
  color: var(--color-danger); 
  transition: background-color 0.2s, transform 0.2s;
  margin-right: 4px;
  display: flex;
  align-items: center;
  gap: 4px;
}
.favourites-button:hover {
  background-color: var(--color-primary-hover);
}
</style>