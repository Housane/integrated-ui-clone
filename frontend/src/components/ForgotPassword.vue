<template>
  <div class="forgot-bg" :style="{ backgroundImage: `url(${caiBg})` }">
    <div class="container">
      <div class="logo-wrapper">
      </div>

      <div class="reset-box">
        <h2 class="reset-title">Reset Investor Password</h2>
        <p class="reset-subtitle">
          Enter your email below and we'll send you a link to reset your account password if it exists.
        </p>

        <form @submit.prevent="sendResetEmail" class="form">
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

          <button type="submit" class="btn-signin">
            Send Reset Email
          </button>
        </form>

        <button
          type="button"
          class="btn-forgot"
          @click="goToLogin"
        >
          ← Back to Investor Login
        </button>

        <p v-if="message" class="success-message">{{ message }}</p>
        <p v-if="error" class="error-message">{{ error }}</p>
      </div>
    </div>
  </div>
</template>

<script>
import { sendPasswordResetEmail } from "firebase/auth";
import { auth } from "../firebase";
import caiBg from '@/assets/cai.png';
import { initTheme } from '@/ThemeManager'; 

export default {
  name: "ForgotPassword",
  data() {
    return {
      email: "",
      message: "",
      error: "",
      caiBg
    };
  },
  mounted() { //initiatise theme the moment the pg is pushed 
    initTheme();
  },
  methods: {
    async sendResetEmail() {
      this.message = "";
      this.error = "";

      const cleanEmail = this.email.trim();
      if (!cleanEmail) {
        this.error = "Please enter your email address.";
        return;
      }

      try {
        await sendPasswordResetEmail(auth, cleanEmail);
        this.message = " If an account with this email exists, a reset link will be sent to your inbox.";
        this.email = "";
      } catch (err) {
        console.error("Reset password error code:", err.code, err);
        if (err.code === "auth/user-not-found") {
          this.error = " No investor account found with this email.";
        } else if (err.code === "auth/invalid-email") {
          this.error = " The email address is badly formatted.";
        } else if (err.code === "auth/too-many-requests") {
          this.error = "Too many attempts. Please try again later.";
        } else {
          this.error = ` ${err.message}`;
        }
      }
    },

    goToLogin() {
      this.$router.push("/login");
    }
  }
};
</script>

<style>
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
.forgot-bg {
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
  padding: 2vh 2vw;
  overflow-y: auto;
}

.logo-wrapper {
  margin-bottom: 2vh;
}

.logo {
  height: 8vh;
  max-height: 80px;
  min-height: 60px;
}

.reset-box {
  width: 100%;
  display: flex;
  flex-direction: column;
  gap: 1.5vh;
}

.reset-title {
  font-size: clamp(20px, 4vw, 28px);
  font-weight: bold;
  text-align: center;
  margin: 0;
  color: white;
}

.reset-subtitle {
  text-align: center;
  color: #a0aec0;
  margin: 0 0 3vh 0;
  font-size: clamp(12px, 2.5vw, 16px);
  line-height: 1.4;
}

.form {
  display: flex;
  flex-direction: column;
  gap: 2vh;
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
  font-size: clamp(10px, 1.8vw, 12px);
  color: #48bb78;
}

.btn-signin {
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

.btn-forgot {
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

.error-message {
  color: #f56565;
  font-size: clamp(12px, 2.2vw, 14px);
  text-align: center;
  margin: 0;
}

.success-message {
  color: #48bb78;
  font-size: clamp(12px, 2.2vw, 14px);
  text-align: center;
  margin: 0;
  line-height: 1.4;
}

/* for phone screens*/
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
    gap: 1.5vh;
  }

  .reset-subtitle {
    margin-bottom: 2vh;
  }

  .reset-box {
    gap: 1vh;
  }
}

@media (max-width: 480px) {
  .container {
    width: 95vw;
    padding: 2vh 3vw;
  }
}

/* dark mode cchanges */
[data-theme="dark"] .container {
  background: rgba(25, 25, 25, 0.95);
  box-shadow: 0 0 30px rgba(0,0,0,0.5);
}
</style>