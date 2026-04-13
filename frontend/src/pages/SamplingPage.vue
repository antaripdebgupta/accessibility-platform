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

    <!-- Main Content -->
    <template v-else-if="evaluation">
      <PageHeader
        title="Sample Selection"
        :subtitle="evaluation.target_url"
        :back-to="{ name: 'Exploration', params: { id: evaluationId } }"
      >
        <StatusBadge :status="evaluation.status" />
      </PageHeader>

      <!-- Sample Configuration Panel -->
      <div class="mb-6 rounded-lg border border-gray-200 bg-white p-6">
        <div class="flex items-start justify-between">
          <div>
            <h2 class="text-lg font-medium text-gray-900">
              WCAG-EM Sample Configuration
            </h2>
            <p class="mt-1 text-sm text-gray-500">
              Configure the sampling algorithm to select pages for accessibility
              auditing. The algorithm follows the W3C WCAG-EM methodology with
              structured and random sampling.
            </p>
          </div>
          <button
            type="button"
            class="text-sm text-indigo-600 hover:text-indigo-500"
            @click="showHelp = !showHelp"
          >
            {{ showHelp ? 'Hide' : 'Show' }} help
          </button>
        </div>

        <!-- Help Panel -->
        <div v-if="showHelp" class="mt-4 rounded-md bg-blue-50 p-4">
          <h3 class="text-sm font-medium text-blue-800">
            About WCAG-EM Sampling
          </h3>
          <ul
            class="mt-2 text-sm text-blue-700 list-disc list-inside space-y-1"
          >
            <li>
              <strong>Structured Sample:</strong> Automatically selects the
              homepage and one page from each page type (forms, navigation,
              search, etc.)
            </li>
            <li>
              <strong>Random Sample:</strong> Additional pages selected randomly
              to catch issues not covered by structured selection
            </li>
            <li>
              <strong>Minimum Sample Size:</strong> Ensures at least this many
              pages are selected. If structured + random is less, more random
              pages are added.
            </li>
            <li>
              <strong>Maximum Sample Size:</strong> Total sample is capped at
              this number. Structured pages have priority over random.
            </li>
            <li>
              <strong>Random Ratio:</strong> Percentage of eligible pages to
              include in random sample (e.g., 0.1 = 10%).
            </li>
            <li>
              You can manually add or remove pages after the automatic selection
            </li>
          </ul>
        </div>

        <!-- Configuration Form -->
        <div class="mt-6 grid grid-cols-1 gap-6 sm:grid-cols-3">
          <div>
            <label
              for="min-sample"
              class="block text-sm font-medium text-gray-700"
            >
              Minimum Sample Size
            </label>
            <input
              id="min-sample"
              v-model.number="config.minSampleSize"
              type="number"
              min="3"
              max="30"
              class="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-indigo-500 focus:ring-indigo-500 sm:text-sm"
            />
            <p class="mt-1 text-xs text-gray-500">
              At least this many pages will be selected (3-30)
            </p>
          </div>
          <div>
            <label
              for="random-ratio"
              class="block text-sm font-medium text-gray-700"
            >
              Random Sample Ratio
            </label>
            <input
              id="random-ratio"
              v-model.number="config.randomRatio"
              type="number"
              min="0"
              max="0.3"
              step="0.05"
              class="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-indigo-500 focus:ring-indigo-500 sm:text-sm"
            />
            <p class="mt-1 text-xs text-gray-500">
              % of pages for random selection (0-0.3, default: 0.1 = 10%)
            </p>
          </div>
          <div>
            <label
              for="max-sample"
              class="block text-sm font-medium text-gray-700"
            >
              Maximum Sample Size
            </label>
            <input
              id="max-sample"
              v-model.number="config.maxSampleSize"
              type="number"
              min="5"
              max="30"
              class="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-indigo-500 focus:ring-indigo-500 sm:text-sm"
            />
            <p class="mt-1 text-xs text-gray-500">
              Maximum pages in sample (5-30)
            </p>
          </div>
        </div>

        <!-- Action Buttons -->
        <div class="mt-6 flex items-center space-x-3">
          <button
            type="button"
            class="inline-flex items-center rounded-md bg-indigo-600 px-4 py-2 text-sm font-semibold text-white shadow-sm hover:bg-indigo-500 focus:outline-none focus:ring-2 focus:ring-indigo-500 focus:ring-offset-2 disabled:cursor-not-allowed disabled:opacity-50"
            :disabled="applying"
            @click="handleApplySample"
          >
            <LoadingSpinner
              v-if="applying"
              size="sm"
              color="white"
              class="mr-2"
            />
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
                d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15"
              />
            </svg>
            {{
              applying
                ? 'Applying...'
                : hasSample
                  ? 'Recompute Sample'
                  : 'Compute Sample'
            }}
          </button>

          <button
            v-if="hasSample"
            type="button"
            class="inline-flex items-center rounded-md bg-green-600 px-4 py-2 text-sm font-semibold text-white shadow-sm hover:bg-green-500 focus:outline-none focus:ring-2 focus:ring-green-500 focus:ring-offset-2 disabled:cursor-not-allowed disabled:opacity-50"
            :disabled="isScanning || sampleSize === 0"
            @click="handleStartAudit"
          >
            <LoadingSpinner
              v-if="isScanning"
              size="sm"
              color="white"
              class="mr-2"
            />
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
                d="M9 5H7a2 2 0 00-2 2v12a2 2 0 002 2h10a2 2 0 002-2V7a2 2 0 00-2-2h-2M9 5a2 2 0 002 2h2a2 2 0 002-2M9 5a2 2 0 012-2h2a2 2 0 012 2m-6 9l2 2 4-4"
              />
            </svg>
            {{ isScanning ? 'Scanning...' : 'Start Accessibility Audit' }}
          </button>
        </div>

        <!-- Scanning Progress (SSE-driven) -->
        <div
          v-if="isScanning"
          class="mt-6 rounded-lg border border-indigo-100 bg-indigo-50 p-4"
        >
          <div class="flex items-center justify-between mb-2">
            <span class="text-sm font-medium text-indigo-800">
              {{
                scanProgress.message ||
                'Scanning pages for accessibility issues...'
              }}
            </span>
            <span class="text-sm text-indigo-600">
              {{ scanProgress.pagesScanned || 0 }} / {{ sampleSize }} pages
            </span>
          </div>
          <div class="h-2 w-full overflow-hidden rounded-full bg-indigo-200">
            <div
              class="h-2 rounded-full bg-indigo-600 transition-all duration-300"
              :style="{ width: `${scanProgress.percent || 5}%` }"
            ></div>
          </div>
          <!-- Current page being scanned -->
          <div
            v-if="scanProgress.currentPage"
            class="mt-2 text-xs text-indigo-600 truncate"
          >
            Scanning: {{ truncateUrl(scanProgress.currentPage) }}
          </div>
          <!-- Last completed page -->
          <div v-if="scanProgress.lastPage" class="mt-1 text-xs text-gray-500">
            <span class="text-green-600">✓</span> Completed:
            {{ truncateUrl(scanProgress.lastPage) }}
            <span
              v-if="scanProgress.findingsOnPage"
              class="ml-1 text-orange-600"
            >
              ({{ scanProgress.findingsOnPage }} issues found)
            </span>
          </div>
        </div>
      </div>

      <!-- Sample Summary -->
      <div
        v-if="sampleSummary"
        class="mb-6 rounded-lg border border-gray-200 bg-white p-6"
      >
        <h2 class="mb-4 text-lg font-medium text-gray-900">Sample Summary</h2>

        <div class="grid grid-cols-1 gap-4 sm:grid-cols-4">
          <div class="rounded-lg bg-gray-50 p-4">
            <div class="text-2xl font-bold text-gray-900">
              {{ sampleSummary.sampled_pages }}
            </div>
            <div class="text-sm text-gray-500">Pages in Sample</div>
          </div>
          <div class="rounded-lg bg-gray-50 p-4">
            <div class="text-2xl font-bold text-gray-900">
              {{ sampleSummary.total_pages }}
            </div>
            <div class="text-sm text-gray-500">Total Pages</div>
          </div>
          <div class="rounded-lg bg-blue-50 p-4">
            <div class="text-2xl font-bold text-blue-700">
              {{ structuredCount }}
            </div>
            <div class="text-sm text-blue-600">Structured Sample</div>
          </div>
          <div class="rounded-lg bg-purple-50 p-4">
            <div class="text-2xl font-bold text-purple-700">
              {{ randomPageCount }}
            </div>
            <div class="text-sm text-purple-600">Random Sample</div>
          </div>
        </div>

        <!-- By Type Breakdown -->
        <div
          v-if="
            sampleSummary.coverage &&
            Object.keys(sampleSummary.coverage).length > 0
          "
          class="mt-6"
        >
          <h3 class="mb-3 text-sm font-medium text-gray-700">
            Sampled Pages by Type
          </h3>
          <div class="flex flex-wrap gap-2">
            <span
              v-for="(count, pageType) in sampleSummary.coverage"
              :key="pageType"
              class="inline-flex items-center rounded-full bg-gray-100 px-3 py-1 text-sm font-medium text-gray-700"
            >
              {{ pageType }}
              <span class="ml-1.5 rounded-full bg-gray-200 px-2 py-0.5 text-xs">
                {{ count }}
              </span>
            </span>
          </div>
        </div>
      </div>

      <!-- Sampled Pages List -->
      <div class="rounded-lg border border-gray-200 bg-white">
        <div
          class="flex items-center justify-between border-b border-gray-200 px-6 py-4"
        >
          <h2 class="text-lg font-medium text-gray-900">
            All Pages
            <span
              v-if="sampledPages.length > 0"
              class="text-sm font-normal text-gray-500"
            >
              ({{ sampledPages.length }} pages,
              {{ sampleSummary?.sampled_pages || 0 }} in sample)
            </span>
          </h2>
          <div v-if="hasSample" class="text-sm text-gray-500">
            Click the checkbox to include/exclude pages
          </div>
        </div>

        <!-- Empty State -->
        <div v-if="!hasSample" class="p-8 text-center">
          <svg
            class="mx-auto h-12 w-12 text-gray-400"
            fill="none"
            stroke="currentColor"
            viewBox="0 0 24 24"
            aria-hidden="true"
          >
            <path
              stroke-linecap="round"
              stroke-linejoin="round"
              stroke-width="1.5"
              d="M19 11H5m14 0a2 2 0 012 2v6a2 2 0 01-2 2H5a2 2 0 01-2-2v-6a2 2 0 012-2m14 0V9a2 2 0 00-2-2M5 11V9a2 2 0 012-2m0 0V5a2 2 0 012-2h6a2 2 0 012 2v2M7 7h10"
            />
          </svg>
          <h3 class="mt-4 text-sm font-medium text-gray-900">
            No sample computed yet
          </h3>
          <p class="mt-2 text-sm text-gray-500">
            Click "Compute Sample" above to select pages for the accessibility
            audit.
          </p>
        </div>

        <!-- Loading -->
        <div
          v-else-if="loadingPages"
          class="flex items-center justify-center py-12"
        >
          <LoadingSpinner size="md" />
        </div>

        <!-- Pages Table -->
        <div v-else-if="sampledPages.length > 0" class="overflow-hidden">
          <table class="min-w-full divide-y divide-gray-200">
            <thead class="bg-gray-50">
              <tr>
                <th scope="col" class="w-12 px-6 py-3 text-left">
                  <span class="sr-only">Include</span>
                </th>
                <th
                  scope="col"
                  class="px-6 py-3 text-left text-xs font-medium uppercase tracking-wider text-gray-500"
                >
                  URL
                </th>
                <th
                  scope="col"
                  class="px-6 py-3 text-left text-xs font-medium uppercase tracking-wider text-gray-500"
                >
                  Title
                </th>
                <th
                  scope="col"
                  class="px-6 py-3 text-left text-xs font-medium uppercase tracking-wider text-gray-500"
                >
                  Type
                </th>
                <th
                  scope="col"
                  class="px-6 py-3 text-left text-xs font-medium uppercase tracking-wider text-gray-500"
                >
                  Reason
                </th>
                <th
                  scope="col"
                  class="px-6 py-3 text-left text-xs font-medium uppercase tracking-wider text-gray-500"
                >
                  Status
                </th>
              </tr>
            </thead>
            <tbody class="divide-y divide-gray-200 bg-white">
              <tr
                v-for="page in displayedPages"
                :key="page.id"
                class="hover:bg-gray-50"
                :class="{ 'bg-indigo-50': page.in_sample }"
              >
                <td class="whitespace-nowrap px-6 py-4">
                  <input
                    type="checkbox"
                    :checked="page.in_sample"
                    class="h-4 w-4 rounded border-gray-300 text-indigo-600 focus:ring-indigo-500"
                    @change="handleTogglePage(page)"
                  />
                </td>
                <td class="px-6 py-4">
                  <a
                    :href="page.url"
                    target="_blank"
                    rel="noopener noreferrer"
                    class="text-sm text-indigo-600 hover:text-indigo-900 hover:underline"
                    :title="page.url"
                  >
                    {{ truncateUrl(page.url) }}
                  </a>
                </td>
                <td class="px-6 py-4 text-sm text-gray-900">
                  {{ page.title || '(No title)' }}
                </td>
                <td class="whitespace-nowrap px-6 py-4">
                  <span
                    class="inline-flex rounded-full bg-gray-100 px-2 py-1 text-xs font-medium text-gray-700"
                  >
                    {{ page.page_type }}
                  </span>
                </td>
                <td class="whitespace-nowrap px-6 py-4">
                  <span
                    v-if="page.in_sample && page.sample_reason"
                    class="inline-flex rounded-full px-2 py-1 text-xs font-medium"
                    :class="{
                      'bg-blue-100 text-blue-700':
                        page.sample_reason === 'structured',
                      'bg-purple-100 text-purple-700':
                        page.sample_reason === 'random',
                      'bg-gray-100 text-gray-700':
                        page.sample_reason === 'minimum' || !page.sample_reason,
                    }"
                  >
                    {{ page.sample_reason }}
                  </span>
                  <span v-else class="text-sm text-gray-400">-</span>
                </td>
                <td class="whitespace-nowrap px-6 py-4">
                  <span
                    class="inline-flex rounded-full px-2 py-1 text-xs font-medium"
                    :class="getHttpStatusClass(page.http_status)"
                  >
                    {{ page.http_status || 'N/A' }}
                  </span>
                </td>
              </tr>
            </tbody>
          </table>

          <!-- Pagination -->
          <div
            v-if="totalDisplayedPages > paginationLimit"
            class="flex items-center justify-between border-t border-gray-200 bg-white px-6 py-3"
          >
            <div class="text-sm text-gray-700">
              Showing {{ paginationSkip + 1 }} to
              {{
                Math.min(paginationSkip + paginationLimit, totalDisplayedPages)
              }}
              of {{ totalDisplayedPages }}
            </div>
            <div class="flex space-x-2">
              <button
                type="button"
                class="rounded-md border border-gray-300 bg-white px-3 py-1.5 text-sm font-medium text-gray-700 hover:bg-gray-50 disabled:cursor-not-allowed disabled:opacity-50"
                :disabled="paginationSkip === 0"
                @click="prevPage"
              >
                Previous
              </button>
              <button
                type="button"
                class="rounded-md border border-gray-300 bg-white px-3 py-1.5 text-sm font-medium text-gray-700 hover:bg-gray-50 disabled:cursor-not-allowed disabled:opacity-50"
                :disabled="
                  paginationSkip + paginationLimit >= totalDisplayedPages
                "
                @click="nextPage"
              >
                Next
              </button>
            </div>
          </div>
        </div>
      </div>

      <!-- Error Toast -->
      <ErrorToast
        v-if="showError"
        :title="errorTitle"
        :message="errorMessage"
        @close="showError = false"
      />
    </template>
  </AppLayout>
</template>

<script setup>
import { computed, onMounted, onUnmounted, ref } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import ErrorToast from '../components/common/ErrorToast.vue'
import LoadingSpinner from '../components/common/LoadingSpinner.vue'
import StatusBadge from '../components/common/StatusBadge.vue'
import AppLayout from '../components/layout/AppLayout.vue'
import PageHeader from '../components/layout/PageHeader.vue'
import { usePermissions } from '../composables/usePermissions'
import api from '../lib/api'
import { useEvaluationsStore } from '../stores/evaluations'
import { useSamplingStore } from '../stores/sampling'
import { useTasksStore } from '../stores/tasks'

const route = useRoute()
const router = useRouter()
const evaluationsStore = useEvaluationsStore()
const samplingStore = useSamplingStore()
const tasksStore = useTasksStore()
const { canStartScan } = usePermissions()

// Reactive state
const loading = ref(true)
const error = ref('')
const showHelp = ref(false)
const loadingPages = ref(false)
const applying = ref(false)
const currentTaskId = ref(null)

// Pagination (for local filtering)
const paginationSkip = ref(0)
const paginationLimit = ref(50)

// Computed for displayed pages (local pagination)
const displayedPages = computed(() => {
  const start = paginationSkip.value
  const end = start + paginationLimit.value
  return sampledPages.value.slice(start, end)
})

const totalDisplayedPages = computed(() => sampledPages.value.length)

// Configuration
const config = ref({
  minSampleSize: 5,
  randomRatio: 0.1,
  maxSampleSize: 15,
})

// Error toast state
const showError = ref(false)
const errorTitle = ref('Error')
const errorMessage = ref('')

// Computed
const evaluationId = computed(() => route.params.id)
const evaluation = computed(() => evaluationsStore.current)

const sampleSummary = computed(() => samplingStore.sampleSummary)
const sampledPages = computed(() => samplingStore.sampledPages)
const hasSample = computed(() => samplingStore.hasSample)
const sampleSize = computed(() => samplingStore.sampleSize)

const structuredCount = computed(() => {
  // Count pages with sample_reason = 'structured'
  return sampledPages.value.filter(
    (p) => p.in_sample && p.sample_reason === 'structured',
  ).length
})

const randomPageCount = computed(() => {
  // Count pages with sample_reason = 'random'
  return sampledPages.value.filter(
    (p) => p.in_sample && p.sample_reason === 'random',
  ).length
})

const isScanning = computed(() => {
  return evaluation.value?.status === 'AUDITING'
})

// SSE-driven scan progress
const scanProgress = computed(() => {
  if (!currentTaskId.value) {
    return {
      percent: 5,
      message: 'Starting scan...',
      pagesScanned: 0,
      currentPage: null,
      lastPage: null,
      findingsOnPage: 0,
    }
  }
  const progress = tasksStore.getProgress(currentTaskId.value)
  return {
    percent: progress?.percent || 5,
    message: progress?.message || 'Scanning pages...',
    pagesScanned: progress?.pagesScanned || 0,
    currentPage: progress?.currentPage || null,
    lastPage: progress?.lastPage || null,
    findingsOnPage: progress?.findingsOnPage || 0,
  }
})

// Methods
function truncateUrl(url) {
  try {
    const parsed = new URL(url)
    return parsed.pathname.length > 50
      ? parsed.pathname.substring(0, 47) + '...'
      : parsed.pathname || '/'
  } catch {
    return url.length > 50 ? url.substring(0, 47) + '...' : url
  }
}

function getHttpStatusClass(status) {
  if (status >= 200 && status < 300) {
    return 'bg-green-100 text-green-800'
  } else if (status >= 300 && status < 400) {
    return 'bg-yellow-100 text-yellow-800'
  } else if (status >= 400) {
    return 'bg-red-100 text-red-800'
  }
  return 'bg-gray-100 text-gray-800'
}

function showErrorToast(title, message) {
  errorTitle.value = title
  errorMessage.value = message
  showError.value = true
}

function nextPage() {
  if (
    paginationSkip.value + paginationLimit.value <
    totalDisplayedPages.value
  ) {
    paginationSkip.value += paginationLimit.value
  }
}

function prevPage() {
  if (paginationSkip.value > 0) {
    paginationSkip.value = Math.max(
      0,
      paginationSkip.value - paginationLimit.value,
    )
  }
}

async function handleApplySample() {
  applying.value = true
  try {
    await samplingStore.applySample(evaluationId.value, {
      min_sample_size: config.value.minSampleSize,
      max_sample_size: config.value.maxSampleSize,
      random_sample_ratio: config.value.randomRatio,
    })

    // Reset pagination
    paginationSkip.value = 0
  } catch (err) {
    console.error('Failed to apply sample:', err)
    showErrorToast('Failed to compute sample', err.message)
  } finally {
    applying.value = false
  }
}

async function handleTogglePage(page) {
  try {
    await samplingStore.togglePageInSample(
      evaluationId.value,
      page.id,
      !page.in_sample,
    )
  } catch (err) {
    console.error('Failed to toggle page:', err)
    showErrorToast('Failed to update page', err.message)
  }
}

async function handleStartAudit() {
  try {
    const response = await api.post(`/evaluations/${evaluationId.value}/scan`)

    const taskId = response.data.task_id
    currentTaskId.value = taskId

    // Refresh evaluation to get updated status
    await evaluationsStore.fetchOne(evaluationId.value)

    // Start polling for task completion (uses SSE with polling fallback)
    tasksStore.startPolling(
      taskId,
      // On success
      async (result) => {
        currentTaskId.value = null
        await evaluationsStore.fetchOne(evaluationId.value)
        // Redirect to findings page after successful audit
        router.push({
          name: 'Findings',
          params: { id: evaluationId.value },
        })
      },
      // On error
      (errorMsg) => {
        currentTaskId.value = null
        showErrorToast('Scan failed', errorMsg)
        evaluationsStore.fetchOne(evaluationId.value)
      },
    )
  } catch (err) {
    console.error('Failed to start scan:', err)
    showErrorToast('Failed to start accessibility audit', err.message)
  }
}

// Lifecycle
onMounted(async () => {
  loading.value = true

  try {
    // Fetch evaluation details
    await evaluationsStore.fetchOne(evaluationId.value)

    if (evaluation.value) {
      // Fetch sample data (summary + pages)
      try {
        await samplingStore.fetchSampleSummary(evaluationId.value)
      } catch (err) {
        // Sample may not exist yet, that's ok
        console.log('No sample yet:', err.message)
      }
    }
  } catch (err) {
    error.value = err.message || 'Failed to load evaluation'
  } finally {
    loading.value = false
  }
})

onUnmounted(() => {
  // Clean up any active SSE/polling on unmount
  tasksStore.stopAll()
})
</script>
