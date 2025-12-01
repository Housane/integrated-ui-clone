<template>
  <div class="login-bg" :style="{ backgroundImage: `url(${caiBg})` }">
    <div class="container">
      <div class="logo-wrapper">
      </div>

      <div class="login-box">
        <h2 class="login-title">Investor Login</h2>
        <p class="login-subtitle">
          Sign in to view your portfolio and predictions
        </p>

        <form @submit.prevent="handleLogin" class="form">
          <div class="form-group">
            <input
              v-model="email"
              type="email"
              required
              placeholder=" "
              class="form-input"
            />
            <label class="form-label">Email Address</label>
          </div>

          <div class="form-group">
            <input
              v-model="password"
              :type="showPassword ? 'text' : 'password'"
              required
              placeholder=" "
              class="form-input"
            />
            <label class="form-label">Password</label>
            <button
              type="button"
              class="show-button"
              @click="showPassword = !showPassword"
            >
              {{ showPassword ? "Hide" : "Show" }}
            </button>
          </div>

          <button type="submit" class="btn-signin">Sign In</button>

          <button
            type="button"
            class="btn-forgot"
            @click="goToForgotPassword"
          >
            Forgot Password?
          </button>
        </form>

        <button
          type="button"
          class="btn-google"
          @click="handleGoogleLogin"
        >
          <img
            src="../assets/google-icon.png"
            alt="Google Icon"
            class="google-icon"
          />
          <span>Continue with Google</span>
        </button>

        <button
          type="button"
          class="btn-signup"
          @click="goToSignup"
        >
          New here? Create an account
        </button>

        <p v-if="error" class="error-message">{{ error }}</p>
      </div>
    </div>
  </div>
</template>

<script>
import {
  signInWithEmailAndPassword,
  GoogleAuthProvider,
  signInWithPopup
} from "firebase/auth";
import { doc, getDoc, setDoc } from "firebase/firestore";
import { auth, db } from "../firebase";
import caiBg from '@/assets/cai.png';
import { initTheme } from '@/ThemeManager'; 

export default {
  name: "Login",
  data() {
    return {
      email: "",
      password: "",
      showPassword: false,
      error: "",
      caiBg
    };
  },
  mounted() {
    //initialise theme on login page
    initTheme();
  },
  methods: {
    async handleLogin() {
      this.error = "";
      try {
        const userCredential = await signInWithEmailAndPassword(
          auth,
          this.email,
          this.password
        );
        const user = userCredential.user;

        const docRef = doc(db, "Investors", user.uid);
        const docSnap = await getDoc(docRef);
        if (!docSnap.exists()) {
          await setDoc(doc(db, "Investors", user.uid), {
            email: user.email,
            firstname: "",
            lastname: "",
            contact: "",
            preferenceSet: false,
            themePreference: "light" // default theme preference
          });
        }
        this.$router.push("/general");
      } catch (err) {
        console.error("Login error:", err);
        this.error = err.message;
      }
    },
    async handleGoogleLogin() {
      this.error = "";
      try {
        const provider = new GoogleAuthProvider();
        provider.setCustomParameters({ prompt: "select_account" });
        const result = await signInWithPopup(auth, provider);
        const user = result.user;

        const docRef = doc(db, "Investors", user.uid);
        const docSnap = await getDoc(docRef);
        if (!docSnap.exists()) {
          await setDoc(doc(db, "Investors", user.uid), {
            email: user.email,
            firstname: "",
            lastname: "",
            contact: "",
            preferenceSet: false,
            themePreference: "light" //default theme preference
          });
        }
        this.$router.push("/general");
      } catch (err) {
        console.error("Google login error:", err);
        this.error = err.message;
      }
    },
    goToSignup() {
      this.$router.push("/signup");
    },
    goToForgotPassword() {
      this.$router.push("/forgot-password");
    }
  }
};
</script>

<style>
/* login does not need to scroll */
html, body {
  margin: 0;
  padding: 0;
  width: 100vw;
  height: 100vh;
  overflow: hidden;
  box-sizing: border-box;
}

*, *::before, *::after {
  box-sizing: border-box;
}
</style>

<style scoped>
.login-bg {
  position: fixed;
  top: 0;
  left: 0;
  width: 100vw;
  height: 100vh;
  background-size: cover;
  background-position: center center;
  background-repeat: no-repeat;
  display: flex;
  align-items: center;
  justify-content: center;
  overflow: hidden;
}

.container {
  width: 90vw;
  max-width: 380px;
  max-height: 85vh;
  display: flex;
  flex-direction: column;
  align-items: center;
  background: rgba(45, 55, 72, 0.95);
  border-radius: 20px;
  box-shadow: 0 0 30px rgba(0,0,0,0.25);
  padding: 1.5vh 1.5vw;
  overflow-y: auto;
}

.logo-wrapper {
  margin-bottom: 1px; 
}

.logo { /* Stonks man size */
  height: 100px;
  max-height: 80px;
  min-height: 60px;
}

.login-box { /*investor login component */
  width: 100%;
  display: flex;
  flex-direction: column;
  gap: 1vh; /* used for it to be variable */
}

.login-title { /* investor login title  */
  font-size: clamp(20px, 4vw, 28px);
  font-weight: bold;
  text-align: center;
  margin: 0;
  color: white;
}

.login-subtitle { /*sign in to view portfolio and predictions */
  text-align: center;
  color: #a0aec0;
  margin: 0 0 2vh 0;
  font-size: clamp(12px, 2.5vw, 16px);
}

.form { /* email address, password, sign in button gap */
  display: flex;
  flex-direction: column;
  gap: 1.5vh;
}

.form-group {
  position: relative;
}

.form-input { /* email add and pw fill in areas */

  width: 100%;
  height: 48px; 
  padding: 12px 16px; 
  padding-right: 64px; 
  background-color: #4a5568;
  color: white;
  border: 1px solid #718096;
  border-radius: 6px;
  font-size: 16px; 
  outline: none;
  box-sizing: border-box;

  /* ensure text not truncated */
  text-overflow: ellipsis;
  white-space: nowrap;
  overflow: hidden;
}

/* bug fix: make sure email autofill can see fully */
.form-input[type="email"] {
  padding-right: 2vw;
  font-size: 16px; 
}

.form-input:focus {
  border-color: #48bb78;
  box-shadow: 0 0 0 2px rgba(72, 187, 120, 0.2);
}

.form-label { 
  position: absolute;
  left: 16px;
  top: 50%;
  transform: translateY(-50%);
  color: #a0aec0;
  font-size: 16px;
  pointer-events: none;
  background-color: #4a5568;
  padding: 0 4px; 
}

.form-input:focus + .form-label,
.form-input:not(:placeholder-shown) + .form-label {
  top: 0;
  transform: translateY(-50%);
  font-size: clamp(10px, 1.8vw, 12px);
  color: #48bb78;
}

.show-button { /*show button for password*/
  position: absolute;
  right: 16px; 
  top: 50%;
  transform: translateY(-50%);
  background: none;
  border: none;
  color: #cbd5e0;
  font-weight: bold;
  cursor: pointer;
  font-size: 14px;
}

.show-button:hover {
  color: #edf2f7;
}

.btn-signin { /* signin button */
  width: 100%;
  background-color: #48bb78;
  color: white;
  padding: 1.5vh 0;
  min-height: 40px;
  border-radius: 6px;
  border: none;
  cursor: pointer;
  font-size: clamp(14px, 2.5vw, 16px);
  font-weight: 600;
}

.btn-signin:hover {
  background-color: #38a169;
}

.btn-forgot { /* forgot password button */
  width: 100%;
  background-color: transparent;
  color: #63b3ed;
  border: 1px solid #63b3ed;
  padding: 1.2vh 0;
  min-height: 36px;
  border-radius: 6px;
  cursor: pointer;
  font-size: clamp(12px, 2.2vw, 14px);
}

.btn-forgot:hover {
  background-color: #63b3ed;
  color: #1a202c;
}

.btn-google { /* login with goog button */
  width: 100%;
  display: flex;
  align-items: center;
  justify-content: center;
  background-color: #4a5568;
  color: white;
  padding: 1.2vh 0;
  min-height: 36px;
  border: 1px solid #718096;
  border-radius: 6px;
  cursor: pointer;
  font-size: clamp(12px, 2.2vw, 16px);
}

.btn-google:hover {
  background-color: #2d3748;
}

.google-icon {
  height: 3vh;
  width: 3vh;
  min-height: 16px;
  min-width: 16px;
  max-height: 20px;
  max-width: 20px;
  margin-right: 1vw;
}

.btn-signup { /* signup button */
  width: 100%; 
  background-color: transparent;
  color: #48bb78;
  border: 1px solid #48bb78;
  padding: 1.2vh 0;
  min-height: 36px;
  border-radius: 6px;
  cursor: pointer;
  font-size: clamp(12px, 2.2vw, 16px);
}

.btn-signup:hover {
  background-color: #48bb78;
  color: #1a202c;
}

.error-message {
  color: #f56565;
  font-size: clamp(10px, 2vw, 14px);
  text-align: center;
  margin: 1vh 0 0 0;
}

/* for phone */
@media (max-height: 600px) {
  .container {
    max-height: 95vh;
    padding: 1vh 2vw;
  }

  .logo {
    height: 6vh;
    min-height: 50px;
  }

  .form {
    gap: 1vh;
  }

  .login-subtitle {
    margin-bottom: 1vh;
  }
}

@media (max-width: 480px) {
  .container {
    width: 95vw;
    padding: 2vh 3vw;
  }
  
  /*email display for phone */
  .form-input[type="email"] {
    font-size: 13px;
  }
}

/* dark mode changes */
[data-theme="dark"] .container {
  background: rgba(25, 25, 25, 0.95);
  box-shadow: 0 0 30px rgba(0,0,0,0.5);
}
</style>