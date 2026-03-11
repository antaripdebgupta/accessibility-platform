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

      <!-- Compact Verdict Banner (shown when COMPLETE) -->
      <div v-if="showVerdictBanner" class="mb-8">
        <VerdictBanner
          :verdict="latestReport.conformance_verdict || 'CANNOT_DETERMINE'"
          :criteria-failed="latestReport.criteria_failed || 0"
          :criteria-total="
            (latestReport.criteria_passed || 0) +
            (latestReport.criteria_failed || 0)
          "
          :compact="true"
        />
      </div>

      <!-- Stats Section (always shown) -->
      <div class="mb-8 grid grid-cols-1 gap-4 sm:grid-cols-4">
        <div class="rounded-lg border border-gray-200 bg-white p-6">
          <dt class="text-sm font-medium text-gray-500">Pages Discovered</dt>
          <dd class="mt-1 text-3xl font-semibold text-gray-900">
            {{ stats.pagesDiscovered }}
          </dd>
        </div>
        <div class="rounded-lg border border-gray-200 bg-white p-6">
          <dt class="text-sm font-medium text-gray-500">Issues Found</dt>
          <dd class="mt-1 text-3xl font-semibold text-gray-900">
            {{ stats.issuesFound }}
          </dd>
        </div>
        <div class="rounded-lg border border-gray-200 bg-white p-6">
          <dt class="text-sm font-medium text-gray-500">Critical</dt>
          <dd class="mt-1 text-3xl font-semibold text-red-600">
            {{ stats.critical }}
          </dd>
        </div>
        <div class="rounded-lg border border-gray-200 bg-white p-6">
          <dt class="text-sm font-medium text-gray-500">Confirmed</dt>
          <dd class="mt-1 text-3xl font-semibold text-orange-600">
            {{ stats.confirmed }}
          </dd>
        </div>
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
            class="inline-flex items-center rounded-md px-6 py-3 text-sm font-semibold text-white shadow-sm hover:bg-indigo-200 focus:outline-none focus:ring-2 focus:ring-indigo-500 focus:ring-offset-2"
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
          <p class="text-xs text-gray-500">
            Status updates automatically every 10 seconds.
          </p>
          <RouterLink
            :to="`/evaluations/${evaluation.id}/findings`"
            class="inline-flex items-center rounded-md border border-gray-300 bg-white px-4 py-2 text-sm font-medium text-gray-700 shadow-sm hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-indigo-500 focus:ring-offset-2"
          >
            View Findings
          </RouterLink>
        </div>

        <!-- REPORTING status -->
        <div v-else-if="evaluation.status === 'REPORTING'" class="space-y-4">
          <div class="flex items-center space-x-3">
            <div class="flex items-center space-x-2">
              <LoadingSpinner size="sm" />
              <span class="text-sm text-gray-600">Generating report...</span>
            </div>
            <RouterLink
              :to="`/evaluations/${evaluation.id}/reports`"
              class="inline-flex items-center rounded-md border border-gray-300 bg-white px-3 py-1.5 text-sm font-medium text-gray-700 shadow-sm hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-indigo-500 focus:ring-offset-2"
            >
              Go to Reports Page →
            </RouterLink>
          </div>
          <div class="rounded-md bg-green-50 p-4">
            <div class="flex">
              <div class="shrink-0">
                <svg
                  class="h-5 w-5 text-green-400"
                  fill="currentColor"
                  viewBox="0 0 20 20"
                >
                  <path
                    fill-rule="evenodd"
                    d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z"
                    clip-rule="evenodd"
                  />
                </svg>
              </div>
              <div class="ml-3">
                <p class="text-sm font-medium text-green-800">
                  ✓ Audit complete — view your findings
                </p>
              </div>
            </div>
          </div>
          <RouterLink
            :to="`/evaluations/${evaluation.id}/findings`"
            class="inline-flex items-center rounded-md px-4 py-2 text-sm font-semibold text-white shadow-sm hover:bg-indigo-200 focus:outline-none focus:ring-2 focus:ring-indigo-500 focus:ring-offset-2"
          >
            View Findings →
          </RouterLink>
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

      <!-- Activity Log Section (collapsible) -->
      <div class="mb-8 rounded-lg border border-gray-200 bg-white">
        <button
          type="button"
          class="flex w-full items-center justify-between p-6 text-left"
          @click="activityLogExpanded = !activityLogExpanded"
        >
          <h2 class="text-lg font-medium text-gray-900">Activity Log</h2>
          <svg
            class="h-5 w-5 text-gray-500 transition-transform duration-200"
            :class="{ 'rotate-180': activityLogExpanded }"
            fill="none"
            stroke="currentColor"
            viewBox="0 0 24 24"
          >
            <path
              stroke-linecap="round"
              stroke-linejoin="round"
              stroke-width="2"
              d="M19 9l-7 7-7-7"
            />
          </svg>
        </button>
        <div v-if="activityLogExpanded" class="border-t border-gray-200 p-6">
          <AuditLog :evaluation-id="evaluation.id" />
        </div>
      </div>
    </template>
  </AppLayout>
</template>

<script setup>
import { computed, onMounted, onUnmounted, reactive, ref } from 'vue'
import { RouterLink, useRoute, useRouter } from 'vue-router'

import LoadingSpinner from '../components/common/LoadingSpinner.vue'
import StatusBadge from '../components/common/StatusBadge.vue'
import AuditLog from '../components/evaluation/AuditLog.vue'
import EvaluationMeta from '../components/evaluation/EvaluationMeta.vue'
import StepIndicator from '../components/evaluation/StepIndicator.vue'
import AppLayout from '../components/layout/AppLayout.vue'
import PageHeader from '../components/layout/PageHeader.vue'
import VerdictBanner from '../components/reports/VerdictBanner.vue'
import api from '../lib/api'
import { useAuthStore } from '../stores/auth'
import { useEvaluationsStore } from '../stores/evaluations'
import { useFindingsStore } from '../stores/findings'
import { useReportsStore } from '../stores/reports'

const route = useRoute()
const router = useRouter()
const authStore = useAuthStore()
const evaluationsStore = useEvaluationsStore()
const findingsStore = useFindingsStore()
const reportsStore = useReportsStore()

const error = ref('')
const activityLogExpanded = ref(false)
const pollingInterval = ref(null)

// Stats
const stats = reactive({
  pagesDiscovered: 0,
  issuesFound: 0,
  critical: 0,
  confirmed: 0,
})

// Computed properties
const evaluation = computed(() => evaluationsStore.current)

const canDelete = computed(() => {
  return evaluation.value && evaluation.value.status !== 'DELETED'
})

const latestReport = computed(() => {
  return reportsStore.latestFullReport || reportsStore.reports[0] || null
})

const showVerdictBanner = computed(() => {
  return (
    evaluation.value &&
    evaluation.value.status === 'COMPLETE' &&
    latestReport.value
  )
})

// Methods
async function fetchStats() {
  if (!evaluation.value) return

  const evaluationId = evaluation.value.id

  // Fetch findings summary
  try {
    await findingsStore.fetchSummary(evaluationId)
    stats.issuesFound = findingsStore.summary.total || 0
    stats.critical = findingsStore.summary.critical || 0
  } catch (err) {
    console.error('Failed to fetch findings summary:', err)
  }

  // Fetch pages summary
  try {
    const response = await api.get(`/evaluations/${evaluationId}/pages/summary`)
    stats.pagesDiscovered = response.data.total_pages || 0
  } catch (err) {
    console.error('Failed to fetch pages summary:', err)
  }

  // Fetch confirmed count
  try {
    const response = await api.get(
      `/evaluations/${evaluationId}/findings?status=CONFIRMED&limit=1`,
    )
    stats.confirmed = response.data.total || 0
  } catch (err) {
    console.error('Failed to fetch confirmed count:', err)
  }
}

async function fetchLatestReport() {
  if (!evaluation.value) return
  if (evaluation.value.status !== 'COMPLETE') return

  try {
    await reportsStore.fetchLatest(evaluation.value.id)
  } catch (err) {
    console.error('Failed to fetch latest report:', err)
  }
}

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

// Status polling for in-progress evaluations
function shouldPoll() {
  const status = evaluation.value?.status?.toUpperCase()
  return (
    status === 'AUDITING' || status === 'REPORTING' || status === 'EXPLORING'
  )
}

function startPolling() {
  if (pollingInterval.value) return
  if (!shouldPoll()) return

  pollingInterval.value = setInterval(async () => {
    if (!evaluation.value) {
      stopPolling()
      return
    }

    try {
      const previousStatus = evaluation.value.status
      const updatedEvaluation = await evaluationsStore.fetchOne(
        evaluation.value.id,
      )

      // Update only if status has changed
      if (updatedEvaluation.status !== previousStatus) {
        evaluation.value.status = updatedEvaluation.status
      }

      await fetchStats()

      // Check if status changed and polling should stop
      if (!shouldPoll()) {
        stopPolling()
        // Fetch latest report if now complete
        if (evaluation.value.status === 'COMPLETE') {
          await fetchLatestReport()
        }
      }
    } catch (err) {
      // Silent fail on polling errors
    }
  }, 10000) // Poll every 10 seconds
}

function stopPolling() {
  if (pollingInterval.value) {
    clearInterval(pollingInterval.value)
    pollingInterval.value = null
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
    await fetchStats()
    await fetchLatestReport()

    // Start polling if evaluation is in progress
    if (shouldPoll()) {
      startPolling()
    }
  } catch (err) {
    error.value = err.message || 'Failed to load evaluation'
  }
})

onUnmounted(() => {
  stopPolling()
  reportsStore.clearReports()
})
</script>

<style scoped>
.rotate-180 {
  transform: rotate(180deg);
}
</style>
