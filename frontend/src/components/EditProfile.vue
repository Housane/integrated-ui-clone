<template>
  <div class="edit-profile-page">
    <header class="page-header">
      <button @click="goBack" class="back-button">← Back to Account Settings</button>
      <h1>Edit Profile</h1>
    </header>

    <div class="edit-container">
      <form @submit.prevent="saveProfile" class="edit-form">

        <div class="profile-pic-section">
          <div class="current-pic-wrapper">
            <img :src="profileData.image || defaultImage" alt="Current Profile Picture" class="current-pic" />
          </div>
          <div class="pic-upload">
            <label for="profile-pic-input" class="upload-label">
              Change Profile Picture
            </label>
            <input 
              id="profile-pic-input"
              type="file" 
              accept="image/*" 
              @change="handleImageUpload"
              class="file-input"
            />
            <p class="upload-note">Max size: 5MB. Supported formats: JPG, PNG, GIF</p>
          </div>
        </div>

        <div class="form-section">
          <div class="form-row">
            <div class="form-group">
              <label for="firstname">First Name *</label>
              <input 
                id="firstname"
                v-model="profileData.firstname" 
                type="text" 
                required
                class="form-input"
                placeholder="Enter your first name"
              />
            </div>
            <div class="form-group">
              <label for="lastname">Last Name *</label>
              <input 
                id="lastname"
                v-model="profileData.lastname" 
                type="text" 
                required
                class="form-input"
                placeholder="Enter your last name"
              />
            </div>
          </div>

          <div class="form-group">
            <label for="email">Email Address</label>
            <div class="email-field-wrapper">
              <input 
                id="email"
                v-model="profileData.email" 
                type="email" 
                disabled
                class="form-input disabled"
                title="Email cannot be changed"
              />
              <button 
                type="button" 
                @click="resetPassword" 
                :disabled="resettingPassword"
                class="reset-password-button"
              >
                <span v-if="!resettingPassword">Reset Password</span>
                <span v-else>Sending...</span>
              </button>
            </div>
            <small class="field-note">Email address cannot be modified</small>
          </div>

          <div class="form-group">
            <label for="contact">Phone Number</label>
            <input 
              id="contact"
              v-model="profileData.contact" 
              type="tel" 
              class="form-input"
              placeholder="Enter your phone number"
            />
          </div>

          <!--theme toggle -->
          <div class="form-group theme-toggle-group">
            <label>Theme Preference</label>
            <div class="theme-toggle-wrapper">
              <span class="theme-label">Light</span>
              <div class="theme-toggle" @click="toggleThemePreference" :class="{ 'theme-toggle-dark': isDarkTheme }">
                <div class="theme-toggle-knob"></div>
              </div>
              <span class="theme-label">Dark</span>
            </div>
            <small class="field-note">Toggle between light and dark mode</small>
          </div>


        </div>

        <!--if user does not want to edit-->
        <div class="form-actions">
          <button type="button" @click="cancelEdit" class="cancel-button">
            Cancel
          </button>
          <button type="submit" :disabled="saving" class="save-button">
            <span v-if="!saving">Save Changes</span>
            <span v-else>Saving...</span>
          </button>
        </div>
      </form>

      <div v-if="message" :class="['message', messageType]">
        {{ message }}
      </div>
    </div>
  </div>
</template>

<script>
import { ref, onMounted, computed } from 'vue';
import { db, auth } from '../firebase';
import { doc, getDoc, updateDoc } from "firebase/firestore";
import { onAuthStateChanged, sendPasswordResetEmail, signOut } from "firebase/auth";
import { useRouter } from 'vue-router';
import defaultImage from '@/assets/default-pfp.png';
import { currentTheme, toggleTheme, applyTheme } from '@/ThemeManager';

export default {
  name: 'EditProfile',
  setup() {
    const router = useRouter();
    const currentUser = ref(null);
    const saving = ref(false);
    const resettingPassword = ref(false);
    const message = ref('');
    const messageType = ref('');

    const profileData = ref({
      email: "",
      contact: "",
      firstname: "",
      lastname: "",
      image: "",
      themePreference: ""
    });

    const originalData = ref({});
    

    // compute if the current theme is dark
    const isDarkTheme = computed(() => {
      return currentTheme.value === 'dark';
    });

    async function fetchProfileData() {
      if (!currentUser.value) return;
      
      //refer to cheryls bt project for structure 
      try {
        const docRef = doc(db, "Investors", currentUser.value.uid);
        const docSnap = await getDoc(docRef);
        if (docSnap.exists()) {
          const data = docSnap.data();
          profileData.value = { ...profileData.value, ...data };
          originalData.value = { ...data };
          

          if (data.themePreference) {
            applyTheme(data.themePreference);
          }
        } else {
          console.log("No profile found");
        }
      } catch (err) {
        console.error("Error fetching profile:", err);
        showMessage('Error loading profile data', 'error');
      }
    }

    //handles the change when toggled 
    function toggleThemePreference() {
      const newTheme = toggleTheme();
      profileData.value.themePreference = newTheme;
    }

    //handles profile pic upload 
    function handleImageUpload(event) {
      const file = event.target.files[0];
      if (!file) return;

      if (file.size > 5 * 1024 * 1024) {
        showMessage('Image size must be less than 5MB', 'error');
        return;
      }

      if (!file.type.startsWith('image/')) {
        showMessage('Please select a valid image file', 'error');
        return;
      }

      const reader = new FileReader();
      reader.onload = (e) => {
        profileData.value.image = e.target.result;
      };
      reader.readAsDataURL(file);
    }

    async function resetPassword() {
      if (!currentUser.value || !profileData.value.email) {
        showMessage('Unable to send reset email. Please try again.', 'error');
        return;
      }

      resettingPassword.value = true;
      try {
        await sendPasswordResetEmail(auth, profileData.value.email);
        showMessage('A link will be sent to your registered email address. Click on the link to reset the password.', 'success');
        
        // after user clicks reset password they r redirected to login page. set time ard 2s 
        setTimeout(async () => {
          try {
            await signOut(auth);
            router.push('/login');
          } catch (signOutErr) {
            console.error("Error signing out:", signOutErr);
            //edge case: if signing out fails also push router to login 
            router.push('/login');
          }
        }, 2000);
        
      } catch (err) {
        console.error("Error sending password reset email:", err);
        showMessage('Error sending reset email. Please try again.', 'error');
      } finally {
        resettingPassword.value = false;
      }
    }

    async function saveProfile() {
      if (!currentUser.value) return;

      if (!profileData.value.firstname.trim() || !profileData.value.lastname.trim()) {
        showMessage('First name and last name are required', 'error');
        return;
      }

      saving.value = true;
      try {
        const docRef = doc(db, "Investors", currentUser.value.uid);
        await updateDoc(docRef, {
          firstname: profileData.value.firstname.trim(),
          lastname: profileData.value.lastname.trim(),
          contact: profileData.value.contact.trim(),
          image: profileData.value.image,
          themePreference: profileData.value.themePreference
        });

        showMessage('Profile updated successfully!', 'success');
        
        originalData.value = { ...profileData.value };
        
        setTimeout(() => {
          router.push('/account-settings');
        }, 1500);
        
      } catch (err) {
        console.error("Error updating profile:", err);
        showMessage('Error updating profile. Please try again.', 'error');
      } finally {
        saving.value = false;
      }
    }

    function cancelEdit() {
      profileData.value = { ...originalData.value };
      router.push('/account-settings');
    }

    function goBack() {
      const hasChanges = JSON.stringify(profileData.value) !== JSON.stringify(originalData.value);
      
      if (hasChanges) {
        if (confirm('You have unsaved changes. Are you sure you want to leave?')) {
          router.push('/account-settings');
        }
      } else {
        router.push('/account-settings');
      }
    }


    function showMessage(text, type) {
      message.value = text;
      messageType.value = type;
      setTimeout(() => {
        message.value = '';
        messageType.value = '';
      }, 5000);
    }

    onMounted(() => {
      onAuthStateChanged(auth, (user) => {
        if (user) {
          currentUser.value = user;
          profileData.value.email = user.email;
          fetchProfileData();
        } else {
          router.push('/login');
        }
      });
    });

    return {
      profileData,
      saving,
      resettingPassword,
      message,
      messageType,
      defaultImage, 
      isDarkTheme,
      handleImageUpload,
      resetPassword,
      saveProfile,
      cancelEdit,
      goBack,
      toggleThemePreference,
    };
  }
};
</script>

<style scoped>
.edit-profile-page {
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

.edit-container {
  background: var(--color-surface);
  border-radius: 8px;
  padding: 40px;
  box-shadow: 0 2px 10px var(--color-card-shadow);
  max-width: 800px;
  margin: 0 auto;
}

.profile-pic-section {
  display: flex;
  gap: 30px;
  margin-bottom: 40px;
  align-items: flex-start;
  padding-bottom: 30px;
  border-bottom: 1px solid var(--color-border);
}

.current-pic-wrapper {
  width: 120px;
  height: 120px;
  border-radius: 8px;
  overflow: hidden;
  box-shadow: 0 2px 8px var(--color-card-shadow);
  flex-shrink: 0;
}

.current-pic {
  width: 100%;
  height: 100%;
  object-fit: cover;
}

.pic-upload {
  flex: 1;
}

.upload-label {
  display: inline-block;
  background-color: var(--color-primary);
  color: var(--color-text-primary);
  padding: 10px 20px;
  border-radius: 4px;
  cursor: pointer;
  font-size: 14px;
  font-weight: 500;
  transition: background-color 0.2s;
}

.upload-label:hover {
  background-color: var(--color-primary-hover);
}

.file-input {
  display: none;
}

.upload-note {
  margin-top: 10px;
  font-size: 12px;
  color: var(--color-text-secondary);
}

.form-section {
  margin-bottom: 30px;
}

.form-row {
  display: flex;
  gap: 20px;
  margin-bottom: 20px;
}

.form-group {
  margin-bottom: 20px;
  flex: 1;
}

.form-group label {
  display: block;
  margin-bottom: 8px;
  font-weight: 500;
  color: var(--color-text-primary);
}

.form-input {
  width: 100%;
  padding: 12px;
  border: 1px solid var(--color-border);
  border-radius: 4px;
  font-size: 14px;
  transition: border-color 0.2s;
  box-sizing: border-box;
  background-color: var(--color-input-bg);
  color: var(--color-text-primary);
}

.form-input:focus {
  outline: none;
  border-color: var(--color-primary);
}

.form-input.disabled {
  background-color: var(--color-background);
  cursor: not-allowed;
}

.email-field-wrapper {
  display: flex;
  gap: 10px;
  align-items: center;
}

.email-field-wrapper .form-input {
  flex: 1;
}

.reset-password-button {
  background-color: var(--color-danger);
  color: white;
  border: none;
  padding: 12px 16px;
  border-radius: 4px;
  cursor: pointer;
  font-size: 12px;
  font-weight: 500;
  transition: background-color 0.2s;
  white-space: nowrap;
  flex-shrink: 0;
}

.reset-password-button:hover:not(:disabled) {
  background-color: var(--color-danger-hover);
}

.reset-password-button:disabled {
  opacity: 0.6;
  cursor: not-allowed;
}

.field-note {
  display: block;
  margin-top: 5px;
  font-size: 12px;
  color: var(--color-text-secondary);
}

.theme-toggle-group {
  margin-top: 20px;
}

.theme-toggle-wrapper {
  display: flex;
  align-items: center;
  gap: 12px;
  margin-top: 8px;
}

.theme-label {
  font-size: 14px;
  color: var(--color-text-primary);
}

.theme-toggle {
  position: relative;
  width: 50px;
  height: 26px;
  background-color: #ccc;
  border-radius: 15px;
  cursor: pointer;
  transition: background-color 0.3s;
}

.theme-toggle-dark {
  background-color: var(--color-secondary);
}

.theme-toggle-knob {
  position: absolute;
  top: 3px;
  left: 3px;
  width: 20px;
  height: 20px;
  background-color: white;
  border-radius: 50%;
  transition: transform 0.3s;
}

.theme-toggle-dark .theme-toggle-knob {
  transform: translateX(24px);
}

.form-actions {
  display: flex;
  gap: 15px;
  justify-content: flex-end;
  padding-top: 30px;
  border-top: 1px solid var(--color-border);
}

.cancel-button {
  background: none;
  border: 1px solid var(--color-text-secondary);
  color: var(--color-text-secondary);
  padding: 12px 24px;
  border-radius: 4px;
  cursor: pointer;
  font-size: 14px;
  transition: all 0.2s;
}

.cancel-button:hover {
  background-color: var(--color-border);
  color: var(--color-text-primary);
}

.save-button {
  background-color: var(--color-success);
  color: white;
  border: none;
  padding: 12px 24px;
  border-radius: 4px;
  cursor: pointer;
  font-size: 14px;
  font-weight: 500;
  transition: background-color 0.2s;
}

.save-button:hover:not(:disabled) {
  opacity: 0.9;
}

.save-button:disabled {
  opacity: 0.6;
  cursor: not-allowed;
}

.message {
  margin-top: 20px;
  padding: 12px;
  border-radius: 4px;
  font-size: 14px;
  text-align: center;
}

.message.success {
  background-color: #d4edda;
  color: #155724;
  border: 1px solid #c3e6cb;
}

.message.error {
  background-color: #f8d7da;
  color: #721c24;
  border: 1px solid #f5c6cb;
}
</style>