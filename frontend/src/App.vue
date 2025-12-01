<template>
  <router-view/>
</template>

<script>
import { onMounted } from 'vue';
import { onAuthStateChanged } from 'firebase/auth';
import { doc, getDoc } from 'firebase/firestore';
import { auth, db } from './firebase';
import { initTheme } from './ThemeManager';

export default {
  name: 'App',
  setup() {
    onMounted(() => {
      // Check if user is logged in and retrieve theme preference
      onAuthStateChanged(auth, async (user) => {
        if (user) {
          try {
            const docRef = doc(db, "Investors", user.uid);
            const docSnap = await getDoc(docRef);
            
            if (docSnap.exists() && docSnap.data().themePreference) {
              // Initialize with user's theme preference
              initTheme(docSnap.data().themePreference);
            } else {
              // Initialize with default theme
              initTheme();
            }
          } catch (err) {
            console.error("Error fetching theme preference:", err);
            initTheme();
          }
        } else {
          // No user logged in, use default theme
          initTheme();
        }
      });
    });
    
    return {};
  }
};
</script>

<style>
/* Global styles that should apply to all components */
body {
  margin: 0;
  padding: 0;
  font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Oxygen, Ubuntu, Cantarell, 'Open Sans', 'Helvetica Neue', sans-serif;
  background-color: var(--color-background);
  color: var(--color-text-primary);
}
</style>