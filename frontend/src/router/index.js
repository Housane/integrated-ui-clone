import { createRouter, createWebHistory } from "vue-router";
import { getAuth } from "firebase/auth";

import Login from "../components/Login.vue";
import Signup from "../components/Signup.vue";
import ForgotPassword from "../components/ForgotPassword.vue";
import Dashboard from "../components/Dashboard.vue";
import AccountSettings from "../components/AccountSettings.vue";
import EditProfile from "../components/EditProfile.vue";
import GeneralPage from "../components/GeneralPage.vue";
import favouritestocks from "../components/favouritestocks.vue";
import Comments from "../components/comments.vue";

const routes = [
  { path: "/", redirect: "/login" },
  { path: "/login", component: Login },
  { path: "/signup", component: Signup },
  { path: "/forgot-password", component: ForgotPassword },
  { path: "/dashboard", component: Dashboard, meta: { requiresAuth: true } },
  { path: "/general", component: GeneralPage, meta: { requiresAuth: true } },
  { path: "/account-settings", component: AccountSettings, meta: { requiresAuth: true } },
  { path: "/edit-profile", component: EditProfile, meta: { requiresAuth: true } }, 
  { path: "/favourites", component: favouritestocks, meta: { requiresAuth: true } },
   {path: '/stock/:symbol/comments', name: 'StockComments', component: Comments},
  { path: "/:catchAll(.*)", redirect: "/login" }
];

const router = createRouter({
  history: createWebHistory(),
  routes
});

router.beforeEach((to, from, next) => {
  const auth = getAuth();
  const user = auth.currentUser;

  if (to.meta.requiresAuth && !user) {
    next("/login");
  } else if (user && to.path === '/login') {
    next('/general');
  } else if (user && to.path === '/') {
    next('/general');
  } else {
    next();
  }
});

export default router;