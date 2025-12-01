import { auth, db } from '../firebase'; 
import { doc, updateDoc, getDoc, arrayUnion, arrayRemove } from 'firebase/firestore';

export default {
  async getFavourites() {
    if (!auth.currentUser) {
      return [];
    }
    
    try {
      const userRef = doc(db, 'users', auth.currentUser.uid);
      const userSnap = await getDoc(userRef);
      
      if (userSnap.exists() && userSnap.data().favourites) {
        return userSnap.data().favourites;
      } else {
        return [];
      }
    } catch (error) {
      console.error('Error getting favourites:', error);
      return [];
    }
  },
  
  async addFavourite(stock) {
    if (!auth.currentUser) {
      return false;
    }
    
    const favouriteStock = {
      symbol: stock.symbol,
      name: stock.name,
      addedAt: new Date().toISOString()
    };
    
    try {
      const userRef = doc(db, 'users', auth.currentUser.uid);
      
      //check if already favourited 
      const userSnap = await getDoc(userRef);
      const currentFavourites = userSnap.exists() && userSnap.data().favourites 
        ? userSnap.data().favourites 
        : [];
        
      if (currentFavourites.some(fav => fav.symbol === stock.symbol)) {
        return true;
      }
      
      await updateDoc(userRef, {
        favourites: arrayUnion(favouriteStock)
      });
      
      return true;
    } catch (error) {
      console.error('Error adding favourite:', error);
      return false;
    }
  },
  
  async removeFavourite(symbol) {
    if (!auth.currentUser) {
      return false;
    }
    
    try {
      const userRef = doc(db, 'users', auth.currentUser.uid);
      
      const userSnap = await getDoc(userRef);
      const currentFavourites = userSnap.exists() && userSnap.data().favourites 
        ? userSnap.data().favourites 
        : [];
      
      const stockToRemove = currentFavourites.find(fav => fav.symbol === symbol);
      if (!stockToRemove) {
        return true; 
      }
      
      await updateDoc(userRef, {
        favourites: arrayRemove(stockToRemove)
      });
      
      return true;
    } catch (error) {
      console.error('Error removing favourite:', error);
      return false;
    }
  },
  
  async isFavourite(symbol) {
    const favourites = await this.getFavourites();
    return favourites.some(fav => fav.symbol === symbol);
  }
};