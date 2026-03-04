// Firebase initialization (modular v9) - Auth only
import { initializeApp } from 'firebase/app'
import { connectAuthEmulator, getAuth } from 'firebase/auth'

// Check if we're using Firebase emulator (set via env var)
const useEmulator = import.meta.env.VITE_USE_FIREBASE_EMULATOR === 'true'

// Use Vite environment variables (VITE_ prefix)
const firebaseConfig = {
  apiKey: import.meta.env.VITE_FIREBASE_API_KEY,
  authDomain: import.meta.env.VITE_FIREBASE_AUTH_DOMAIN,
  projectId: import.meta.env.VITE_FIREBASE_PROJECT_ID,
  appId: import.meta.env.VITE_FIREBASE_APP_ID,
}

// Validate required config
if (!firebaseConfig.apiKey || firebaseConfig.apiKey === 'your-firebase-api-key') {
  console.error('Firebase configuration error: Missing or invalid VITE_FIREBASE_API_KEY')
  console.error('Please set Firebase environment variables in your .env file')
}

// Initialize Firebase app
const app = initializeApp(firebaseConfig)

// Initialize Auth
const auth = getAuth(app)

// Connect to emulator if enabled
if (useEmulator) {
  const host = import.meta.env.VITE_FIREBASE_EMULATOR_HOST || '127.0.0.1'
  const authPort = Number(
    import.meta.env.VITE_FIREBASE_AUTH_EMULATOR_PORT || 9099,
  )
  const url = `http://${host}:${authPort}`

  try {
    connectAuthEmulator(auth, url, { disableWarnings: true })
    console.info('Connected to Firebase Auth emulator at', url)
  } catch (e) {
    console.warn('Could not connect to Auth emulator', e?.message || e)
  }
}

export { auth }
