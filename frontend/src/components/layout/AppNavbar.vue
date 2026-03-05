<template>
  <nav
    class="fixed left-0 right-0 top-0 z-50 border-b border-gray-200 bg-white"
  >
    <div class="mx-auto max-w-7xl px-4 sm:px-6 lg:px-8">
      <div class="flex h-16 items-center justify-between">
        <!-- Left side: Logo and brand -->
        <RouterLink
          to="/dashboard"
          class="flex items-center space-x-2 text-gray-900 focus:outline-none"
        >
          <span class="text-lg font-semibold text-gray-900">AccessHub</span>
        </RouterLink>

        <!-- Right side: Org name, user info, avatar dropdown -->
        <div class="flex items-center space-x-4">
          <!-- Current org name -->
          <span
            v-if="currentOrgName"
            class="hidden text-sm text-gray-500 sm:block"
          >
            {{ currentOrgName }}
          </span>

          <!-- User display name or email -->
          <span class="hidden text-sm font-medium text-gray-700 md:block">
            {{ displayName }}
          </span>

          <!-- Avatar dropdown -->
          <div class="relative" ref="dropdownRef">
            <button
              type="button"
              class="flex items-center justify-center rounded-full bg-indigo-600 text-sm font-medium text-white focus:outline-none focus:ring-2 focus:ring-indigo-500 focus:ring-offset-2"
              :class="avatarSizeClasses"
              @click="toggleDropdown"
              @keydown.enter.prevent="toggleDropdown"
              @keydown.space.prevent="toggleDropdown"
              @keydown.escape="closeDropdown"
              :aria-expanded="isDropdownOpen"
              aria-haspopup="true"
              aria-label="User menu"
            >
              <span aria-hidden="true">{{ initials }}</span>
            </button>

            <!-- Dropdown menu -->
            <Transition
              enter-active-class="transition ease-out duration-100"
              enter-from-class="transform opacity-0 scale-95"
              enter-to-class="transform opacity-100 scale-100"
              leave-active-class="transition ease-in duration-75"
              leave-from-class="transform opacity-100 scale-100"
              leave-to-class="transform opacity-0 scale-95"
            >
              <div
                v-if="isDropdownOpen"
                class="absolute right-0 mt-2 w-48 origin-top-right rounded-md bg-white py-1 shadow-lg ring-1 ring-black ring-opacity-5 focus:outline-none"
                role="menu"
                aria-orientation="vertical"
                aria-labelledby="user-menu-button"
              >
                <!-- User info in dropdown (mobile) -->
                <div class="border-b border-gray-100 px-4 py-2 md:hidden">
                  <p class="text-sm font-medium text-gray-900">
                    {{ displayName }}
                  </p>
                  <p
                    v-if="authStore.userEmail"
                    class="truncate text-xs text-gray-500"
                  >
                    {{ authStore.userEmail }}
                  </p>
                </div>

                <!-- Sign out option -->
                <button
                  type="button"
                  class="block w-full px-4 py-2 text-left text-sm text-gray-700 hover:bg-gray-100 focus:bg-gray-100 focus:outline-none"
                  role="menuitem"
                  @click="handleSignOut"
                  @keydown.enter.prevent="handleSignOut"
                  @keydown.space.prevent="handleSignOut"
                >
                  Sign out
                </button>
              </div>
            </Transition>
          </div>
        </div>
      </div>
    </div>
  </nav>
</template>

<script setup>
import { computed, onMounted, onUnmounted, ref } from 'vue'
import { RouterLink, useRouter } from 'vue-router'

import { useAuthStore } from '../../stores/auth'

const router = useRouter()
const authStore = useAuthStore()

// Dropdown state
const isDropdownOpen = ref(false)
const dropdownRef = ref(null)

// Computed properties
const displayName = computed(() => {
  return authStore.user?.displayName || authStore.userEmail || 'User'
})

const currentOrgName = computed(() => {
  // This will be populated when we have org data from auth
  // For now, return null to hide the org name display
  return authStore.currentOrg?.name || null
})

const initials = computed(() => {
  const name = displayName.value
  if (!name) return '?'

  const parts = name.trim().split(/\s+/)
  if (parts.length >= 2) {
    return (parts[0][0] + parts[1][0]).toUpperCase()
  }
  return name.substring(0, 2).toUpperCase()
})

const avatarSizeClasses = computed(() => {
  return 'h-9 w-9'
})

// Methods
function toggleDropdown() {
  isDropdownOpen.value = !isDropdownOpen.value
}

function closeDropdown() {
  isDropdownOpen.value = false
}

async function handleSignOut() {
  closeDropdown()
  try {
    await authStore.logout()
    router.push('/signin')
  } catch (error) {
    console.error('Sign out failed:', error)
  }
}

// Handle clicks outside the dropdown to close it
function handleClickOutside(event) {
  if (dropdownRef.value && !dropdownRef.value.contains(event.target)) {
    closeDropdown()
  }
}

// Handle escape key to close dropdown
function handleEscapeKey(event) {
  if (event.key === 'Escape') {
    closeDropdown()
  }
}

onMounted(() => {
  document.addEventListener('click', handleClickOutside)
  document.addEventListener('keydown', handleEscapeKey)
})

onUnmounted(() => {
  document.removeEventListener('click', handleClickOutside)
  document.removeEventListener('keydown', handleEscapeKey)
})
</script>
