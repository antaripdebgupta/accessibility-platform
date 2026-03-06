<template>
  <AppLayout>
    <!-- Loading State -->
    <div
      v-if="loading && !evaluation"
      class="flex items-center justify-center py-24"
    >
      <LoadingSpinner size="lg" />
    </div>

    <!-- Error State -->
    <div v-else-if="error && !evaluation" class="mx-auto max-w-2xl py-16">
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
        <h3 class="mt-4 text-lg font-medium text-red-800">{{ error }}</h3>
        <RouterLink
          to="/dashboard"
          class="mt-4 inline-flex items-center rounded-md bg-red-100 px-4 py-2 text-sm font-medium text-red-700 hover:bg-red-200 focus:outline-none focus:ring-2 focus:ring-red-500 focus:ring-offset-2"
        >
          Return to Dashboard
        </RouterLink>
      </div>
    </div>

    <!-- Main Content -->
    <template v-else-if="evaluation">
      <PageHeader
        title="Findings Review"
        :subtitle="`${evaluation.target_url} - Review and manage accessibility issues`"
        :back-to="{ name: 'EvaluationDetail', params: { id: evaluationId } }"
      >
        <div class="flex items-center space-x-3">
          <button
            type="button"
            class="inline-flex items-center rounded-md border border-gray-300 bg-white px-3 py-2 text-sm font-semibold text-gray-700 shadow-sm hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-indigo-500 focus:ring-offset-2"
            @click="showManualModal = true"
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
                d="M12 4v16m8-8H4"
              />
            </svg>
            Add Manual Finding
          </button>
          <button
            type="button"
            class="inline-flex items-center rounded-md bg-green-600 px-3 py-2 text-sm font-semibold text-white shadow-sm hover:bg-green-500 focus:outline-none focus:ring-2 focus:ring-green-500 focus:ring-offset-2 disabled:cursor-not-allowed disabled:opacity-50"
            :disabled="generatingReport"
            @click="handleGenerateReport"
          >
            <svg
              v-if="generatingReport"
              class="-ml-0.5 mr-1.5 h-4 w-4 animate-spin"
              fill="none"
              viewBox="0 0 24 24"
              aria-hidden="true"
            >
              <circle
                class="opacity-25"
                cx="12"
                cy="12"
                r="10"
                stroke="currentColor"
                stroke-width="4"
              ></circle>
              <path
                class="opacity-75"
                fill="currentColor"
                d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"
              ></path>
            </svg>
            <svg
              v-else
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
                d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z"
              />
            </svg>
            {{ generatingReport ? 'Generating...' : 'Generate Report' }}
          </button>
        </div>
      </PageHeader>

      <!-- Summary Cards -->
      <FindingsSummary
        :summary="findingsStore.summary"
        :active-severity="findingsStore.filters.severity"
        class="mb-6"
        @filter="handleSeverityFilter"
      />

      <!-- Filters -->
      <FindingFilters
        :model-value="findingsStore.filters"
        class="mb-6"
        @update:model-value="handleFiltersUpdate"
      />

      <!-- Findings Table -->
      <FindingsTable
        :findings="findingsStore.findings"
        :loading="findingsStore.loadingFindings"
        @select="openDetail"
        @confirm="handleConfirm"
        @dismiss="handleDismiss"
      />

      <!-- Pagination -->
      <div
        v-if="findingsStore.total > findingsStore.pagination.limit"
        class="mt-4 flex items-center justify-between rounded-lg border border-gray-200 bg-white px-6 py-3"
      >
        <div class="text-sm text-gray-700">
          Showing
          <span class="font-medium">{{
            findingsStore.pagination.skip + 1
          }}</span>
          to
          <span class="font-medium">
            {{
              Math.min(
                findingsStore.pagination.skip + findingsStore.pagination.limit,
                findingsStore.total,
              )
            }}
          </span>
          of
          <span class="font-medium">{{ findingsStore.total }}</span>
          findings
        </div>
        <div class="flex space-x-2">
          <button
            type="button"
            :disabled="findingsStore.pagination.skip === 0"
            class="rounded-md border border-gray-300 bg-white px-3 py-2 text-sm font-medium text-gray-700 shadow-sm hover:bg-gray-50 disabled:cursor-not-allowed disabled:opacity-50"
            @click="prevPage"
          >
            Previous
          </button>
          <button
            type="button"
            :disabled="
              findingsStore.pagination.skip + findingsStore.pagination.limit >=
              findingsStore.total
            "
            class="rounded-md border border-gray-300 bg-white px-3 py-2 text-sm font-medium text-gray-700 shadow-sm hover:bg-gray-50 disabled:cursor-not-allowed disabled:opacity-50"
            @click="nextPage"
          >
            Next
          </button>
        </div>
      </div>
    </template>

    <!-- Finding Detail Panel -->
    <FindingDetailPanel
      :finding="selectedFinding"
      :show="!!selectedFinding"
      @close="selectedFinding = null"
      @confirm="handleConfirm"
      @dismiss="handleDismiss"
    />

    <!-- Manual Finding Modal -->
    <ManualFindingModal
      :show="showManualModal"
      :pages="pages"
      :criteria="criteria"
      @close="showManualModal = false"
      @submit="handleCreateManualFinding"
    />

    <!-- Error Toast -->
    <div class="fixed bottom-4 right-4 z-50">
      <ErrorToast
        :show="showError"
        :title="errorTitle"
        :message="errorMessage"
        @close="showError = false"
      />
    </div>
  </AppLayout>
</template>

<script setup>
import { computed, onMounted, ref } from 'vue'
import { RouterLink, useRoute, useRouter } from 'vue-router'

import ErrorToast from '../components/common/ErrorToast.vue'
import LoadingSpinner from '../components/common/LoadingSpinner.vue'
import FindingDetailPanel from '../components/findings/FindingDetailPanel.vue'
import FindingFilters from '../components/findings/FindingFilters.vue'
import FindingsSummary from '../components/findings/FindingsSummary.vue'
import FindingsTable from '../components/findings/FindingsTable.vue'
import ManualFindingModal from '../components/findings/ManualFindingModal.vue'
import AppLayout from '../components/layout/AppLayout.vue'
import PageHeader from '../components/layout/PageHeader.vue'
import api from '../lib/api'
import { useEvaluationsStore } from '../stores/evaluations'
import { useFindingsStore } from '../stores/findings'

const route = useRoute()
const router = useRouter()
const evaluationsStore = useEvaluationsStore()
const findingsStore = useFindingsStore()

// Reactive state
const loading = ref(true)
const error = ref('')
const selectedFinding = ref(null)
const showManualModal = ref(false)
const pages = ref([])
const criteria = ref([])
const generatingReport = ref(false)

// Error toast state
const showError = ref(false)
const errorTitle = ref('Error')
const errorMessage = ref('')

// Computed
const evaluationId = computed(() => route.params.id)
const evaluation = computed(() => evaluationsStore.current)

// Methods
function showErrorToast(title, message) {
  errorTitle.value = title
  errorMessage.value = message
  showError.value = true
}

function handleSeverityFilter(severity) {
  findingsStore.setFilter(
    'severity',
    severity === findingsStore.filters.severity ? '' : severity,
  )
}

function handleFiltersUpdate(newFilters) {
  // Update filters individually to trigger reactivity
  Object.keys(newFilters).forEach((key) => {
    findingsStore.filters[key] = newFilters[key]
  })
  // Reset pagination and reload
  findingsStore.pagination.skip = 0
  loadFindings()
}

function openDetail(finding) {
  selectedFinding.value = finding
}

function nextPage() {
  if (
    findingsStore.pagination.skip + findingsStore.pagination.limit <
    findingsStore.total
  ) {
    findingsStore.pagination.skip += findingsStore.pagination.limit
    loadFindings()
  }
}

function prevPage() {
  if (findingsStore.pagination.skip > 0) {
    findingsStore.pagination.skip = Math.max(
      0,
      findingsStore.pagination.skip - findingsStore.pagination.limit,
    )
    loadFindings()
  }
}

async function loadFindings() {
  try {
    await findingsStore.fetchFindings(evaluationId.value)
  } catch (err) {
    showErrorToast('Failed to load findings', err.message)
  }
}

async function handleConfirm(findingOrId) {
  // Support both finding object and finding ID
  const findingId =
    typeof findingOrId === 'string' ? findingOrId : findingOrId?.id
  if (!findingId) {
    showErrorToast('Failed to confirm finding', 'Invalid finding ID')
    return
  }

  try {
    await findingsStore.updateFinding(findingId, {
      status: 'CONFIRMED',
    })
    // Update local state if detail panel is open
    if (selectedFinding.value?.id === findingId) {
      selectedFinding.value = { ...selectedFinding.value, status: 'CONFIRMED' }
    }
    // Refresh summary
    await findingsStore.fetchSummary(evaluationId.value)
  } catch (err) {
    showErrorToast('Failed to confirm finding', err.message || 'Unknown error')
  }
}

async function handleDismiss(findingOrId) {
  // Support both finding object and finding ID
  const findingId =
    typeof findingOrId === 'string' ? findingOrId : findingOrId?.id
  if (!findingId) {
    showErrorToast('Failed to dismiss finding', 'Invalid finding ID')
    return
  }

  try {
    await findingsStore.updateFinding(findingId, {
      status: 'DISMISSED',
    })
    // Update local state if detail panel is open
    if (selectedFinding.value?.id === findingId) {
      selectedFinding.value = { ...selectedFinding.value, status: 'DISMISSED' }
    }
    // Refresh summary
    await findingsStore.fetchSummary(evaluationId.value)
  } catch (err) {
    showErrorToast('Failed to dismiss finding', err.message || 'Unknown error')
  }
}

async function handleCreateManualFinding(formData) {
  try {
    await findingsStore.createManual(evaluationId.value, formData)
    showManualModal.value = false
    // Refresh findings and summary
    await Promise.all([
      findingsStore.fetchFindings(evaluationId.value),
      findingsStore.fetchSummary(evaluationId.value),
    ])
  } catch (err) {
    showErrorToast('Failed to create finding', err.message)
  }
}

async function handleGenerateReport() {
  generatingReport.value = true
  try {
    const response = await api.post(
      `/evaluations/${evaluationId.value}/reports/generate`,
    )
    // Navigate to evaluation detail page to see progress
    router.push({
      name: 'EvaluationDetail',
      params: { id: evaluationId.value },
    })
  } catch (err) {
    showErrorToast(
      'Failed to generate report',
      err.response?.data?.detail || err.message || 'Unknown error',
    )
  } finally {
    generatingReport.value = false
  }
}

async function loadPages() {
  try {
    const response = await api.get(
      `/evaluations/${evaluationId.value}/pages?limit=200`,
    )
    pages.value = response.data.items
  } catch (err) {
    console.error('Failed to load pages:', err)
  }
}

async function loadCriteria() {
  try {
    const response = await api.get('/wcag/criteria')
    criteria.value = response.data
  } catch (err) {
    console.error('Failed to load WCAG criteria:', err)
  }
}

// Lifecycle
onMounted(async () => {
  loading.value = true

  try {
    // Fetch evaluation details
    await evaluationsStore.fetchOne(evaluationId.value)

    if (evaluation.value) {
      // Load findings, summary, pages, and criteria in parallel
      await Promise.all([
        findingsStore.fetchFindings(evaluationId.value),
        findingsStore.fetchSummary(evaluationId.value),
        loadPages(),
        loadCriteria(),
      ])
    }
  } catch (err) {
    error.value = err.message || 'Failed to load evaluation'
  } finally {
    loading.value = false
  }
})
</script>
