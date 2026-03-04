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
authStore.initAuthListener().then(() => {
  // Mount app after auth is initialized
  app.mount('#app')
})
