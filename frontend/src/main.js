

import { createApp } from 'vue';
import App from './App.vue';
import router from './router';   
import './style.css';
import './assets/themes.css' 
import { initTheme } from './ThemeManager' 


initTheme();

const app = createApp(App);
app.use(router); // to use our router         
app.mount('#app');

