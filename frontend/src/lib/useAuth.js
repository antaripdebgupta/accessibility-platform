import { onAuthStateChanged } from 'firebase/auth'
import { ref } from 'vue'
import { auth } from './firebase'

// central reactive user state for the app
const currentUser = ref(null)

let initialized = false

export function initAuthListener() {
  if (initialized) return
  initialized = true
  onAuthStateChanged(auth, (u) => {
    currentUser.value = u ? { uid: u.uid, email: u.email } : null
  })
}

export function useAuth() {
  function isAuthenticated() {
    return !!currentUser.value
  }

  return {
    currentUser,
    isAuthenticated,
  }
}
