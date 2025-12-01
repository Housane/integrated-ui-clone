<template>
  <div class="favourites-page">
    <header class="page-header">
      <button @click="goBack" class="back-button">← Back</button>
      <h1>My Favourite Stocks</h1>
    </header>

    <div class="favourites-container">
      <div v-if="isLoading" class="loading-state">
        <div class="loading-spinner"></div>
        <p>Loading your favourite stocks...</p>
      </div>
      
      <div v-else-if="favourites.length === 0" class="empty-state">
        <div class="empty-icon">
          <i class="fas fa-heart-broken"></i>
        </div>
        <h2>No favourites yet</h2>
        <p>You haven't added any stocks to your favourites.</p>
        <p class="empty-tip">When viewing a stock on the dashboard, click the heart icon to add it to your favourites.</p>
        <button @click="goToGeneral" class="action-button">
          Search for Stocks
        </button>
      </div>
      
      <div v-else>
        <p class="favourites-intro">Click on any stock to view its details or remove it from your favourites.</p>
        
        <div class="favourites-list">
          <div 
            v-for="stock in favourites" 
            :key="stock.symbol" 
            class="favourite-item" 
            @click="viewStock(stock.symbol)"
          >
            <div class="favourite-info">
              <h3>{{ stock.symbol }}</h3>
              <p v-if="stock.name && stock.name !== stock.symbol">{{ stock.name }}</p>
              <small>Added: {{ formatDate(stock.addedAt) }}</small>
            </div>
            <button 
              class="remove-btn"
              @click.stop="removeFavourite(stock)"
              aria-label="Remove from favourites"
            >
              <i class="fas fa-trash"></i>
            </button>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script>
import { ref, onMounted } from 'vue';
import { auth, db } from '../firebase';
import { onAuthStateChanged } from 'firebase/auth';
import { doc, getDoc, updateDoc, arrayRemove } from 'firebase/firestore';
import { useRouter } from 'vue-router';

export default {
  name: 'FavouriteStocks',
  
  setup() {
    const router = useRouter();
    const favourites = ref([]);
    const isLoading = ref(true);
    const currentUser = ref(null);
    
    function formatDate(dateString) {
      try {
        const date = new Date(dateString);
        return date.toLocaleDateString();
      } catch (e) {
        return 'Unknown date';
      }
    }
    
    function goBack() {
      router.go(-1); 
    }
    
    function goToGeneral() {
      router.push('/general');
    }
    
    async function loadFavourites() {
      if (!currentUser.value) return;
      
      isLoading.value = true;
      try {
        const docRef = doc(db, 'Investors', currentUser.value.uid);
        const docSnap = await getDoc(docRef);
        
        if (docSnap.exists() && docSnap.data().favourites) {
          favourites.value = docSnap.data().favourites;
        } else {
          favourites.value = [];
          
          await updateDoc(docRef, { favourites: [] });
        }
      } catch (error) {
        console.error('Error loading favourites:', error);
        favourites.value = [];
      } finally {
        isLoading.value = false;
      }
    }
    
    async function removeFavourite(stock) {
      if (!currentUser.value) return;
      
      try {
        const docRef = doc(db, 'Investors', currentUser.value.uid);
        
        await updateDoc(docRef, {
          favourites: arrayRemove(stock)
        });
        
        favourites.value = favourites.value.filter(fav => fav.symbol !== stock.symbol);
      } catch (error) {
        console.error('Error removing favourite:', error);
      }
    }
    
    function viewStock(symbol) {
      router.push(`/dashboard?symbol=${symbol}`);
    }
    
    onMounted(() => {
      onAuthStateChanged(auth, (user) => {
        if (user) {
          currentUser.value = user;
          loadFavourites();
        } else {
          router.push('/login');
        }
      });
    });
    
    return {
      favourites,
      isLoading,
      formatDate,
      goBack,
      goToGeneral,
      removeFavourite,
      viewStock
    };
  }
};
</script>

<style scoped>
.favourites-page {
  min-height: 100vh;
  background-color: var(--color-background);
  padding: 20px;
}

.page-header {
  display: flex;
  align-items: center;
  margin-bottom: 30px;
  gap: 20px;
}

.back-button {
  background: none;
  border: 1px solid var(--color-text-primary);
  padding: 8px 16px;
  border-radius: 4px;
  cursor: pointer;
  font-size: 14px;
  transition: background-color 0.2s;
  color: var(--color-text-primary);
}

.back-button:hover {
  background-color: var(--color-border);
}

h1 {
  margin: 0;
  font-size: 24px;
  color: var(--color-text-primary);
}

.favourites-container {
  background: var(--color-surface);
  border-radius: 8px;
  padding: 40px;
  box-shadow: 0 2px 10px var(--color-card-shadow);
  max-width: 800px;
  margin: 0 auto;
}

.favourites-intro {
  margin-bottom: 20px;
  color: var(--color-text-secondary);
}

.loading-state {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 60px 0;
}

.loading-spinner {
  width: 40px;
  height: 40px;
  border: 4px solid rgba(0, 0, 0, 0.1);
  border-radius: 50%;
  border-top: 4px solid var(--color-primary);
  animation: spin 1s linear infinite;
  margin-bottom: 20px;
}

@keyframes spin {
  0% { transform: rotate(0deg); }
  100% { transform: rotate(360deg); }
}

.empty-state {
  text-align: center;
  padding: 40px 0;
}

.empty-icon {
  font-size: 40px;
  color: var(--color-text-secondary);
  opacity: 0.5;
  margin-bottom: 20px;
}

.empty-state h2 {
  margin-bottom: 10px;
  color: var(--color-text-primary);
}

.empty-state p {
  color: var(--color-text-secondary);
}

.empty-tip {
  margin: 20px 0;
  padding: 12px;
  background-color: var(--color-background);
  border-radius: 8px;
  font-size: 14px;
}

.action-button {
  margin-top: 20px;
  background-color: var(--color-primary);
  color: var(--color-text-primary);
  border: none;
  padding: 12px 24px;
  border-radius: 4px;
  cursor: pointer;
  font-size: 16px;
  transition: background-color 0.2s;
}

.action-button:hover {
  background-color: var(--color-primary-hover);
}

.favourites-list {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(300px, 1fr));
  gap: 16px;
}

.favourite-item {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 16px;
  background-color: var(--color-input-bg);
  border-radius: 8px;
  transition: transform 0.2s, box-shadow 0.2s;
  cursor: pointer;
}

.favourite-item:hover {
  transform: translateY(-2px);
  box-shadow: 0 4px 12px var(--color-card-shadow);
}

.favourite-info h3 {
  margin: 0 0 8px 0;
  font-size: 18px;
  color: var(--color-text-primary);
}

.favourite-info p {
  margin: 0 0 8px 0;
  color: var(--color-text-secondary);
}

.favourite-info small {
  font-size: 12px;
  color: var(--color-text-secondary);
}

.remove-btn {
  background: transparent;
  border: none;
  color: var(--color-danger);
  cursor: pointer;
  padding: 8px;
  border-radius: 50%;
  transition: background-color 0.2s;
}

.remove-btn:hover {
  background-color: rgba(220, 53, 69, 0.1);
}

@media (max-width: 768px) {
  .favourites-container {
    padding: 20px;
  }
  
  .favourites-list {
    grid-template-columns: 1fr;
  }
}
</style>