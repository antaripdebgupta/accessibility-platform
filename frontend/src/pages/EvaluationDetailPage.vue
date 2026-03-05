<template>
  <AppLayout>
    <!-- Loading State -->
    <div
      v-if="evaluationsStore.loading"
      class="flex items-center justify-center py-24"
    >
      <LoadingSpinner size="lg" />
    </div>

    <!-- Error State -->
    <div v-else-if="error" class="mx-auto max-w-2xl py-16">
      <div class="rounded-lg border border-red-200 bg-red-50 p-6 text-center">
        <svg
          class="mx-auto h-12 w-12 text-red-400"
          fill="none"
          stroke="currentColor"
          viewBox="0 0 24 24"
          aria-hidden="true"
        >
          <path
            stroke-linecap="round"
            stroke-linejoin="round"
            stroke-width="2"
            d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z"
          />
        </svg>
        <h3 class="mt-4 text-lg font-medium text-red-800">
          {{ error }}
        </h3>
        <RouterLink
          to="/dashboard"
          class="mt-4 inline-flex items-center rounded-md bg-red-100 px-4 py-2 text-sm font-medium text-red-700 hover:bg-red-200 focus:outline-none focus:ring-2 focus:ring-red-500 focus:ring-offset-2"
        >
          Return to Dashboard
        </RouterLink>
      </div>
    </div>

    <!-- Evaluation Detail -->
    <template v-else-if="evaluation">
      <!-- Page Header -->
      <PageHeader
        :title="evaluation.title"
        :subtitle="evaluation.target_url"
        :back-to="{ name: 'Dashboard' }"
      >
        <StatusBadge :status="evaluation.status" />
        <button
          v-if="canDelete"
          type="button"
          class="ml-3 inline-flex items-center rounded-md border border-red-300 bg-white px-3 py-2 text-sm font-medium text-red-700 shadow-sm hover:bg-red-50 focus:outline-none focus:ring-2 focus:ring-red-500 focus:ring-offset-2"
          @click="handleDelete"
        >
          <svg
            class="-ml-0.5 mr-1.5 h-4 w-4"
            fill="none"
            stroke="currentColor"
            viewBox="0 0 24 24"
            aria-hidden="true"
          >
            <path
              stroke-linecap="round"
              stroke-linejoin="round"
              stroke-width="2"
              d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16"
            />
          </svg>
          Delete
        </button>
      </PageHeader>

      <!-- Step Indicator -->
      <div class="mb-8 rounded-lg border border-gray-200 bg-white p-6">
        <StepIndicator :current-status="evaluation.status" />
      </div>

      <!-- Project Details Card -->
      <div class="mb-8 rounded-lg border border-gray-200 bg-white p-6">
        <h2 class="mb-4 text-lg font-medium text-gray-900">Project Details</h2>
        <EvaluationMeta :evaluation="evaluation" />
      </div>

      <!-- Action Panel -->
      <div class="mb-8 rounded-lg border border-gray-200 bg-white p-6">
        <h2 class="mb-4 text-lg font-medium text-gray-900">Actions</h2>

        <!-- DRAFT status -->
        <div v-if="evaluation.status === 'DRAFT'" class="space-y-4">
          <p class="text-sm text-gray-600">
            Begin by crawling the target website to discover all pages.
          </p>
          <RouterLink
            :to="`/evaluations/${evaluation.id}/explore`"
            class="inline-flex items-center rounded-md px-6 py-3 text-sm font-semibold text-white shadow-sm hover:bg-indigo-200 focus:outline-none focus:ring-2 focus:ring-indigo-500 focus:ring-offset-2"
          >
            Configure & Start Exploration
          </RouterLink>
        </div>

        <!-- SCOPING status -->
        <div v-else-if="evaluation.status === 'SCOPING'" class="space-y-4">
          <p class="text-sm text-gray-600">
            Configure your evaluation scope and start exploration.
          </p>
          <RouterLink
            :to="`/evaluations/${evaluation.id}/explore`"
            class="inline-flex items-center rounded-md bg-indigo-600 px-6 py-3 text-sm font-semibold text-white shadow-sm hover:bg-indigo-500 focus:outline-none focus:ring-2 focus:ring-indigo-500 focus:ring-offset-2"
          >
            Configure & Start Exploration
          </RouterLink>
        </div>

        <!-- EXPLORING status -->
        <div v-else-if="evaluation.status === 'EXPLORING'" class="space-y-4">
          <div class="flex items-center space-x-2">
            <LoadingSpinner size="sm" />
            <span class="text-sm text-gray-600"
              >Exploration in progress...</span
            >
          </div>
          <RouterLink
            :to="`/evaluations/${evaluation.id}/explore`"
            class="inline-flex items-center rounded-md border border-gray-300 bg-white px-4 py-2 text-sm font-medium text-gray-700 shadow-sm hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-indigo-500 focus:ring-offset-2"
          >
            View Pages
          </RouterLink>
        </div>

        <!-- SAMPLING status -->
        <div v-else-if="evaluation.status === 'SAMPLING'" class="space-y-4">
          <p class="text-sm text-gray-600">
            Select pages for sampling and start the audit.
          </p>
          <div class="flex items-center space-x-3">
            <button
              type="button"
              class="inline-flex items-center rounded-md bg-indigo-600 px-4 py-2 text-sm font-semibold text-white shadow-sm hover:bg-indigo-500 focus:outline-none focus:ring-2 focus:ring-indigo-500 focus:ring-offset-2"
            >
              Start Audit
            </button>
            <RouterLink
              :to="`/evaluations/${evaluation.id}/explore`"
              class="text-sm text-indigo-600 hover:text-indigo-500"
            >
              View discovered pages
            </RouterLink>
          </div>
        </div>

        <!-- AUDITING status -->
        <div v-else-if="evaluation.status === 'AUDITING'" class="space-y-4">
          <div class="flex items-center space-x-2">
            <LoadingSpinner size="sm" />
            <span class="text-sm text-gray-600">Audit in progress...</span>
          </div>
          <RouterLink
            :to="`/evaluations/${evaluation.id}/findings`"
            class="inline-flex items-center rounded-md border border-gray-300 bg-white px-4 py-2 text-sm font-medium text-gray-700 shadow-sm hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-indigo-500 focus:ring-offset-2"
          >
            View Findings
          </RouterLink>
        </div>

        <!-- REPORTING status -->
        <div v-else-if="evaluation.status === 'REPORTING'" class="space-y-4">
          <div class="flex items-center space-x-2">
            <LoadingSpinner size="sm" />
            <span class="text-sm text-gray-600">Generating report...</span>
          </div>
        </div>

        <!-- COMPLETE status -->
        <div v-else-if="evaluation.status === 'COMPLETE'" class="space-y-4">
          <p class="text-sm text-gray-600">
            Your accessibility evaluation is complete.
          </p>
          <div class="flex items-center space-x-3">
            <RouterLink
              :to="`/evaluations/${evaluation.id}/reports`"
              class="inline-flex items-center rounded-md bg-green-600 px-4 py-2 text-sm font-semibold text-white shadow-sm hover:bg-green-500 focus:outline-none focus:ring-2 focus:ring-green-500 focus:ring-offset-2"
            >
              View Report
            </RouterLink>
            <RouterLink
              :to="`/evaluations/${evaluation.id}/findings`"
              class="inline-flex items-center rounded-md border border-gray-300 bg-white px-4 py-2 text-sm font-medium text-gray-700 shadow-sm hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-indigo-500 focus:ring-offset-2"
            >
              View Findings
            </RouterLink>
          </div>
        </div>
      </div>

      <!-- Stats Row (only for AUDITING or COMPLETE) -->
      <div v-if="showStats" class="grid grid-cols-1 gap-4 sm:grid-cols-3">
        <div class="rounded-lg border border-gray-200 bg-white p-6">
          <dt class="text-sm font-medium text-gray-500">Pages Scanned</dt>
          <dd class="mt-1 text-3xl font-semibold text-gray-400">0</dd>
        </div>
        <div class="rounded-lg border border-gray-200 bg-white p-6">
          <dt class="text-sm font-medium text-gray-500">Issues Found</dt>
          <dd class="mt-1 text-3xl font-semibold text-gray-400">0</dd>
        </div>
        <div class="rounded-lg border border-gray-200 bg-white p-6">
          <dt class="text-sm font-medium text-gray-500">Criteria Affected</dt>
          <dd class="mt-1 text-3xl font-semibold text-gray-400">0</dd>
        </div>
      </div>
    </template>
  </AppLayout>
</template>

<script setup>
import { computed, onMounted, ref } from 'vue'
import { RouterLink, useRoute, useRouter } from 'vue-router'

import LoadingSpinner from '../components/common/LoadingSpinner.vue'
import StatusBadge from '../components/common/StatusBadge.vue'
import EvaluationMeta from '../components/evaluation/EvaluationMeta.vue'
import StepIndicator from '../components/evaluation/StepIndicator.vue'
import AppLayout from '../components/layout/AppLayout.vue'
import PageHeader from '../components/layout/PageHeader.vue'
import { useAuthStore } from '../stores/auth'
import { useEvaluationsStore } from '../stores/evaluations'

const route = useRoute()
const router = useRouter()
const authStore = useAuthStore()
const evaluationsStore = useEvaluationsStore()

const error = ref('')

// Computed properties
const evaluation = computed(() => evaluationsStore.current)

const showStats = computed(() => {
  const status = evaluation.value?.status?.toUpperCase()
  return status === 'AUDITING' || status === 'COMPLETE'
})

const canDelete = computed(() => {
  // For now, allow deletion for all users with access
  // In a real app, you'd check if user is owner
  return evaluation.value && evaluation.value.status !== 'DELETED'
})

// Methods
async function handleDelete() {
  const confirmed = window.confirm('Are you sure? This cannot be undone.')

  if (!confirmed) return

  try {
    await evaluationsStore.deleteOne(evaluation.value.id)
    router.push('/dashboard')
  } catch (err) {
    error.value = err.message || 'Failed to delete evaluation'
  }
}

// Lifecycle
onMounted(async () => {
  const id = route.params.id

  if (!id) {
    error.value = 'Evaluation ID is required'
    return
  }

  try {
    await evaluationsStore.fetchOne(id)
  } catch (err) {
    error.value = err.message || 'Failed to load evaluation'
  }
})
</script>
