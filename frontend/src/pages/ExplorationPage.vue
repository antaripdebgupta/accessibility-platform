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
        title="Website Exploration"
        :subtitle="evaluation.target_url"
        :back-to="{ name: 'EvaluationDetail', params: { id: evaluationId } }"
      >
        <StatusBadge :status="evaluation.status" />
      </PageHeader>

      <!-- Crawl Control Panel -->
      <div class="mb-6 rounded-lg border border-gray-200 bg-white p-6">
        <h2 class="mb-4 text-lg font-medium text-gray-900">
          Crawl Configuration
        </h2>

        <!-- Already Crawled State -->
        <div v-if="hasCrawled" class="space-y-4">
          <div class="flex items-center space-x-2 text-green-600">
            <svg
              class="h-5 w-5"
              fill="none"
              stroke="currentColor"
              viewBox="0 0 24 24"
              aria-hidden="true"
            >
              <path
                stroke-linecap="round"
                stroke-linejoin="round"
                stroke-width="2"
                d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z"
              />
            </svg>
            <span class="text-sm font-medium"
              >Exploration complete - {{ totalPages }} pages discovered</span
            >
          </div>
          <button
            type="button"
            class="inline-flex items-center rounded-md border border-gray-300 bg-white px-4 py-2 text-sm font-medium text-gray-700 shadow-sm hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-indigo-500 focus:ring-offset-2"
            @click="handleRecrawl"
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
                d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15"
              />
            </svg>
            Re-crawl Website
          </button>
        </div>

        <!-- Crawling In Progress -->
        <div v-else-if="isCrawling" class="space-y-4">
          <div class="flex items-center space-x-3">
            <LoadingSpinner size="sm" />
            <span class="text-sm text-gray-600">
              Exploring website... This may take a few minutes.
            </span>
          </div>
          <div class="h-2 w-full overflow-hidden rounded-full bg-gray-200">
            <div
              class="h-2 animate-pulse rounded-full bg-indigo-500"
              style="width: 60%"
            ></div>
          </div>
        </div>

        <!-- Crawl Configuration Form -->
        <div v-else class="space-y-4">
          <p class="text-sm text-gray-600">
            Configure how the crawler will discover pages on the target website.
          </p>

          <div class="grid grid-cols-1 gap-4 sm:grid-cols-2">
            <!-- Max Pages -->
            <div>
              <label
                for="maxPages"
                class="block text-sm font-medium text-gray-700"
              >
                Maximum Pages
              </label>
              <select
                id="maxPages"
                v-model.number="crawlOptions.maxPages"
                class="mt-1 block w-full rounded-md border-gray-300 py-2 pl-3 pr-10 text-base focus:border-indigo-500 focus:outline-none focus:ring-indigo-500 sm:text-sm"
              >
                <option :value="10">10 pages</option>
                <option :value="15">15 pages (recommended)</option>
                <option :value="25">25 pages</option>
                <option :value="50">50 pages</option>
              </select>
              <p class="mt-1 text-xs text-gray-500">
                More pages = longer crawl time
              </p>
            </div>

            <!-- Respect Robots.txt -->
            <div>
              <label class="block text-sm font-medium text-gray-700">
                Robots.txt
              </label>
              <div class="mt-2">
                <label class="inline-flex items-center">
                  <input
                    v-model="crawlOptions.respectRobots"
                    type="checkbox"
                    class="h-4 w-4 rounded border-gray-300 text-indigo-600 focus:ring-indigo-500"
                  />
                  <span class="ml-2 text-sm text-gray-600">
                    Respect robots.txt rules
                  </span>
                </label>
              </div>
              <p class="mt-1 text-xs text-gray-500">
                Recommended for production sites
              </p>
            </div>
          </div>

          <div class="flex items-center space-x-3 pt-4">
            <button
              type="button"
              class="inline-flex items-center rounded-md bg-indigo-600 px-4 py-2 text-sm font-semibold text-white shadow-sm hover:bg-indigo-500 focus:outline-none focus:ring-2 focus:ring-indigo-500 focus:ring-offset-2"
              :disabled="isCrawling"
              @click="handleStartCrawl"
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
                  d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z"
                />
              </svg>
              Start Exploration
            </button>
          </div>
        </div>
      </div>

      <!-- Pages Summary -->
      <div
        v-if="pageSummary && pageSummary.total_pages > 0"
        class="mb-6 rounded-lg border border-gray-200 bg-white p-6"
      >
        <h2 class="mb-4 text-lg font-medium text-gray-900">Pages by Type</h2>
        <div class="flex flex-wrap gap-3">
          <button
            v-for="type in pageSummary.by_type"
            :key="type.page_type"
            type="button"
            class="inline-flex items-center rounded-full px-3 py-1.5 text-sm font-medium transition-colors"
            :class="[
              selectedPageType === type.page_type
                ? 'bg-indigo-600 text-white'
                : 'bg-gray-100 text-gray-700 hover:bg-gray-200',
            ]"
            @click="togglePageTypeFilter(type.page_type)"
          >
            {{ type.page_type }}
            <span
              class="ml-1.5 rounded-full px-2 py-0.5 text-xs"
              :class="[
                selectedPageType === type.page_type
                  ? 'bg-indigo-500'
                  : 'bg-gray-200',
              ]"
            >
              {{ type.count }}
            </span>
          </button>
          <button
            v-if="selectedPageType"
            type="button"
            class="inline-flex items-center rounded-full bg-gray-200 px-3 py-1.5 text-sm font-medium text-gray-600 hover:bg-gray-300"
            @click="selectedPageType = null"
          >
            <svg
              class="-ml-0.5 mr-1 h-4 w-4"
              fill="none"
              stroke="currentColor"
              viewBox="0 0 24 24"
              aria-hidden="true"
            >
              <path
                stroke-linecap="round"
                stroke-linejoin="round"
                stroke-width="2"
                d="M6 18L18 6M6 6l12 12"
              />
            </svg>
            Clear filter
          </button>
        </div>
      </div>

      <!-- Pages List -->
      <div class="rounded-lg border border-gray-200 bg-white">
        <div class="border-b border-gray-200 px-6 py-4">
          <h2 class="text-lg font-medium text-gray-900">
            Discovered Pages
            <span
              v-if="totalPages > 0"
              class="text-sm font-normal text-gray-500"
            >
              ({{ totalPages }} total)
            </span>
          </h2>
        </div>

        <!-- Empty State -->
        <div v-if="!hasCrawled && pages.length === 0" class="p-8 text-center">
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
              d="M21 12a9 9 0 01-9 9m9-9a9 9 0 00-9-9m9 9H3m9 9a9 9 0 01-9-9m9 9c1.657 0 3-4.03 3-9s-1.343-9-3-9m0 18c-1.657 0-3-4.03-3-9s1.343-9 3-9m-9 9a9 9 0 019-9"
            />
          </svg>
          <h3 class="mt-4 text-sm font-medium text-gray-900">
            No pages discovered yet
          </h3>
          <p class="mt-2 text-sm text-gray-500">
            Start the crawl to discover pages on the target website.
          </p>
        </div>

        <!-- Loading Pages -->
        <div
          v-else-if="loadingPages"
          class="flex items-center justify-center py-12"
        >
          <LoadingSpinner size="md" />
        </div>

        <!-- Pages Table -->
        <div v-else-if="pages.length > 0" class="overflow-x-auto">
          <table class="min-w-full divide-y divide-gray-200">
            <thead class="bg-gray-50">
              <tr>
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
                  Status
                </th>
                <th
                  scope="col"
                  class="px-6 py-3 text-left text-xs font-medium uppercase tracking-wider text-gray-500"
                >
                  In Sample
                </th>
              </tr>
            </thead>
            <tbody class="divide-y divide-gray-200 bg-white">
              <tr v-for="page in pages" :key="page.id" class="hover:bg-gray-50">
                <td class="max-w-xs truncate px-6 py-4 text-sm text-gray-900">
                  <a
                    :href="page.url"
                    target="_blank"
                    rel="noopener noreferrer"
                    class="text-indigo-600 hover:text-indigo-500 hover:underline"
                  >
                    {{ truncateUrl(page.url) }}
                  </a>
                </td>
                <td class="max-w-xs truncate px-6 py-4 text-sm text-gray-500">
                  {{ page.title || '—' }}
                </td>
                <td class="whitespace-nowrap px-6 py-4">
                  <PageTypeTag :page-type="page.page_type" />
                </td>
                <td class="whitespace-nowrap px-6 py-4 text-sm">
                  <span
                    v-if="page.http_status"
                    class="inline-flex items-center rounded-full px-2.5 py-0.5 text-xs font-medium"
                    :class="getHttpStatusClass(page.http_status)"
                  >
                    {{ page.http_status }}
                  </span>
                  <span v-else class="text-gray-400">—</span>
                </td>
                <td class="whitespace-nowrap px-6 py-4 text-sm">
                  <span
                    v-if="page.in_sample"
                    class="inline-flex items-center text-green-600"
                  >
                    <svg
                      class="mr-1 h-4 w-4"
                      fill="currentColor"
                      viewBox="0 0 20 20"
                    >
                      <path
                        fill-rule="evenodd"
                        d="M16.707 5.293a1 1 0 010 1.414l-8 8a1 1 0 01-1.414 0l-4-4a1 1 0 011.414-1.414L8 12.586l7.293-7.293a1 1 0 011.414 0z"
                        clip-rule="evenodd"
                      />
                    </svg>
                    Yes
                  </span>
                  <span v-else class="text-gray-400">No</span>
                </td>
              </tr>
            </tbody>
          </table>
        </div>

        <!-- Pagination -->
        <div
          v-if="totalPages > paginationLimit"
          class="flex items-center justify-between border-t border-gray-200 bg-white px-6 py-3"
        >
          <div class="flex flex-1 justify-between sm:hidden">
            <button
              :disabled="paginationSkip === 0"
              class="relative inline-flex items-center rounded-md border border-gray-300 bg-white px-4 py-2 text-sm font-medium text-gray-700 hover:bg-gray-50 disabled:cursor-not-allowed disabled:opacity-50"
              @click="prevPage"
            >
              Previous
            </button>
            <button
              :disabled="paginationSkip + paginationLimit >= totalPages"
              class="relative ml-3 inline-flex items-center rounded-md border border-gray-300 bg-white px-4 py-2 text-sm font-medium text-gray-700 hover:bg-gray-50 disabled:cursor-not-allowed disabled:opacity-50"
              @click="nextPage"
            >
              Next
            </button>
          </div>
          <div
            class="hidden sm:flex sm:flex-1 sm:items-center sm:justify-between"
          >
            <div>
              <p class="text-sm text-gray-700">
                Showing
                <span class="font-medium">{{ paginationSkip + 1 }}</span>
                to
                <span class="font-medium">
                  {{ Math.min(paginationSkip + paginationLimit, totalPages) }}
                </span>
                of
                <span class="font-medium">{{ totalPages }}</span>
                results
              </p>
            </div>
            <div>
              <nav
                class="isolate inline-flex -space-x-px rounded-md shadow-sm"
                aria-label="Pagination"
              >
                <button
                  :disabled="paginationSkip === 0"
                  class="relative inline-flex items-center rounded-l-md px-2 py-2 text-gray-400 ring-1 ring-inset ring-gray-300 hover:bg-gray-50 focus:z-20 focus:outline-offset-0 disabled:cursor-not-allowed disabled:opacity-50"
                  @click="prevPage"
                >
                  <span class="sr-only">Previous</span>
                  <svg
                    class="h-5 w-5"
                    viewBox="0 0 20 20"
                    fill="currentColor"
                    aria-hidden="true"
                  >
                    <path
                      fill-rule="evenodd"
                      d="M12.79 5.23a.75.75 0 01-.02 1.06L8.832 10l3.938 3.71a.75.75 0 11-1.04 1.08l-4.5-4.25a.75.75 0 010-1.08l4.5-4.25a.75.75 0 011.06.02z"
                      clip-rule="evenodd"
                    />
                  </svg>
                </button>
                <button
                  :disabled="paginationSkip + paginationLimit >= totalPages"
                  class="relative inline-flex items-center rounded-r-md px-2 py-2 text-gray-400 ring-1 ring-inset ring-gray-300 hover:bg-gray-50 focus:z-20 focus:outline-offset-0 disabled:cursor-not-allowed disabled:opacity-50"
                  @click="nextPage"
                >
                  <span class="sr-only">Next</span>
                  <svg
                    class="h-5 w-5"
                    viewBox="0 0 20 20"
                    fill="currentColor"
                    aria-hidden="true"
                  >
                    <path
                      fill-rule="evenodd"
                      d="M7.21 14.77a.75.75 0 01.02-1.06L11.168 10 7.23 6.29a.75.75 0 111.04-1.08l4.5 4.25a.75.75 0 010 1.08l-4.5 4.25a.75.75 0 01-1.06-.02z"
                      clip-rule="evenodd"
                    />
                  </svg>
                </button>
              </nav>
            </div>
          </div>
        </div>
      </div>
    </template>

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
import { computed, onMounted, onUnmounted, ref, watch } from 'vue'
import { useRoute } from 'vue-router'

import ErrorToast from '../components/common/ErrorToast.vue'
import LoadingSpinner from '../components/common/LoadingSpinner.vue'
import PageTypeTag from '../components/common/PageTypeTag.vue'
import StatusBadge from '../components/common/StatusBadge.vue'
import AppLayout from '../components/layout/AppLayout.vue'
import PageHeader from '../components/layout/PageHeader.vue'
import api from '../lib/api'
import { useEvaluationsStore } from '../stores/evaluations'
import { useTasksStore } from '../stores/tasks'

const route = useRoute()
const evaluationsStore = useEvaluationsStore()
const tasksStore = useTasksStore()

// Reactive state
const loading = ref(true)
const error = ref('')
const pages = ref([])
const loadingPages = ref(false)
const totalPages = ref(0)
const pageSummary = ref(null)
const selectedPageType = ref(null)
const paginationSkip = ref(0)
const paginationLimit = ref(50)

// Error toast state
const showError = ref(false)
const errorTitle = ref('Error')
const errorMessage = ref('')

// Crawl options
const crawlOptions = ref({
  maxPages: 15,
  respectRobots: true,
})

// Computed
const evaluationId = computed(() => route.params.id)
const evaluation = computed(() => evaluationsStore.current)

const isCrawling = computed(() => {
  return evaluation.value?.status === 'EXPLORING'
})

const hasCrawled = computed(() => {
  const status = evaluation.value?.status
  return (
    status === 'SAMPLING' ||
    status === 'AUDITING' ||
    status === 'REPORTING' ||
    status === 'COMPLETE'
  )
})

// Watch for page type filter changes
watch(selectedPageType, () => {
  paginationSkip.value = 0
  fetchPages()
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

function togglePageTypeFilter(type) {
  if (selectedPageType.value === type) {
    selectedPageType.value = null
  } else {
    selectedPageType.value = type
  }
}

function nextPage() {
  if (paginationSkip.value + paginationLimit.value < totalPages.value) {
    paginationSkip.value += paginationLimit.value
    fetchPages()
  }
}

function prevPage() {
  if (paginationSkip.value > 0) {
    paginationSkip.value = Math.max(
      0,
      paginationSkip.value - paginationLimit.value,
    )
    fetchPages()
  }
}

function showErrorToast(title, message) {
  errorTitle.value = title
  errorMessage.value = message
  showError.value = true
}

async function fetchPages() {
  loadingPages.value = true

  try {
    const params = new URLSearchParams()
    params.append('skip', paginationSkip.value)
    params.append('limit', paginationLimit.value)

    if (selectedPageType.value) {
      params.append('page_type', selectedPageType.value)
    }

    const response = await api.get(
      `/evaluations/${evaluationId.value}/pages?${params.toString()}`,
    )

    pages.value = response.data.items
    totalPages.value = response.data.total
  } catch (err) {
    console.error('Failed to fetch pages:', err)
    showErrorToast('Failed to load pages', err.message)
  } finally {
    loadingPages.value = false
  }
}

async function fetchPageSummary() {
  try {
    const response = await api.get(
      `/evaluations/${evaluationId.value}/pages/summary`,
    )
    pageSummary.value = response.data
  } catch (err) {
    console.error('Failed to fetch page summary:', err)
  }
}

async function handleStartCrawl() {
  try {
    const response = await api.post(
      `/evaluations/${evaluationId.value}/explore`,
      {
        max_pages: crawlOptions.value.maxPages,
        respect_robots: crawlOptions.value.respectRobots,
      },
    )

    const taskId = response.data.task_id

    // Refresh evaluation to get updated status
    await evaluationsStore.fetchOne(evaluationId.value)

    // Start polling for task completion
    tasksStore.startPolling(
      taskId,
      // On success
      async (result) => {
        await evaluationsStore.fetchOne(evaluationId.value)
        await fetchPages()
        await fetchPageSummary()
      },
      // On error
      (errorMsg) => {
        showErrorToast('Crawl failed', errorMsg)
        evaluationsStore.fetchOne(evaluationId.value)
      },
    )
  } catch (err) {
    console.error('Failed to start crawl:', err)
    showErrorToast('Failed to start exploration', err.message)
  }
}

async function handleRecrawl() {
  const confirmed = window.confirm(
    'This will clear existing pages and re-crawl the website. Continue?',
  )

  if (!confirmed) return

  // Reset pages and start new crawl
  pages.value = []
  totalPages.value = 0
  pageSummary.value = null
  await handleStartCrawl()
}

// Lifecycle
onMounted(async () => {
  loading.value = true

  try {
    // Fetch evaluation details
    await evaluationsStore.fetchOne(evaluationId.value)

    if (evaluation.value) {
      // Fetch pages if crawl has been done
      if (hasCrawled.value || evaluation.value.status === 'EXPLORING') {
        await Promise.all([fetchPages(), fetchPageSummary()])
      }
    }
  } catch (err) {
    error.value = err.message || 'Failed to load evaluation'
  } finally {
    loading.value = false
  }
})

onUnmounted(() => {
  // Clean up any polling on unmount
  tasksStore.stopAll()
})
</script>
