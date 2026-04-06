/**
 * Application Entry Point
 *
 * Initializes Vue app with Pinia (state management) and Vue Router.
 */

import { createPinia } from 'pinia'
import { createApp } from 'vue'

import App from './App.vue'
import router from './router'
import { useAuthStore } from './stores/auth'
import './style.css'

// Create Vue app
const app = createApp(App)

// Create Pinia store
const pinia = createPinia()

// Register plugins
app.use(pinia)
app.use(router)

// Initialize auth listener before mounting
// This ensures auth state is ready when the app renders
const authStore = useAuthStore()
authStore.initAuthListener().then(async () => {
  // After auth is initialized, fetch organisations so the UI (Navbar/org switcher)
  // can render organisation links immediately.
  if (authStore.isAuthenticated) {
    try {
      // Dynamic import to avoid circular dependency issues
      const { useOrgStore } = await import('./stores/org')
      const orgStore = useOrgStore()
      await orgStore.fetchMyOrgs()
    } catch (e) {
      // Non-fatal: log and continue mounting the app
      // (UI will show empty state and user can retry)
      console.error('Failed to load organisations on startup:', e)
    }
  }

  // Mount app after auth and orgs are ready
  app.mount('#app')
})
