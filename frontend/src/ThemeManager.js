import { ref, watch } from 'vue';
import { doc, updateDoc } from "firebase/firestore";
import { db } from './firebase';

// make theme reactive
const currentTheme = ref('light');
const themeInitialised = ref(false);

//apply theme to doc 
function applyTheme(theme) {
  document.documentElement.setAttribute('data-theme', theme);
  localStorage.setItem('user-theme', theme);
  currentTheme.value = theme;
}

// initialise the theme 
function initTheme(userPreference = null) {
  if (themeInitialised.value) return;
  
  const savedTheme = localStorage.getItem('user-theme');
  
  if (userPreference) {
    applyTheme(userPreference);
  } else if (savedTheme) {
    applyTheme(savedTheme);
  } else {
    // set default as light 
    applyTheme('light');
  }
  
  themeInitialised.value = true;
}

// toggle the theme
function toggleTheme(userId = null) {
  const newTheme = currentTheme.value === 'light' ? 'dark' : 'light';
  applyTheme(newTheme);
  
  if (userId) {
    updateUserThemePreference(userId, newTheme);
  }
  
  return newTheme;
}

async function updateUserThemePreference(userId, theme) {
  if (!userId) return;
  
  try {
    const userRef = doc(db, "Investors", userId);
    await updateDoc(userRef, {
      themePreference: theme
    });
  } catch (err) {
    console.error("Error updating theme preference:", err);
  }
}

export {
  currentTheme,
  initTheme,
  applyTheme,
  toggleTheme
};