<template>
  <div class="min-h-screen bg-gray-100">
    <!-- Navigation -->
    <nav class="bg-white shadow">
      <div class="mx-auto max-w-7xl px-4 sm:px-6 lg:px-8">
        <div class="flex h-16 justify-between">
          <div class="flex items-center">
            <h1 class="text-xl font-bold text-gray-900">
              Accessibility Platform
            </h1>
          </div>
          <div class="flex items-center space-x-4">
            <span class="text-sm text-gray-600">
              {{ authStore.userEmail }}
            </span>
            <button
              @click="handleLogout"
              class="rounded-md bg-gray-100 px-3 py-2 text-sm font-medium text-gray-700 hover:bg-gray-200"
            >
              Sign out
            </button>
          </div>
        </div>
      </div>
    </nav>

    <!-- Main Content -->
    <main class="py-10">
      <div class="mx-auto max-w-7xl px-4 sm:px-6 lg:px-8">
        <!-- Welcome Card -->
        <div class="overflow-hidden rounded-lg bg-white shadow">
          <div class="px-4 py-5 sm:p-6">
            <h2 class="text-lg font-medium text-gray-900">
              Welcome to the Dashboard
            </h2>
            <p class="mt-2 text-sm text-gray-500">
              You have successfully logged in. This is a placeholder dashboard
              page that will be built out in future development phases.
            </p>

            <!-- Health Check Status -->
            <div class="mt-6">
              <h3 class="text-sm font-medium text-gray-700">API Status</h3>
              <div class="mt-2 flex items-center space-x-2">
                <span
                  :class="[
                    'inline-flex h-3 w-3 rounded-full',
                    healthStatus === 'ok' ? 'bg-green-500' : 'bg-red-500',
                  ]"
                ></span>
                <span class="text-sm text-gray-600">
                  {{
                    healthStatus === 'ok'
                      ? 'API is healthy'
                      : healthStatus === 'loading'
                        ? 'Checking...'
                        : 'API unavailable'
                  }}
                </span>
              </div>
            </div>

            <!-- Quick Actions -->
            <div class="mt-8">
              <h3 class="text-sm font-medium text-gray-700">Coming Soon</h3>
              <div class="mt-3 grid grid-cols-1 gap-4 sm:grid-cols-3">
                <div
                  class="rounded-lg border border-gray-200 bg-gray-50 p-4 text-center"
                >
                  <div
                    class="mx-auto flex h-12 w-12 items-center justify-center rounded-full bg-indigo-100"
                  >
                    <svg
                      class="h-6 w-6 text-indigo-600"
                      fill="none"
                      stroke="currentColor"
                      viewBox="0 0 24 24"
                    >
                      <path
                        stroke-linecap="round"
                        stroke-linejoin="round"
                        stroke-width="2"
                        d="M9 5H7a2 2 0 00-2 2v12a2 2 0 002 2h10a2 2 0 002-2V7a2 2 0 00-2-2h-2M9 5a2 2 0 002 2h2a2 2 0 002-2M9 5a2 2 0 012-2h2a2 2 0 012 2"
                      />
                    </svg>
                  </div>
                  <h4 class="mt-2 text-sm font-medium text-gray-900">
                    New Evaluation
                  </h4>
                  <p class="mt-1 text-xs text-gray-500">
                    Start a WCAG accessibility audit
                  </p>
                </div>

                <div
                  class="rounded-lg border border-gray-200 bg-gray-50 p-4 text-center"
                >
                  <div
                    class="mx-auto flex h-12 w-12 items-center justify-center rounded-full bg-green-100"
                  >
                    <svg
                      class="h-6 w-6 text-green-600"
                      fill="none"
                      stroke="currentColor"
                      viewBox="0 0 24 24"
                    >
                      <path
                        stroke-linecap="round"
                        stroke-linejoin="round"
                        stroke-width="2"
                        d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z"
                      />
                    </svg>
                  </div>
                  <h4 class="mt-2 text-sm font-medium text-gray-900">
                    View Reports
                  </h4>
                  <p class="mt-1 text-xs text-gray-500">
                    Browse past evaluations
                  </p>
                </div>

                <div
                  class="rounded-lg border border-gray-200 bg-gray-50 p-4 text-center"
                >
                  <div
                    class="mx-auto flex h-12 w-12 items-center justify-center rounded-full bg-purple-100"
                  >
                    <svg
                      class="h-6 w-6 text-purple-600"
                      fill="none"
                      stroke="currentColor"
                      viewBox="0 0 24 24"
                    >
                      <path
                        stroke-linecap="round"
                        stroke-linejoin="round"
                        stroke-width="2"
                        d="M10.325 4.317c.426-1.756 2.924-1.756 3.35 0a1.724 1.724 0 002.573 1.066c1.543-.94 3.31.826 2.37 2.37a1.724 1.724 0 001.065 2.572c1.756.426 1.756 2.924 0 3.35a1.724 1.724 0 00-1.066 2.573c.94 1.543-.826 3.31-2.37 2.37a1.724 1.724 0 00-2.572 1.065c-.426 1.756-2.924 1.756-3.35 0a1.724 1.724 0 00-2.573-1.066c-1.543.94-3.31-.826-2.37-2.37a1.724 1.724 0 00-1.065-2.572c-1.756-.426-1.756-2.924 0-3.35a1.724 1.724 0 001.066-2.573c-.94-1.543.826-3.31 2.37-2.37.996.608 2.296.07 2.572-1.065z"
                      />
                      <path
                        stroke-linecap="round"
                        stroke-linejoin="round"
                        stroke-width="2"
                        d="M15 12a3 3 0 11-6 0 3 3 0 016 0z"
                      />
                    </svg>
                  </div>
                  <h4 class="mt-2 text-sm font-medium text-gray-900">
                    Settings
                  </h4>
                  <p class="mt-1 text-xs text-gray-500">
                    Configure your account
                  </p>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </main>
  </div>
</template>

<script setup>
import { onMounted, ref } from 'vue'
import { useRouter } from 'vue-router'

import { apiClient } from '../lib/api'
import { useAuthStore } from '../stores/auth'

const router = useRouter()
const authStore = useAuthStore()
const healthStatus = ref('loading')

onMounted(async () => {
  // Check API health on mount
  try {
    const response = await apiClient.health()
    healthStatus.value = response.data?.status || 'ok'
  } catch (error) {
    console.error('Health check failed:', error)
    healthStatus.value = 'error'
  }
})

async function handleLogout() {
  await authStore.logout()
  router.push('/signin')
}
</script>
