<template>
  <div class="fixed inset-0 z-50 overflow-y-auto" v-if="show">
    <!-- Backdrop -->
    <div
      class="fixed inset-0 bg-black/50 transition-opacity"
      @click="$emit('close')"
    ></div>

    <!-- Modal Panel -->
    <div class="flex min-h-full items-center justify-center p-4">
      <div
        class="relative w-full max-w-2xl transform rounded-xl bg-white shadow-2xl transition-all"
        @click.stop
      >
        <!-- Header -->
        <div class="border-b border-gray-200 px-6 py-4">
          <div class="flex items-center justify-between">
            <div>
              <h2 class="text-lg font-semibold text-gray-900">
                Select User Perspective
              </h2>
              <p class="mt-1 text-sm text-gray-500">
                View findings from the perspective of users with specific
                disabilities
              </p>
            </div>
            <button
              type="button"
              class="rounded-lg p-2 text-gray-400 hover:bg-gray-100 hover:text-gray-500"
              @click="$emit('close')"
            >
              <svg
                class="h-5 w-5"
                fill="none"
                stroke="currentColor"
                viewBox="0 0 24 24"
              >
                <path
                  stroke-linecap="round"
                  stroke-linejoin="round"
                  stroke-width="2"
                  d="M6 18L18 6M6 6l12 12"
                />
              </svg>
            </button>
          </div>
        </div>

        <!-- Profile Cards Grid -->
        <div class="p-6">
          <div class="grid grid-cols-1 gap-4 sm:grid-cols-2">
            <!-- Profile Cards -->
            <button
              v-for="profile in profilesStore.profiles"
              :key="profile.id"
              type="button"
              class="relative flex flex-col items-center rounded-xl border-2 p-6 text-center transition-all focus:outline-none focus:ring-2 focus:ring-offset-2"
              :class="getCardClasses(profile.id)"
              @click="selectProfile(profile.id)"
            >
              <!-- Active Badge -->
              <div
                v-if="isActive(profile.id)"
                class="absolute right-3 top-3 flex items-center space-x-1 rounded-full bg-white px-2 py-1 text-xs font-medium shadow-sm"
                :class="getActiveBadgeClass(profile.id)"
              >
                <svg class="h-3 w-3" fill="currentColor" viewBox="0 0 20 20">
                  <path
                    fill-rule="evenodd"
                    d="M16.707 5.293a1 1 0 010 1.414l-8 8a1 1 0 01-1.414 0l-4-4a1 1 0 011.414-1.414L8 12.586l7.293-7.293a1 1 0 011.414 0z"
                    clip-rule="evenodd"
                  />
                </svg>
                <span>Active</span>
              </div>

              <!-- Name -->
              <h3 class="mt-3 text-base font-semibold text-gray-900">
                {{ profile.name }}
              </h3>

              <!-- Description -->
              <p class="mt-2 text-sm text-gray-500">
                {{ profile.description }}
              </p>
            </button>

            <!-- No Profile Option -->
            <button
              type="button"
              class="relative flex flex-col items-center rounded-xl border-2 p-6 text-center transition-all focus:outline-none focus:ring-2 focus:ring-gray-500 focus:ring-offset-2"
              :class="
                noProfileActive
                  ? 'border-gray-400 bg-gray-50'
                  : 'border-gray-200 hover:border-gray-300 bg-white'
              "
              @click="clearProfile"
            >
              <!-- Active Badge -->
              <div
                v-if="noProfileActive"
                class="absolute right-3 top-3 flex items-center space-x-1 rounded-full bg-white px-2 py-1 text-xs font-medium text-gray-600 shadow-sm"
              >
                <svg class="h-3 w-3" fill="currentColor" viewBox="0 0 20 20">
                  <path
                    fill-rule="evenodd"
                    d="M16.707 5.293a1 1 0 010 1.414l-8 8a1 1 0 01-1.414 0l-4-4a1 1 0 011.414-1.414L8 12.586l7.293-7.293a1 1 0 011.414 0z"
                    clip-rule="evenodd"
                  />
                </svg>
                <span>Active</span>
              </div>

              <!-- Icon -->
              <div
                class="flex h-10 w-10 items-center justify-center rounded-full bg-gray-100"
              >
                <svg
                  class="h-6 w-6 text-gray-400"
                  fill="none"
                  stroke="currentColor"
                  viewBox="0 0 24 24"
                >
                  <path
                    stroke-linecap="round"
                    stroke-linejoin="round"
                    stroke-width="2"
                    d="M17 20h5v-2a3 3 0 00-5.356-1.857M17 20H7m10 0v-2c0-.656-.126-1.283-.356-1.857M7 20H2v-2a3 3 0 015.356-1.857M7 20v-2c0-.656.126-1.283.356-1.857m0 0a5.002 5.002 0 019.288 0M15 7a3 3 0 11-6 0 3 3 0 016 0z"
                  />
                </svg>
              </div>

              <!-- Name -->
              <h3 class="mt-3 text-base font-semibold text-gray-900">
                No Profile (All Users)
              </h3>

              <!-- Description -->
              <p class="mt-2 text-sm text-gray-500">
                View findings with standard severity without any profile-based
                adjustments
              </p>
            </button>
          </div>
        </div>

        <!-- Footer Info -->
        <div class="border-t border-gray-200 bg-gray-50 px-6 py-4 rounded-b-xl">
          <p class="text-xs text-gray-500">
            <strong>Tip:</strong> Selecting a profile re-prioritizes findings
            based on which WCAG criteria most impact that user group. Severity
            may be boosted for critical barriers.
          </p>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { computed, onMounted } from 'vue'
import { useProfilesStore } from '../../stores/profiles'

const props = defineProps({
  show: {
    type: Boolean,
    default: false,
  },
})

const emit = defineEmits(['close', 'changed'])

const profilesStore = useProfilesStore()

const noProfileActive = computed(() => !profilesStore.hasActiveProfile)

function isActive(profileId) {
  return profilesStore.activeProfile === profileId
}

function getCardClasses(profileId) {
  const isActiveProfile = isActive(profileId)
  const baseClasses = 'cursor-pointer'

  const colorMap = {
    blind: isActiveProfile
      ? 'border-blue-600 bg-blue-50 ring-blue-500'
      : 'border-gray-200 bg-white hover:border-blue-300',
    low_vision: isActiveProfile
      ? 'border-amber-500 bg-amber-50 ring-amber-500'
      : 'border-gray-200 bg-white hover:border-amber-300',
    motor: isActiveProfile
      ? 'border-green-600 bg-green-50 ring-green-500'
      : 'border-gray-200 bg-white hover:border-green-300',
    cognitive: isActiveProfile
      ? 'border-purple-600 bg-purple-50 ring-purple-500'
      : 'border-gray-200 bg-white hover:border-purple-300',
  }

  return `${baseClasses} ${colorMap[profileId] || 'border-gray-200'}`
}

function getActiveBadgeClass(profileId) {
  const colorMap = {
    blind: 'text-blue-700',
    low_vision: 'text-amber-700',
    motor: 'text-green-700',
    cognitive: 'text-purple-700',
  }
  return colorMap[profileId] || 'text-gray-700'
}

function selectProfile(profileId) {
  profilesStore.setActiveProfile(profileId)
  emit('changed', profileId)
  emit('close')
}

function clearProfile() {
  profilesStore.clearProfile()
  emit('changed', null)
  emit('close')
}

onMounted(async () => {
  if (profilesStore.profiles.length === 0) {
    try {
      await profilesStore.fetchProfiles()
    } catch (err) {
      console.error('Failed to load profiles:', err)
    }
  }
})
</script>
