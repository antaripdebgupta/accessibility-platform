/**
 * Profiles Pinia Store
 *
 * Manages disability profile state including:
 * - Available profiles (fetched from API)
 * - Active profile selection
 * - localStorage persistence
 */

import { defineStore } from 'pinia'
import { computed, ref } from 'vue'
import api from '../lib/api'

const STORAGE_KEY = 'active_profile'

// Valid profile IDs for validation
const VALID_PROFILE_IDS = ['blind', 'low_vision', 'motor', 'cognitive']

export const useProfilesStore = defineStore('profiles', () => {
  // State
  const profiles = ref([])
  const activeProfile = ref(null)
  const loading = ref(false)
  const error = ref(null)

  // Computed
  const hasActiveProfile = computed(() => activeProfile.value !== null)

  const activeProfileData = computed(() => {
    if (!activeProfile.value) return null
    return profiles.value.find((p) => p.id === activeProfile.value) || null
  })

  const activeProfileName = computed(() => {
    return activeProfileData.value?.name || null
  })

  async function fetchProfiles() {
    loading.value = true
    error.value = null

    try {
      const response = await api.get('/profiles')
      profiles.value = response.data.profiles || []
      return profiles.value
    } catch (err) {
      error.value = err.message || 'Failed to fetch profiles'
      console.error('Failed to fetch profiles:', err)
      throw err
    } finally {
      loading.value = false
    }
  }

  async function fetchProfileDetail(profileId) {
    try {
      const response = await api.get(`/profiles/${profileId}`)
      return response.data
    } catch (err) {
      console.error('Failed to fetch profile detail:', err)
      throw err
    }
  }

  function setActiveProfile(profileId) {
    if (profileId === null) {
      activeProfile.value = null
      localStorage.removeItem(STORAGE_KEY)
      return
    }

    // Validate profile ID
    if (!VALID_PROFILE_IDS.includes(profileId)) {
      console.warn(`Invalid profile ID: ${profileId}`)
      return
    }

    activeProfile.value = profileId
    localStorage.setItem(STORAGE_KEY, profileId)
  }

  function clearProfile() {
    activeProfile.value = null
    localStorage.removeItem(STORAGE_KEY)
  }

  function restoreFromStorage() {
    const stored = localStorage.getItem(STORAGE_KEY)
    if (stored && VALID_PROFILE_IDS.includes(stored)) {
      activeProfile.value = stored
    }
  }

  function getProfileColorClass(profileId, isActive = false) {
    const colorMap = {
      blind: isActive
        ? 'border-blue-600 bg-blue-50'
        : 'border-gray-200 hover:border-blue-300',
      low_vision: isActive
        ? 'border-amber-500 bg-amber-50'
        : 'border-gray-200 hover:border-amber-300',
      motor: isActive
        ? 'border-green-600 bg-green-50'
        : 'border-gray-200 hover:border-green-300',
      cognitive: isActive
        ? 'border-purple-600 bg-purple-50'
        : 'border-gray-200 hover:border-purple-300',
    }
    return colorMap[profileId] || 'border-gray-200'
  }

  function getProfileBadgeClass(profileId) {
    const colorMap = {
      blind: 'bg-blue-100 text-blue-800 border-blue-200',
      low_vision: 'bg-amber-100 text-amber-800 border-amber-200',
      motor: 'bg-green-100 text-green-800 border-green-200',
      cognitive: 'bg-purple-100 text-purple-800 border-purple-200',
    }
    return colorMap[profileId] || 'bg-gray-100 text-gray-800 border-gray-200'
  }

  // Initialize from storage on store creation
  restoreFromStorage()

  return {
    // State
    profiles,
    activeProfile,
    loading,
    error,
    // Computed
    hasActiveProfile,
    activeProfileData,
    activeProfileName,
    // Actions
    fetchProfiles,
    fetchProfileDetail,
    setActiveProfile,
    clearProfile,
    restoreFromStorage,
    // Helpers
    getProfileColorClass,
    getProfileBadgeClass,
  }
})
