<template>
  <div class="signup-bg" :style="{ backgroundImage: `url(${caiBg})` }">
    <div class="container">
      <div class="logo-wrapper">
      </div>

      <div class="signup-box">
        <h2 class="signup-title">Create Your Investor Account</h2>
        <p class="signup-subtitle">
          Join now and receive real-time stock predictions tailored to your portfolio.
        </p>

        <form @submit.prevent="handleSignup" class="form">
          <div class="form-group">
            <input
              v-model="firstName"
              type="text"
              required
              placeholder=" "
              class="form-input"
            />
            <label class="form-label">First Name</label>
          </div>

          <div class="form-group">
            <input
              v-model="lastName"
              type="text"
              required
              placeholder=" "
              class="form-input"
            />
            <label class="form-label">Last Name</label>
          </div>

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
              v-model="phone"
              type="text"
              placeholder=" "
              class="form-input"
            />
            <label class="form-label">Phone Number (Optional)</label>
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

          <div class="form-group">
            <input
              v-model="confirmPassword"
              :type="showPassword ? 'text' : 'password'"
              required
              placeholder=" "
              class="form-input"
            />
            <label class="form-label">Confirm Password</label>
          </div>

          <div class="terms-wrapper">
            <input
              v-model="agreed"
              type="checkbox"
              id="terms"
              required
              class="terms-checkbox"
            />
            <label for="terms" class="terms-label">
              I agree to the
              <span class="terms-link">Terms of Service</span>
              and
              <span class="terms-link">Privacy Policy</span>
            </label>
          </div>

          <button type="submit" class="btn-signin">Create Account</button>
        </form>

        <button type="button" class="btn-google" @click="handleGoogleSignup">
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
          @click="goToLogin"
        >
          Already have an account? Sign in here
        </button>

        <p v-if="error" class="error-message">{{ error }}</p>
        <p v-if="message" class="success-message">{{ message }}</p>
      </div>
    </div>
  </div>
</template>

<script>
import {
  createUserWithEmailAndPassword,
  GoogleAuthProvider,
  signInWithPopup
} from "firebase/auth";
import { doc, setDoc, collection, getDoc } from "firebase/firestore";
import { auth, db } from "../firebase";
import caiBg from '@/assets/cai.png';
import { initTheme } from '@/ThemeManager';

export default {
  name: "Signup",
  data() {
    return {
      firstName: "",
      lastName: "",
      email: "",
      phone: "",
      password: "",
      confirmPassword: "",
      showPassword: false,
      agreed: false,
      message: "",
      error: "",
      caiBg
    };
  },
  mounted() {
    initTheme();
  },
  methods: {
    async handleSignup() {
      this.message = "";
      this.error = "";

      if (this.password !== this.confirmPassword) {
        this.error = "Passwords do not match.";
        return;
      }
      if (!this.agreed) {
        this.error = "You must agree to Terms & Privacy.";
        return;
      }

      try {
        const userCredential = await createUserWithEmailAndPassword(
          auth,
          this.email.trim().toLowerCase(),
          this.password
        );
        const user = userCredential.user;

        await setDoc(doc(collection(db, "Investors"), user.uid), {
          email: this.email.trim().toLowerCase(),
          firstname: this.firstName,
          lastname: this.lastName,
          contact: this.phone || "",
          preferenceSet: false,
          themePreference: "light"
        });

        this.message = "Account created! Redirecting to login…";
        setTimeout(() => {
          this.$router.push("/login");
        }, 1200);
      } catch (err) {
        console.error("Error in signup:", err);
        this.error = err.message;
      }
    },

    async handleGoogleSignup() {
      this.message = "";
      this.error = "";
      try {
        const provider = new GoogleAuthProvider();
        provider.setCustomParameters({ prompt: "select_account" });
        const result = await signInWithPopup(auth, provider);
        const user = result.user;

        const docRef = doc(db, "Investors", user.uid);
        const docSnap = await getDoc(docRef);
        if (!docSnap.exists()) {
          await setDoc(docRef, {
            email: user.email.trim().toLowerCase(),
            firstname: "",
            lastname: "",
            contact: "",
            preferenceSet: false,
            themePreference: "light" 
          });
        }
        this.$router.push("/preferences");
      } catch (err) {
        console.error("Google signup error:", err);
        this.error = err.message;
      }
    },

    goToLogin() {
      this.$router.push("/login");
    }
  }
};
</script>

<style scoped>
.signup-bg {
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
  min-height: 100vh; 
  display: flex; 
  flex-direction: column; 
  align-items: center;
  color: white; 
  padding: 100px; 
  justify-content: center;
}

.logo-wrapper {
  margin-bottom: 25px;
}

.logo {
  height: 120px;
}

.signup-box {
  width: 100%; 
  max-width: 430px; 
  background-color: rgba(45, 55, 72, 0.95); 
  border-radius: 30px;
  box-shadow: 0 0 15px rgba(0, 0, 0, 0.2); 
  padding: 32px; 
  display: flex;
  flex-direction: column; 
  gap: 10px;
}

.signup-title {
  font-size: 30px;
  font-weight: bold;
  text-align: center;
  color: white;
}

.signup-subtitle {
  text-align: center;
  color: #a0aec0;
  margin-bottom: 16px;
  margin-top: 1px;
}

.form {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.form-group {
  position: relative;
}

.form-input {
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
  font-size: 12px;
  color: #48bb78;
}

.show-button {
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

.terms-wrapper {
  display: flex;
  align-items: center;
  gap: 8px;
}

.terms-checkbox {
  width: 16px;
  height: 16px;
  accent-color: #48bb78;
}

.terms-label {
  color: #a0aec0;
  font-size: 14px;
}

.terms-link {
  color: #48bb78;
  text-decoration: underline;
  cursor: pointer;
}

.btn-signin {
  width: 100%; 
  background-color: #48bb78; 
  color: white; 
  padding: 12px; 
  border-radius: 6px;
  border: none; 
  cursor: pointer; 
  font-size: 16px; 
  font-weight: 600;
}

.btn-signin:hover {
  background-color: #38a169;
}

.btn-google {
  width: 100%; 
  display: flex; 
  align-items: center; 
  justify-content: center; 
  background-color: #4a5568;
  color: white; 
  padding: 12px; 
  border: 1px solid #718096; 
  border-radius: 6px; 
  cursor: pointer;
  font-size: 16px;
}

.btn-google:hover {
  background-color: #2d3748;
}

.google-icon {
  height: 20px;
  width: 20px;
  margin-right: 8px;
}

.btn-signup {
  width: 100%; 
  background-color: transparent; 
  color: #48bb78; 
  border: 1px solid #48bb78;
  padding: 12px; 
  border-radius: 6px; 
  cursor: pointer; 
  font-size: 16px;
}

.btn-signup:hover {
  background-color: #48bb78;
  color: #1a202c;
}

.error-message {
  color: #f56565;
  font-size: 14px;
  text-align: center;
}

.success-message {
  color: #48bb78;
  font-size: 14px;
  text-align: center;
}

/* change background of signup box when dark */
[data-theme="dark"] .signup-box {
  background-color: rgba(25, 25, 25, 0.95);
  box-shadow: 0 0 15px rgba(0, 0, 0, 0.5);
}
</style>