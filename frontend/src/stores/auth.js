import {
  createUserWithEmailAndPassword,
  signOut as firebaseSignOut,
  onAuthStateChanged,
  signInWithEmailAndPassword,
} from 'firebase/auth'
import { defineStore } from 'pinia'
import { computed, ref } from 'vue'

import { auth } from '../lib/firebase'

export const useAuthStore = defineStore('auth', () => {
  const user = ref(null)

  const token = ref(null)

  const initialized = ref(false)

  const loading = ref(false)

  const error = ref(null)

  const isAuthenticated = computed(() => !!user.value)

  const userEmail = computed(() => user.value?.email || null)

  const userId = computed(() => user.value?.uid || null)

  function initAuthListener() {
    return new Promise((resolve) => {
      onAuthStateChanged(auth, async (firebaseUser) => {
        if (firebaseUser) {
          user.value = {
            uid: firebaseUser.uid,
            email: firebaseUser.email,
            displayName: firebaseUser.displayName,
            photoURL: firebaseUser.photoURL,
            emailVerified: firebaseUser.emailVerified,
          }
          try {
            token.value = await firebaseUser.getIdToken()
          } catch (e) {
            console.error('Failed to get ID token:', e)
            token.value = null
          }
        } else {
          user.value = null
          token.value = null
        }
        initialized.value = true
        resolve(user.value)
      })
    })
  }

  async function login(email, password) {
    loading.value = true
    error.value = null

    try {
      const userCredential = await signInWithEmailAndPassword(
        auth,
        email,
        password,
      )
      return userCredential.user
    } catch (e) {
      error.value = getAuthErrorMessage(e.code)
      return null
    } finally {
      loading.value = false
    }
  }

  async function signUp(email, password) {
    loading.value = true
    error.value = null

    try {
      const userCredential = await createUserWithEmailAndPassword(
        auth,
        email,
        password,
      )
      return userCredential.user
    } catch (e) {
      error.value = getAuthErrorMessage(e.code)
      return null
    } finally {
      loading.value = false
    }
  }

  async function logout() {
    loading.value = true
    error.value = null

    try {
      await firebaseSignOut(auth)
      user.value = null
      token.value = null

      // Clear organisation state on logout
      const { useOrgStore } = await import('./org')
      const orgStore = useOrgStore()
      orgStore.clear()
      localStorage.removeItem('current_org_id')
    } catch (e) {
      error.value = 'Failed to sign out. Please try again.'
      console.error('Logout error:', e)
    } finally {
      loading.value = false
    }
  }

  async function refreshToken() {
    if (!auth.currentUser) {
      token.value = null
      return null
    }

    try {
      token.value = await auth.currentUser.getIdToken(true)
      return token.value
    } catch (e) {
      console.error('Failed to refresh token:', e)
      token.value = null
      return null
    }
  }

  function clearError() {
    error.value = null
  }

  function getAuthErrorMessage(code) {
    const messages = {
      'auth/user-not-found': 'No account found with this email address.',
      'auth/wrong-password': 'Incorrect password. Please try again.',
      'auth/invalid-email': 'Please enter a valid email address.',
      'auth/user-disabled': 'This account has been disabled.',
      'auth/email-already-in-use': 'An account with this email already exists.',
      'auth/weak-password': 'Password should be at least 6 characters.',
      'auth/too-many-requests':
        'Too many failed attempts. Please try again later.',
      'auth/network-request-failed':
        'Network error. Please check your connection.',
      'auth/invalid-credential': 'Invalid email or password.',
    }
    return messages[code] || 'An error occurred. Please try again.'
  }

  return {
    // State
    user,
    token,
    initialized,
    loading,
    error,
    // Getters
    isAuthenticated,
    userEmail,
    userId,
    // Actions
    initAuthListener,
    login,
    signUp,
    logout,
    refreshToken,
    clearError,
  }
})
