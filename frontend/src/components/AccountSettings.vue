<template>
  <div class="account-settings-page">
    <header class="page-header">
      <button @click="goBack" class="back-button">← Back to Home Page</button>
      <h1>Account Settings</h1>
    </header>

    <div class="settings-container">
      <div class="profile-section">
        <div class="profile-pic-wrapper">
          <img :src="profile.image || defaultImage" alt="Profile Picture" class="profile-pic" />
        </div>
        
        <div class="profile-info">
          <h2>{{ fullName }}</h2>
          <div class="info-group">
            <label>Email:</label>
            <span>{{ profile.email }}</span>
          </div>
          <div class="info-group">
            <label>Phone:</label>
            <span>{{ profile.contact || 'Not Provided' }}</span>
          </div>
          <div class="info-group">
            <label>Member since:</label>
            <span>{{ memberSince }}</span>
          </div>
          <!-- we are removing this cos theres no link between the risk appetite n sentiment analysis 
          <div class="info-group">
            <label>Preference Set:</label>
            <span>{{ profile.preferenceSet ? 'Yes' : 'No' }}</span>
          </div>-->
          <div class="info-group">
            <label>Theme:</label>
            <span>{{ profile.themePreference || 'Light (Default)' }}</span>
          </div>
        </div>
      </div>

      <div class="actions-section">
        <button class="edit-button" @click="editProfile">Edit Profile</button>
        <button class="logout-button" @click="handleLogout" :disabled="loggingOut">
          <span v-if="!loggingOut">Log Out</span>
          <span v-else>Logging out...</span>
        </button>
      </div>
    </div>
  </div>
</template>

<script>
import { ref, onMounted, computed } from 'vue';
import { db, auth } from '../firebase';
import { doc, getDoc } from "firebase/firestore";
import { onAuthStateChanged, signOut } from "firebase/auth";
import { useRouter } from 'vue-router';
import { applyTheme } from '@/ThemeManager';

export default {
  name: 'AccountSettings',
  setup() {
    const router = useRouter();
    const profile = ref({
      email: "",
      contact: "",
      firstname: "",
      lastname: "",
      image: "",
      preferenceSet: false,
      themePreference: ""
    });
    const currentUser = ref(null);
    const memberSince = ref("");
    const loggingOut = ref(false);
    const defaultImage = "/src/assets/default-pfp.png";

    const fullName = computed(() => {
      return `${profile.value.firstname} ${profile.value.lastname}`.trim();
    });

    function formatDate(isoString) {
      if (!isoString) return "";
      const dateObj = new Date(isoString);
      const d = String(dateObj.getDate()).padStart(2, "0");
      const m = String(dateObj.getMonth() + 1).padStart(2, "0");
      const y = String(dateObj.getFullYear()).slice(-2);
      return `${d}/${m}/${y}`;
    }

    async function fetchProfileData() {
      if (!currentUser.value) return;
      
      try {
        const docRef = doc(db, "Investors", currentUser.value.uid);
        const docSnap = await getDoc(docRef);
        if (docSnap.exists()) {
          profile.value = { ...profile.value, ...docSnap.data() };
          
          // apply theme if theme is set 
          if (profile.value.themePreference) {
            applyTheme(profile.value.themePreference);
          }
        } else {
          console.log("No profile found");
        }
      } catch (err) {
        console.error("Error fetching profile:", err);
      }
    }

    function goBack() {
      router.push('/general');
    }

    function editProfile() {
      router.push('/edit-profile');
    }

    async function handleLogout() {
      loggingOut.value = true;
      try {
        await signOut(auth);
        router.push("/login");
      } finally {
        loggingOut.value = false;
      }
    }

    onMounted(() => {
      onAuthStateChanged(auth, (user) => {
        if (user) {
          currentUser.value = user;
          memberSince.value = formatDate(user.metadata.creationTime);
          fetchProfileData();
        } else {
          currentUser.value = null;
          memberSince.value = "";
          router.push('/login');
        }
      });
    });

    return {
      profile,
      fullName,
      memberSince,
      loggingOut,
      defaultImage,
      goBack,
      editProfile,
      handleLogout
    };
  }
};
</script>

<style scoped>
.account-settings-page {
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

.settings-container {
  background: var(--color-surface);
  border-radius: 8px;
  padding: 30px;
  box-shadow: 0 2px 10px var(--color-card-shadow);
  max-width: 800px;
  margin: 0 auto;
}

.profile-section {
  display: flex;
  gap: 30px;
  margin-bottom: 30px;
  align-items: flex-start;
}

.profile-pic-wrapper {
  width: 120px;
  height: 120px;
  border-radius: 8px;
  overflow: hidden;
  box-shadow: 0 2px 8px var(--color-card-shadow);
  flex-shrink: 0;
}

.profile-pic {
  width: 100%;
  height: 100%;
  object-fit: cover;
}

.profile-info {
  flex: 1;
}

.profile-info h2 {
  margin: 0 0 20px 0;
  font-size: 20px;
  color: var(--color-text-primary);
}

.info-group {
  margin-bottom: 12px;
  display: flex;
  gap: 10px;
}

.info-group label {
  font-weight: bold;
  min-width: 120px;
  color: var(--color-text-secondary);
}

.info-group span {
  color: var(--color-text-primary);
}

.actions-section {
  display: flex;
  gap: 15px;
  padding-top: 20px;
  border-top: 1px solid var(--color-border);
}

.edit-button {
  background-color: var(--color-primary);
  color: var(--color-text-primary);
  border: none;
  padding: 12px 24px;
  border-radius: 4px;
  cursor: pointer;
  font-size: 14px;
  font-weight: 500;
}

.edit-button:hover {
  background-color: var(--color-primary-hover);
}

.logout-button {
  background-color: var(--color-danger);
  color: white;
  border: none;
  padding: 12px 24px;
  border-radius: 4px;
  cursor: pointer;
  font-size: 14px;
  font-weight: 500;
}

.logout-button:hover:not(:disabled) {
  background-color: var(--color-danger-hover);
}

.logout-button:disabled {
  opacity: 0.6;
  cursor: not-allowed;
}
</style>