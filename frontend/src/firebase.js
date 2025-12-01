

import { initializeApp } from 'firebase/app';
import { getAuth } from 'firebase/auth';
import { getFirestore } from 'firebase/firestore';

//FB Config
const firebaseConfig = {
  apiKey: "AIzaSyCoPWzcwBmdRVF3i-euIub6er9WjpmicB0",
  authDomain: "ggwoman-b43ef.firebaseapp.com",
  projectId: "ggwoman-b43ef",
  storageBucket: "ggwoman-b43ef.firebasestorage.app",
  messagingSenderId: "759029361023",
  appId: "1:759029361023:web:a0b489fa4db55f5255d24a",
};

// FB initialisation
const app = initializeApp(firebaseConfig);
const auth = getAuth(app);
const db = getFirestore(app);

export { auth, db };
