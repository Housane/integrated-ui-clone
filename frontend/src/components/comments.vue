<template>
  <div class="comments-page">
    <header class="comments-header">
      <div class="header-content">
        <button class="back-btn" @click="goBack">
          ← Back
        </button>
        <h1 class="page-title">{{ symbolInput }} Comments</h1>
      </div>
    </header>

    <div class="comments-content">
      <div class="comments-stats">
        <span class="count">{{ comments.length }} comments</span>
        <span class="sort-options">
          <select v-model="sortOption" class="sort-select" @change="refreshComments">
            <option value="newest">Newest first</option>
            <option value="oldest">Oldest first</option>
          </select>
        </span>
      </div>


      <div v-if="loading" class="loading-container">
        <div class="loading-spinner"></div>
        <p>Loading comments...</p>
      </div>


      <div v-else class="comments-list">
        <div v-if="comments.length === 0" class="no-comments">
          <p>No comments yet for {{ symbolInput }}.</p>
          <p class="sub-text">Be the first to share your thoughts!</p>
        </div>
        
        <div v-for="comment in comments" :key="comment.id" class="comment-item">
          <div class="comment-header">
            <div class="user-info">
              <span class="username">{{ comment.username || 'Anonymous' }}</span>
            </div>
            <span class="timestamp">{{ formatDate(comment.timestamp) }}</span>
          </div>
          <div class="comment-content">{{ comment.content }}</div>
        </div>
      </div>
      
      <div class="add-comment-section">
        <h2>Add Your Comment</h2>
        <textarea 
          v-model="newComment" 
          placeholder="Share your thoughts about this stock..."
          rows="4"
          :disabled="!currentUser"
          class="comment-textarea"
        ></textarea>
        <div class="button-row">
          <button 
            @click="submitComment" 
            :disabled="!newComment.trim() || isSubmitting || !currentUser"
            class="submit-btn"
          >
            {{ isSubmitting ? 'Posting...' : 'Post Comment' }}
          </button>
          <button 
            @click="refreshComments" 
            class="refresh-btn"
          >
            Refresh Comments
          </button>
          <p v-if="!currentUser" class="login-prompt">
            Please <router-link to="/login" class="login-link">login</router-link> to post comments
          </p>
        </div>
      </div>
    </div>
  </div>
</template>

<script>
import { ref, onMounted, onBeforeUnmount } from 'vue';
import { useRouter, useRoute } from 'vue-router';
import { collection, addDoc, getDocs, query, serverTimestamp } from 'firebase/firestore';
import { auth, db } from '../firebase';
import { onAuthStateChanged } from 'firebase/auth';
import { doc, getDoc } from 'firebase/firestore';

export default {
  name: 'StockComments',
  setup() {
    const router = useRouter();
    const route = useRoute();
    
    const symbolInput = ref(route.params.symbol || '');
    const comments = ref([]);
    const newComment = ref('');
    const sortOption = ref('newest');
    const loading = ref(true);
    const isSubmitting = ref(false);
    const currentUser = ref(null);
    const userProfile = ref(null);
    
    let unsubscribeAuth = null;

    function goBack() {
      router.back();
    }
    
    function formatDate(timestamp) {
      if (!timestamp) return 'Just now';
      
      try {
        const date = timestamp.toDate ? timestamp.toDate() : new Date(timestamp);
        
        return new Intl.DateTimeFormat('en-US', {
          year: 'numeric',
          month: 'short',
          day: 'numeric',
          hour: '2-digit',
          minute: '2-digit'
        }).format(date);
      } catch (error) {
        return 'Just now';
      }
    }
    
    async function fetchComments() {
      if (!symbolInput.value) return;
      loading.value = true;
  
      try {
        console.log("Fetching comments for symbol:", symbolInput.value);
        
        const commentsRef = collection(db, "stockComments");
        const q = query(commentsRef);
        const querySnapshot = await getDocs(q);
        
        const commentsArray = [];
        
        querySnapshot.forEach((doc) => {
          const data = doc.data();
          if (data.stockSymbol && data.stockSymbol.toUpperCase() === symbolInput.value.toUpperCase()) {
            commentsArray.push({
              id: doc.id,
              ...data
            });
          }
        });
        
        console.log(`Found ${commentsArray.length} comments total`);
        

        commentsArray.sort((a, b) => {
          const getTime = (item) => {
            if (item.timestamp?.toMillis) return item.timestamp.toMillis();
            if (item.timestamp?.seconds) return item.timestamp.seconds * 1000;
            if (item.createdAt) return new Date(item.createdAt).getTime();
            return 0;
          };
          
          const aTime = getTime(a);
          const bTime = getTime(b);
          
          return sortOption.value === 'newest' ? bTime - aTime : aTime - bTime;
        });
        
        comments.value = commentsArray;
        console.log("Sorted comments:", commentsArray);
      } catch (error) {
        console.error("Error fetching comments:", error);
      } finally {
        loading.value = false;
      }
    }

    function refreshComments() {
      fetchComments();
    }

    async function fetchUserProfile() {
      if (!currentUser.value) return;
      
      try {
        const docRef = doc(db, 'Investors', currentUser.value.uid);
        const snap = await getDoc(docRef);
        if (snap.exists()) {
          userProfile.value = snap.data();
        }
      } catch (err) {
        console.error("Error fetching user profile:", err);
      }
    }
    
    async function submitComment() {
      if (!newComment.value.trim() || isSubmitting.value || !currentUser.value) return;
      
      isSubmitting.value = true;
      
      try {
        const displayName = userProfile.value?.firstname && userProfile.value?.lastname 
          ? `${userProfile.value.firstname} ${userProfile.value.lastname}`
          : currentUser.value.email || 'Anonymous User';
        
        const stockSymbol = symbolInput.value.toUpperCase();
        
        const commentData = {
          userId: currentUser.value.uid,
          username: displayName,
          stockSymbol: stockSymbol,
          content: newComment.value.trim(),
          timestamp: serverTimestamp(),
          createdAt: new Date().toISOString()
        };
        
        const docRef = await addDoc(collection(db, "stockComments"), commentData);
        console.log("Comment added with ID:", docRef.id);
        
        newComment.value = '';
        
        setTimeout(() => {
          fetchComments();
        }, 1000);
        
      } catch (error) {
        console.error('Failed to post comment:', error);
        alert('Failed to post your comment. Please try again.');
      } finally {
        isSubmitting.value = false;
      }
    }

    onMounted(() => {
      console.log("Comments component mounted");
      console.log("Stock symbol:", symbolInput.value);

      unsubscribeAuth = onAuthStateChanged(auth, (user) => {
        currentUser.value = user;
        
        if (user) {
          fetchUserProfile();
        }
      });
      
      if (symbolInput.value) {
        fetchComments();
      } else {
        console.error("No stock symbol provided");
        router.push('/');
      }
    });

    onBeforeUnmount(() => {
      if (unsubscribeAuth) unsubscribeAuth();
    });

    return {
      symbolInput,
      comments,
      newComment,
      sortOption,
      loading,
      isSubmitting,
      currentUser,
      goBack,
      formatDate,
      submitComment,
      refreshComments
    };
  }
}
</script>

<style scoped>
.comments-page {
  display: flex;
  flex-direction: column;
  min-height: 100vh;
  background-color: var(--color-background);
  color: var(--color-text-primary);
}

.comments-header {
  background-color: var(--color-primary);
  padding: 16px 24px;
  position: sticky;
  top: 0;
  z-index: 100;
  box-shadow: 0 2px 8px var(--color-card-shadow);
}

.header-content {
  display: flex;
  align-items: center;
  gap: 16px;
}

.back-btn {
  background: none;
  border: 2px solid var(--color-text-primary);
  border-radius: 4px;
  padding: 6px 12px;
  cursor: pointer;
  font-size: 16px;
  color: var(--color-text-primary);
  transition: background-color 0.2s;
}

.back-btn:hover {
  background-color: rgba(255, 255, 255, 0.1);
}

.page-title {
  font-size: 20px;
  margin: 0;
  color: var(--color-text-primary);
}

.comments-content {
  max-width: 800px;
  margin: 0 auto;
  padding: 24px;
  width: 100%;
  box-sizing: border-box;
}

.comments-stats {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 16px;
  padding: 12px 16px;
  background-color: var(--color-surface);
  border-radius: 8px;
  box-shadow: 0 2px 6px var(--color-card-shadow);
}

.count {
  font-weight: 500;
}

.sort-select {
  background-color: var(--color-input-bg);
  color: var(--color-text-primary);
  border: 1px solid var(--color-border);
  padding: 6px 10px;
  border-radius: 4px;
  font-size: 14px;
}

.loading-container {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 60px 0;
}

.loading-spinner {
  border: 4px solid rgba(0, 0, 0, 0.1);
  border-radius: 50%;
  border-top: 4px solid var(--color-secondary);
  width: 30px;
  height: 30px;
  animation: spin 1s linear infinite;
  margin-bottom: 16px;
}

@keyframes spin {
  0% { transform: rotate(0deg); }
  100% { transform: rotate(360deg); }
}

.comments-list {
  margin-bottom: 30px;
}

.no-comments {
  padding: 40px 20px;
  text-align: center;
  background-color: var(--color-surface);
  border-radius: 8px;
  box-shadow: 0 2px 6px var(--color-card-shadow);
}

.no-comments p {
  margin: 5px 0;
}

.sub-text {
  color: var(--color-text-secondary);
  font-size: 14px;
}

.comment-item {
  background-color: var(--color-surface);
  border-radius: 8px;
  padding: 16px;
  margin-bottom: 16px;
  box-shadow: 0 2px 6px var(--color-card-shadow);
}

.comment-header {
  display: flex;
  justify-content: space-between;
  margin-bottom: 12px;
  padding-bottom: 8px;
  border-bottom: 1px solid var(--color-border);
}

.username {
  font-weight: bold;
  color: var(--color-secondary);
}

.timestamp {
  color: var(--color-text-secondary);
  font-size: 14px;
}

.comment-content {
  line-height: 1.5;
}

.add-comment-section {
  background-color: var(--color-surface);
  border-radius: 8px;
  padding: 20px;
  box-shadow: 0 2px 6px var(--color-card-shadow);
}

.add-comment-section h2 {
  margin-top: 0;
  margin-bottom: 16px;
  font-size: 18px;
  color: var(--color-text-primary);
}

.comment-textarea {
  width: 100%;
  background-color: var(--color-input-bg);
  color: var(--color-text-primary);
  border: 1px solid var(--color-border);
  border-radius: 8px;
  padding: 12px;
  margin-bottom: 16px;
  resize: vertical;
  font-family: inherit;
  font-size: 15px;
}

.comment-textarea:disabled {
  opacity: 0.7;
  cursor: not-allowed;
}

.button-row {
  display: flex;
  align-items: center;
  justify-content: space-between;
  flex-wrap: wrap;
  gap: 12px;
}

.submit-btn {
  background-color: var(--color-secondary);
  color: white;
  border: none;
  padding: 10px 20px;
  border-radius: 6px;
  cursor: pointer;
  font-weight: 500;
  transition: background-color 0.2s;
}

.submit-btn:hover:not(:disabled) {
  background-color: var(--color-primary-hover);
}

.submit-btn:disabled {
  opacity: 0.6;
  cursor: not-allowed;
}

.refresh-btn {
  background-color: var(--color-input-bg);
  color: var(--color-text-primary);
  border: 1px solid var(--color-border);
  padding: 10px 20px;
  border-radius: 6px;
  cursor: pointer;
  font-weight: 500;
  transition: background-color 0.2s;
}

.refresh-btn:hover {
  background-color: var(--color-border);
}

.login-prompt {
  font-size: 14px;
  color: var(--color-text-secondary);
  margin: 0;
}

.login-link {
  color: var(--color-secondary);
  text-decoration: none;
}

.login-link:hover {
  text-decoration: underline;
}

@media (max-width: 768px) {
  .comments-content {
    padding: 16px;
  }
  
  .button-row {
    flex-direction: column;
    align-items: flex-start;
  }
  
  .submit-btn, .refresh-btn {
    width: 100%;
  }
}
</style>