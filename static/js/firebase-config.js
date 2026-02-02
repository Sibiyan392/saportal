// Firebase Configuration
const firebaseConfig = {
    apiKey: "AIzaSyDybVVX0exTTH5paRgTlb_TyDn1qHsNVNM",
    authDomain: "atsfit-47490.firebaseapp.com",
    projectId: "atsfit-47490",
    storageBucket: "atsfit-47490.firebasestorage.app",
    messagingSenderId: "1087715598568",
    appId: "1:1087715598568:web:4bb6bd6692ad1f3d94695d",
    measurementId: "G-S1F72BXHBV"
};

// Initialize Firebase
firebase.initializeApp(firebaseConfig);
const auth = firebase.auth();
const db = firebase.firestore();
const analytics = firebase.analytics();

// Firebase Auth State Listener
auth.onAuthStateChanged((user) => {
    if (user) {
        // User is signed in
        document.body.classList.add('user-signed-in');
        updateUIForUser(user);
        console.log("User signed in:", user.email || "Anonymous");
        
        // Check if we need to create user document
        createUserDocument(user);
    } else {
        // User is signed out
        document.body.classList.remove('user-signed-in');
        console.log("User signed out");
    }
});

// Create user document in Firestore if it doesn't exist
async function createUserDocument(user) {
    if (!user || !db) return;
    
    try {
        const userRef = db.collection('users').doc(user.uid);
        const doc = await userRef.get();
        
        if (!doc.exists) {
            await userRef.set({
                email: user.email || null,
                createdAt: firebase.firestore.FieldValue.serverTimestamp(),
                lastLogin: firebase.firestore.FieldValue.serverTimestamp(),
                preferences: {
                    smsAlerts: false,
                    emailUpdates: true,
                    theme: 'auto',
                    location: null
                }
            });
            console.log("User document created");
        } else {
            // Update last login
            await userRef.update({
                lastLogin: firebase.firestore.FieldValue.serverTimestamp()
            });
        }
    } catch (error) {
        console.error("Error creating user document:", error);
    }
}

// Sign in anonymously
async function signInAnonymously() {
    try {
        await auth.signInAnonymously();
        analytics.logEvent('anonymous_sign_in');
        return true;
    } catch (error) {
        console.error("Anonymous sign in error:", error);
        return false;
    }
}

// Sign up with email/password
async function signUpWithEmail(email, password) {
    try {
        const userCredential = await auth.createUserWithEmailAndPassword(email, password);
        analytics.logEvent('email_sign_up', { method: 'email' });
        return { success: true, user: userCredential.user };
    } catch (error) {
        console.error("Sign up error:", error);
        return { success: false, error: error.message };
    }
}

// Sign in with email/password
async function signInWithEmail(email, password) {
    try {
        const userCredential = await auth.signInWithEmailAndPassword(email, password);
        analytics.logEvent('email_sign_in', { method: 'email' });
        return { success: true, user: userCredential.user };
    } catch (error) {
        console.error("Sign in error:", error);
        return { success: false, error: error.message };
    }
}

// Sign out
async function signOutUser() {
    try {
        await auth.signOut();
        analytics.logEvent('sign_out');
        return true;
    } catch (error) {
        console.error("Sign out error:", error);
        return false;
    }
}

// Get current user token
async function getCurrentUserToken() {
    const user = auth.currentUser;
    if (user) {
        try {
            const token = await user.getIdToken();
            return token;
        } catch (error) {
            console.error("Error getting token:", error);
            return null;
        }
    }
    return null;
}

// Update user preferences
async function updateUserPreferences(preferences) {
    const user = auth.currentUser;
    if (!user || !db) return { success: false, error: "Not authenticated" };
    
    try {
        const userRef = db.collection('users').doc(user.uid);
        await userRef.update({
            'preferences': preferences
        });
        return { success: true };
    } catch (error) {
        console.error("Error updating preferences:", error);
        return { success: false, error: error.message };
    }
}

// Save location to user profile
async function saveUserLocation(location, coordinates) {
    const user = auth.currentUser;
    if (!user || !db) return { success: false, error: "Not authenticated" };
    
    try {
        const userRef = db.collection('users').doc(user.uid);
        await userRef.update({
            'preferences.location': location,
            'preferences.coordinates': coordinates
        });
        return { success: true };
    } catch (error) {
        console.error("Error saving location:", error);
        return { success: false, error: error.message };
    }
}

// Initialize on page load
document.addEventListener('DOMContentLoaded', function() {
    // Auto sign in anonymously if not signed in
    setTimeout(() => {
        if (!auth.currentUser) {
            signInAnonymously();
        }
    }, 1000);
    
    // Update UI based on auth state
    updateUIForUser(auth.currentUser);
});

function updateUIForUser(user) {
    const authElements = document.querySelectorAll('[data-auth]');
    
    authElements.forEach(element => {
        const authState = element.getAttribute('data-auth');
        
        if (authState === 'signed-in' && user) {
            element.style.display = '';
        } else if (authState === 'signed-out' && !user) {
            element.style.display = '';
        } else if (authState === 'signed-in' && !user) {
            element.style.display = 'none';
        } else if (authState === 'signed-out' && user) {
            element.style.display = 'none';
        }
        
        // Update user info in elements
        if (user && element.classList.contains('user-email')) {
            element.textContent = user.email || 'Guest User';
        }
    });
}

// Export for use in other files
window.firebaseAuth = {
    auth,
    db,
    signInAnonymously,
    signUpWithEmail,
    signInWithEmail,
    signOutUser,
    getCurrentUserToken,
    updateUserPreferences,
    saveUserLocation
};