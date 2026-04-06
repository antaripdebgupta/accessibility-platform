/**
 * API Client
 *
 * Axios instance configured for the backend API.
 * Automatically injects Firebase ID token for authenticated requests.
 */

import axios from 'axios'

import { useAuthStore } from '../stores/auth'

// Create Axios instance with base configuration
const api = axios.create({
  baseURL: '/api/v1',
  timeout: 30000,
  headers: {
    'Content-Type': 'application/json',
  },
})

// Request Interceptor — Inject Authorization header and X-Organisation-ID

api.interceptors.request.use(
  async (config) => {
    // Get the auth store (must be called inside function after Pinia is ready)
    const authStore = useAuthStore()

    // If we have a token, add it to the request
    if (authStore.token) {
      config.headers.Authorization = `Bearer ${authStore.token}`
    }

    // Add X-Organisation-ID header for multi-tenancy
    // Lazy import to avoid circular dependency
    try {
      const { useOrgStore } = await import('../stores/org')
      const orgStore = useOrgStore()
      if (orgStore.current?.id) {
        config.headers['X-Organisation-ID'] = orgStore.current.id
      }
    } catch {
      // Org store not ready yet, skip header
    }

    return config
  },
  (error) => {
    return Promise.reject(error)
  },
)

// Response Interceptor — Handle errors globally

api.interceptors.response.use(
  (response) => {
    return response
  },
  async (error) => {
    const originalRequest = error.config

    if (error.response?.status === 401 && !originalRequest._retry) {
      originalRequest._retry = true

      try {
        const authStore = useAuthStore()
        const newToken = await authStore.refreshToken()

        if (newToken) {
          originalRequest.headers.Authorization = `Bearer ${newToken}`
          return api(originalRequest)
        }
      } catch (refreshError) {
        // Token refresh failed, redirect to login
        const authStore = useAuthStore()
        await authStore.logout()
        window.location.href = '/signin'
        return Promise.reject(refreshError)
      }
    }

    // Format error for easier handling in components
    const formattedError = {
      message:
        error.response?.data?.detail ||
        error.response?.data?.message ||
        error.message ||
        'An unexpected error occurred',
      status: error.response?.status,
      data: error.response?.data,
    }

    return Promise.reject(formattedError)
  },
)

// API Methods — Type-safe wrappers

export const apiClient = {
  // Health check endpoint
  health() {
    return api.get('/health')
  },

  //Auth endpoints (to be added on Day 2+)
  // auth: {
  //   me() { return api.get('/auth/me') },
  // },

  // ── Evaluation endpoints (to be added on Day 2+)
  // evaluations: {
  //   list() { return api.get('/evaluations') },
  //   get(id) { return api.get(`/evaluations/${id}`) },
  //   create(data) { return api.post('/evaluations', data) },
  // },
}

// Export the raw axios instance for custom requests
export default api
