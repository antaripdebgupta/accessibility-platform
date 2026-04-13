<template>
  <div class="min-h-screen top-10 bg-gray-50 dark:bg-gray-900">
    <div class="mx-auto max-w-7xl px-4 py-8 sm:px-6 lg:px-8">
      <!-- Page Header -->
      <div class="mb-8">
        <h1 class="text-3xl pt-10 font-bold text-gray-900 dark:text-white">
          Longitudinal Dashboard
        </h1>
        <p class="mt-2 text-gray-600 dark:text-gray-400">
          Track accessibility trends over time and detect regressions
        </p>
      </div>

      <!-- Help Panel -->
      <LongitudinalHelpPanel />

      <!-- Loading State -->
      <div v-if="loading" class="flex items-center justify-center py-20">
        <div class="flex flex-col items-center gap-4">
          <svg
            class="h-10 w-10 animate-spin text-blue-600"
            fill="none"
            viewBox="0 0 24 24"
          >
            <circle
              class="opacity-25"
              cx="12"
              cy="12"
              r="10"
              stroke="currentColor"
              stroke-width="4"
            />
            <path
              class="opacity-75"
              fill="currentColor"
              d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"
            />
          </svg>
          <span class="text-gray-600 dark:text-gray-400">
            Loading series data...
          </span>
        </div>
      </div>

      <!-- Error State -->
      <div
        v-else-if="error"
        class="rounded-lg border border-red-300 bg-red-50 p-6 dark:border-red-700 dark:bg-red-900/20"
      >
        <p class="text-red-700 dark:text-red-300">{{ error }}</p>
        <button
          class="mt-4 rounded bg-red-600 px-4 py-2 text-white hover:bg-red-700"
          @click="loadData"
        >
          Retry
        </button>
      </div>

      <!-- Main Content -->
      <div v-else class="space-y-8">
        <!-- Series List View (when no series selected) -->
        <div v-if="!selectedSeriesId">
          <div class="mb-6 flex items-center justify-between">
            <h2 class="text-xl font-semibold text-gray-900 dark:text-white">
              Evaluation Series ({{ allSeries.length }})
            </h2>
          </div>

          <!-- Empty State -->
          <div
            v-if="allSeries.length === 0"
            class="rounded-lg border-2 border-dashed border-gray-300 p-12 text-center dark:border-gray-700"
          >
            <svg
              class="mx-auto h-12 w-12 text-gray-400"
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
            <h3 class="mt-4 text-lg font-medium text-gray-900 dark:text-white">
              No evaluation series yet
            </h3>
            <p class="mt-2 text-gray-600 dark:text-gray-400">
              Series are created automatically when evaluations are completed.
              Run an evaluation on a target URL to get started.
            </p>
          </div>

          <!-- Series Cards -->
          <div v-else class="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
            <button
              v-for="series in allSeries"
              :key="series.id"
              class="rounded-lg border border-gray-200 bg-white p-4 text-left transition-shadow hover:shadow-md dark:border-gray-700 dark:bg-gray-800"
              @click="selectSeries(series.id)"
            >
              <h3 class="font-semibold text-gray-900 dark:text-white">
                {{ series.display_name || series.target_url }}
              </h3>
              <p class="mt-1 truncate text-sm text-gray-500 dark:text-gray-400">
                {{ series.target_url }}
              </p>
              <div
                class="mt-3 flex items-center gap-4 text-sm text-gray-600 dark:text-gray-400"
              >
                <span>{{ series.snapshot_count || 0 }} evaluations</span>
                <span v-if="series.latest_snapshot_date">
                  Last: {{ formatDate(series.latest_snapshot_date) }}
                </span>
              </div>
            </button>
          </div>
        </div>

        <!-- Series Detail View -->
        <div v-else>
          <!-- Back Button & Header -->
          <div class="mb-6 flex items-center gap-4">
            <button
              class="flex items-center gap-2 rounded-lg border border-gray-300 px-3 py-2 text-sm text-gray-700 hover:bg-gray-50 dark:border-gray-600 dark:text-gray-300 dark:hover:bg-gray-800"
              @click="selectedSeriesId = null"
            >
              <svg
                class="h-4 w-4"
                fill="none"
                stroke="currentColor"
                viewBox="0 0 24 24"
              >
                <path
                  stroke-linecap="round"
                  stroke-linejoin="round"
                  stroke-width="2"
                  d="M10 19l-7-7m0 0l7-7m-7 7h18"
                />
              </svg>
              Back to all series
            </button>
          </div>

          <div v-if="currentSeries">
            <!-- Series Header -->
            <div class="mb-6">
              <div class="flex items-start justify-between">
                <div>
                  <h2 class="text-2xl font-bold text-gray-900 dark:text-white">
                    {{ currentSeries.display_name || currentSeries.target_url }}
                  </h2>
                  <a
                    :href="currentSeries.target_url"
                    target="_blank"
                    rel="noopener noreferrer"
                    class="mt-1 inline-flex items-center gap-1 text-blue-600 hover:underline dark:text-blue-400"
                  >
                    {{ currentSeries.target_url }}
                    <svg
                      class="h-4 w-4"
                      fill="none"
                      stroke="currentColor"
                      viewBox="0 0 24 24"
                    >
                      <path
                        stroke-linecap="round"
                        stroke-linejoin="round"
                        stroke-width="2"
                        d="M10 6H6a2 2 0 00-2 2v10a2 2 0 002 2h10a2 2 0 002-2v-4M14 4h6m0 0v6m0-6L10 14"
                      />
                    </svg>
                  </a>
                </div>
                <button
                  class="rounded-lg border border-gray-300 px-3 py-2 text-sm text-gray-700 hover:bg-gray-50 dark:border-gray-600 dark:text-gray-300 dark:hover:bg-gray-800"
                  @click="showRenameModal = true"
                >
                  Rename
                </button>
              </div>
            </div>

            <!-- Trend Summary Cards -->
            <TrendSummaryCards
              v-if="trends"
              :total-evaluations="currentSeries.snapshots?.length || 0"
              :net-change="trends.total_change"
              :regressions-count="trends.regressions?.length || 0"
              :improvements-count="trends.improvements?.length || 0"
            />

            <!-- Regression Alert -->
            <RegressionAlert
              v-if="trends"
              class="mt-6"
              :regressions="trends.regressions || []"
              :new-failures="trends.new_failures || []"
            />

            <!-- Charts Section -->
            <div class="mt-8 grid gap-6 lg:grid-cols-2">
              <!-- Total Findings Chart -->
              <div
                class="rounded-lg border border-gray-200 bg-white p-4 dark:border-gray-700 dark:bg-gray-800"
              >
                <h3
                  class="mb-4 text-lg font-semibold text-gray-900 dark:text-white"
                >
                  Total Findings Over Time
                </h3>
                <TotalFindingsChart
                  :snapshots="currentSeries.snapshots || []"
                />
              </div>

              <!-- Verdict History Chart -->
              <div
                class="rounded-lg border border-gray-200 bg-white p-4 dark:border-gray-700 dark:bg-gray-800"
              >
                <h3
                  class="mb-4 text-lg font-semibold text-gray-900 dark:text-white"
                >
                  Conformance Verdict History
                </h3>
                <VerdictHistoryChart
                  :snapshots="currentSeries.snapshots || []"
                />
              </div>
            </div>

            <!-- Criterion Trends Section -->
            <div
              v-if="trends && trends.criterion_trends?.length > 0"
              class="mt-8"
            >
              <h3
                class="mb-4 text-lg font-semibold text-gray-900 dark:text-white"
              >
                Trends by WCAG Criterion
              </h3>
              <div
                class="grid gap-4 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4"
              >
                <CriterionTrendChart
                  v-for="criterion in trends.criterion_trends"
                  :key="criterion.criterion_id"
                  :criterion="criterion"
                  :snapshots="currentSeries.snapshots || []"
                />
              </div>
            </div>

            <!-- Evaluation History Table -->
            <div class="mt-8">
              <h3
                class="mb-4 text-lg font-semibold text-gray-900 dark:text-white"
              >
                Evaluation History
              </h3>
              <div
                class="overflow-hidden rounded-lg border border-gray-200 dark:border-gray-700"
              >
                <table
                  class="min-w-full divide-y divide-gray-200 dark:divide-gray-700"
                >
                  <thead class="bg-gray-50 dark:bg-gray-800">
                    <tr>
                      <th
                        scope="col"
                        class="px-4 py-3 text-left text-sm font-semibold text-gray-900 dark:text-white"
                      >
                        Date
                      </th>
                      <th
                        scope="col"
                        class="px-4 py-3 text-left text-sm font-semibold text-gray-900 dark:text-white"
                      >
                        Total Findings
                      </th>
                      <th
                        scope="col"
                        class="px-4 py-3 text-left text-sm font-semibold text-gray-900 dark:text-white"
                      >
                        Critical
                      </th>
                      <th
                        scope="col"
                        class="px-4 py-3 text-left text-sm font-semibold text-gray-900 dark:text-white"
                      >
                        Serious
                      </th>
                      <th
                        scope="col"
                        class="px-4 py-3 text-left text-sm font-semibold text-gray-900 dark:text-white"
                      >
                        Verdict
                      </th>
                      <th
                        scope="col"
                        class="px-4 py-3 text-left text-sm font-semibold text-gray-900 dark:text-white"
                      >
                        Actions
                      </th>
                    </tr>
                  </thead>
                  <tbody
                    class="divide-y divide-gray-200 bg-white dark:divide-gray-700 dark:bg-gray-900"
                  >
                    <tr
                      v-for="snapshot in sortedSnapshots"
                      :key="snapshot.id"
                      class="hover:bg-gray-50 dark:hover:bg-gray-800"
                    >
                      <td
                        class="whitespace-nowrap px-4 py-3 text-sm text-gray-900 dark:text-white"
                      >
                        {{ formatDate(snapshot.snapshot_date) }}
                      </td>
                      <td
                        class="whitespace-nowrap px-4 py-3 text-sm text-gray-700 dark:text-gray-300"
                      >
                        {{ snapshot.total_findings }}
                      </td>
                      <td class="whitespace-nowrap px-4 py-3 text-sm">
                        <span
                          v-if="snapshot.findings_by_severity?.critical > 0"
                          class="font-medium text-red-600 dark:text-red-400"
                        >
                          {{ snapshot.findings_by_severity.critical }}
                        </span>
                        <span v-else class="text-gray-400">0</span>
                      </td>
                      <td class="whitespace-nowrap px-4 py-3 text-sm">
                        <span
                          v-if="snapshot.findings_by_severity?.serious > 0"
                          class="font-medium text-orange-600 dark:text-orange-400"
                        >
                          {{ snapshot.findings_by_severity.serious }}
                        </span>
                        <span v-else class="text-gray-400">0</span>
                      </td>
                      <td class="whitespace-nowrap px-4 py-3 text-sm">
                        <span
                          :class="verdictClasses(snapshot.conformance_verdict)"
                          class="rounded-full px-2 py-1 text-xs font-medium"
                        >
                          {{ snapshot.conformance_verdict || 'N/A' }}
                        </span>
                      </td>
                      <td class="whitespace-nowrap px-4 py-3 text-sm">
                        <router-link
                          :to="`/evaluations/${snapshot.evaluation_id}`"
                          class="text-blue-600 hover:underline dark:text-blue-400"
                        >
                          View Evaluation
                        </router-link>
                      </td>
                    </tr>
                  </tbody>
                </table>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- Rename Modal -->
    <Teleport to="body">
      <div
        v-if="showRenameModal"
        class="fixed inset-0 z-50 flex items-center justify-center bg-black/50"
        @click.self="showRenameModal = false"
      >
        <div
          class="w-full max-w-md rounded-lg bg-white p-6 shadow-xl dark:bg-gray-800"
        >
          <h3 class="mb-4 text-lg font-semibold text-gray-900 dark:text-white">
            Rename Series
          </h3>
          <input
            v-model="newSeriesName"
            type="text"
            class="w-full rounded-lg border border-gray-300 px-3 py-2 focus:border-blue-500 focus:outline-none focus:ring-1 focus:ring-blue-500 dark:border-gray-600 dark:bg-gray-700 dark:text-white"
            placeholder="Enter display name"
            @keyup.enter="saveName"
          />
          <div class="mt-4 flex justify-end gap-3">
            <button
              class="rounded-lg border border-gray-300 px-4 py-2 text-gray-700 hover:bg-gray-50 dark:border-gray-600 dark:text-gray-300 dark:hover:bg-gray-700"
              @click="showRenameModal = false"
            >
              Cancel
            </button>
            <button
              class="rounded-lg bg-blue-600 px-4 py-2 text-white hover:bg-blue-700"
              :disabled="!newSeriesName.trim()"
              @click="saveName"
            >
              Save
            </button>
          </div>
        </div>
      </div>
    </Teleport>
  </div>
</template>

<script setup>
import CriterionTrendChart from '@/components/longitudinal/CriterionTrendChart.vue'
import LongitudinalHelpPanel from '@/components/longitudinal/LongitudinalHelpPanel.vue'
import RegressionAlert from '@/components/longitudinal/RegressionAlert.vue'
import TotalFindingsChart from '@/components/longitudinal/TotalFindingsChart.vue'
import TrendSummaryCards from '@/components/longitudinal/TrendSummaryCards.vue'
import VerdictHistoryChart from '@/components/longitudinal/VerdictHistoryChart.vue'
import { useLongitudinalStore } from '@/stores/longitudinal'
import { computed, onMounted, ref, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'

const route = useRoute()
const router = useRouter()
const store = useLongitudinalStore()

const loading = ref(true)
const error = ref(null)
const selectedSeriesId = ref(null)
const showRenameModal = ref(false)
const newSeriesName = ref('')

const allSeries = computed(() => store.allSeries)
const currentSeries = computed(() => store.currentSeries)
const trends = computed(() => store.trends)

const sortedSnapshots = computed(() => {
  if (!currentSeries.value?.snapshots) return []
  return [...currentSeries.value.snapshots].sort(
    (a, b) => new Date(b.snapshot_date) - new Date(a.snapshot_date),
  )
})

async function loadData() {
  loading.value = true
  error.value = null
  try {
    await store.fetchAllSeries()
    const seriesIdFromRoute = route.query.series
    if (seriesIdFromRoute) {
      selectedSeriesId.value = seriesIdFromRoute
    }
  } catch (err) {
    error.value = err.message || 'Failed to load series data'
  } finally {
    loading.value = false
  }
}

async function selectSeries(id) {
  selectedSeriesId.value = id
  router.replace({ query: { series: id } })
  try {
    await Promise.all([store.fetchSeries(id), store.fetchTrends(id)])
  } catch (err) {
    error.value = err.message || 'Failed to load series details'
  }
}

watch(selectedSeriesId, async (newId) => {
  if (newId) {
    try {
      await Promise.all([store.fetchSeries(newId), store.fetchTrends(newId)])
    } catch (err) {
      error.value = err.message || 'Failed to load series details'
    }
  } else {
    router.replace({ query: {} })
  }
})

async function saveName() {
  if (!newSeriesName.value.trim() || !selectedSeriesId.value) return
  try {
    await store.updateSeriesName(
      selectedSeriesId.value,
      newSeriesName.value.trim(),
    )
    showRenameModal.value = false
    newSeriesName.value = ''
  } catch (err) {
    error.value = err.message || 'Failed to rename series'
  }
}

function formatDate(dateString) {
  if (!dateString) return 'N/A'
  const date = new Date(dateString)
  return date.toLocaleDateString('en-GB', {
    day: 'numeric',
    month: 'short',
    year: 'numeric',
  })
}

function verdictClasses(verdict) {
  switch (verdict?.toLowerCase()) {
    case 'passed':
    case 'pass':
      return 'bg-green-100 text-green-800 dark:bg-green-900/40 dark:text-green-300'
    case 'failed':
    case 'fail':
      return 'bg-red-100 text-red-800 dark:bg-red-900/40 dark:text-red-300'
    case 'inapplicable':
      return 'bg-gray-100 text-gray-800 dark:bg-gray-700 dark:text-gray-300'
    default:
      return 'bg-yellow-100 text-yellow-800 dark:bg-yellow-900/40 dark:text-yellow-300'
  }
}

onMounted(loadData)
</script>
