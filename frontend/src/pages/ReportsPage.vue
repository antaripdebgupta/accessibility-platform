<template>
  <AppLayout>
    <!-- Loading State -->
    <div
      v-if="evaluationsStore.loading && !evaluation"
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
          class="mt-4 inline-flex items-center rounded-md bg-red-100 px-4 py-2 text-sm font-medium text-red-700 hover:bg-red-200"
        >
          Return to Dashboard
        </RouterLink>
      </div>
    </div>

    <!-- Main Content -->
    <template v-else-if="evaluation">
      <!-- Page Header -->
      <PageHeader
        title="Conformance Report"
        :subtitle="evaluation.title"
        :back-to="{ name: 'EvaluationDetail', params: { id: evaluationId } }"
      >
        <StatusBadge :status="evaluation.status" />
      </PageHeader>

      <!-- State A: Not Ready -->
      <div
        v-if="!isReadyToGenerate && !reportsStore.hasReports"
        class="rounded-lg border border-yellow-200 bg-yellow-50 p-8"
      >
        <div class="text-center">
          <svg
            class="mx-auto h-16 w-16 text-yellow-500"
            fill="none"
            stroke="currentColor"
            viewBox="0 0 24 24"
            aria-hidden="true"
          >
            <path
              stroke-linecap="round"
              stroke-linejoin="round"
              stroke-width="1.5"
              d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z"
            />
          </svg>
          <h3 class="mt-4 text-xl font-semibold text-yellow-800">
            Evaluation Not Ready
          </h3>
          <p class="mx-auto mt-2 max-w-md text-sm text-yellow-700">
            Complete the scan and review your findings before generating a
            report. Current status: {{ evaluation.status }}
          </p>
          <div class="mt-6 flex items-center justify-center space-x-4">
            <RouterLink
              :to="`/evaluations/${evaluationId}/findings`"
              class="inline-flex items-center rounded-md bg-yellow-600 px-4 py-2 text-sm font-semibold text-white hover:bg-yellow-500"
            >
              Go to Findings →
            </RouterLink>
            <RouterLink
              :to="`/evaluations/${evaluationId}/explore`"
              class="inline-flex items-center rounded-md border border-yellow-600 bg-white px-4 py-2 text-sm font-semibold text-yellow-700 hover:bg-yellow-50"
            >
              Go to Scan →
            </RouterLink>
          </div>
        </div>
      </div>

      <!-- State B: Ready to Generate -->
      <div
        v-else-if="isReadyToGenerate && !reportsStore.hasReports && !generating"
        class="space-y-6"
      >
        <div class="rounded-lg border border-gray-200 bg-white p-8">
          <div class="text-center">
            <!-- Status Badge -->
            <div
              class="mb-4 inline-flex items-center rounded-full bg-green-100 px-4 py-1.5"
            >
              <svg
                class="mr-1.5 h-4 w-4 text-green-600"
                fill="none"
                stroke="currentColor"
                viewBox="0 0 24 24"
                aria-hidden="true"
              >
                <path
                  stroke-linecap="round"
                  stroke-linejoin="round"
                  stroke-width="2"
                  d="M5 13l4 4L19 7"
                />
              </svg>
              <span class="text-sm font-medium text-green-700"
                >Ready to Generate</span
              >
            </div>

            <!-- Icon -->
            <svg
              class="mx-auto h-16 w-16 text-gray-400"
              fill="none"
              stroke="currentColor"
              viewBox="0 0 24 24"
              aria-hidden="true"
            >
              <path
                stroke-linecap="round"
                stroke-linejoin="round"
                stroke-width="1.5"
                d="M9 17v-2m3 2v-4m3 4v-6m2 10H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z"
              />
            </svg>

            <h3 class="mt-4 text-lg font-medium text-gray-900">
              WCAG Conformance Reports
            </h3>
            <p class="mx-auto mt-2 max-w-md text-sm text-gray-500">
              Generate comprehensive accessibility conformance reports in
              multiple formats.
            </p>

            <!-- Checklist -->
            <div class="mx-auto mt-6 max-w-sm">
              <ul class="space-y-2 text-left text-sm">
                <li class="flex items-center text-green-600">
                  <svg
                    class="mr-2 h-4 w-4"
                    fill="none"
                    stroke="currentColor"
                    viewBox="0 0 24 24"
                  >
                    <path
                      stroke-linecap="round"
                      stroke-linejoin="round"
                      stroke-width="2"
                      d="M5 13l4 4L19 7"
                    />
                  </svg>
                  Pages crawled
                </li>
                <li class="flex items-center text-green-600">
                  <svg
                    class="mr-2 h-4 w-4"
                    fill="none"
                    stroke="currentColor"
                    viewBox="0 0 24 24"
                  >
                    <path
                      stroke-linecap="round"
                      stroke-linejoin="round"
                      stroke-width="2"
                      d="M5 13l4 4L19 7"
                    />
                  </svg>
                  Automated scan complete
                </li>
                <li class="flex items-center text-green-600">
                  <svg
                    class="mr-2 h-4 w-4"
                    fill="none"
                    stroke="currentColor"
                    viewBox="0 0 24 24"
                  >
                    <path
                      stroke-linecap="round"
                      stroke-linejoin="round"
                      stroke-width="2"
                      d="M5 13l4 4L19 7"
                    />
                  </svg>
                  Findings reviewed
                </li>
                <li class="flex items-center text-gray-500">
                  <svg
                    class="mr-2 h-4 w-4"
                    fill="none"
                    stroke="currentColor"
                    viewBox="0 0 24 24"
                  >
                    <path
                      stroke-linecap="round"
                      stroke-linejoin="round"
                      stroke-width="2"
                      d="M13 5l7 7-7 7M5 5l7 7-7 7"
                    />
                  </svg>
                  Report not yet generated
                </li>
              </ul>
            </div>

            <!-- Generate Button -->
            <button
              v-if="canGenerateReport"
              type="button"
              class="mt-8 inline-flex items-center rounded-md bg-indigo-600 px-6 py-3 text-base font-semibold text-white shadow-sm hover:bg-indigo-500 focus:outline-none focus:ring-2 focus:ring-indigo-500 focus:ring-offset-2"
              @click="startGeneration"
            >
              Generate Report →
            </button>
            <p v-else class="mt-8 text-sm text-gray-500">
              You don't have permission to generate reports. Contact an auditor
              or owner.
            </p>

            <!-- Options Toggle -->
            <div class="mt-6">
              <button
                type="button"
                class="text-sm text-indigo-600 hover:text-indigo-500"
                @click="showOptions = !showOptions"
              >
                {{ showOptions ? 'Hide options' : 'Show options' }}
              </button>

              <div v-if="showOptions" class="mx-auto mt-4 max-w-sm text-left">
                <div class="space-y-3 rounded-lg bg-gray-50 p-4">
                  <label class="flex items-center">
                    <input
                      v-model="reportTypeOptions.full"
                      type="checkbox"
                      class="h-4 w-4 rounded border-gray-300 text-indigo-600 focus:ring-indigo-500"
                    />
                    <span class="ml-2 text-sm text-gray-700"
                      >Full PDF Report</span
                    >
                  </label>
                  <label class="flex items-center">
                    <input
                      v-model="reportTypeOptions.earl"
                      type="checkbox"
                      class="h-4 w-4 rounded border-gray-300 text-indigo-600 focus:ring-indigo-500"
                    />
                    <span class="ml-2 text-sm text-gray-700">EARL JSON-LD</span>
                  </label>
                  <label class="flex items-center">
                    <input
                      v-model="reportTypeOptions.csv"
                      type="checkbox"
                      class="h-4 w-4 rounded border-gray-300 text-indigo-600 focus:ring-indigo-500"
                    />
                    <span class="ml-2 text-sm text-gray-700">CSV Export</span>
                  </label>
                  <hr class="my-2" />
                  <label class="flex items-center">
                    <input
                      v-model="includeDismissed"
                      type="checkbox"
                      class="h-4 w-4 rounded border-gray-300 text-indigo-600 focus:ring-indigo-500"
                    />
                    <span class="ml-2 text-sm text-gray-700"
                      >Include dismissed findings</span
                    >
                  </label>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>

      <!-- State C: Generation in Progress -->
      <div v-else-if="generating" class="space-y-6">
        <div class="rounded-lg border border-indigo-200 bg-indigo-50 p-8">
          <div class="text-center">
            <LoadingSpinner size="lg" />

            <h3 class="mt-4 text-lg font-medium text-indigo-900">
              Generating your report...
            </h3>

            <!-- Progress Steps -->
            <div class="mx-auto mt-6 max-w-sm text-left">
              <ul class="space-y-3">
                <li
                  :class="[
                    'flex items-center transition-colors',
                    reportProgress.step >= 1
                      ? 'text-indigo-700'
                      : 'text-gray-400',
                  ]"
                >
                  <svg
                    v-if="reportProgress.step > 1"
                    class="mr-2 h-5 w-5 text-green-500"
                    fill="none"
                    stroke="currentColor"
                    viewBox="0 0 24 24"
                  >
                    <path
                      stroke-linecap="round"
                      stroke-linejoin="round"
                      stroke-width="2"
                      d="M5 13l4 4L19 7"
                    />
                  </svg>
                  <LoadingSpinner
                    v-else-if="reportProgress.step === 1"
                    size="sm"
                  />
                  <span v-else class="mr-2 h-5 w-5"></span>
                  <span>Computing conformance verdict...</span>
                </li>
                <li
                  :class="[
                    'flex items-center transition-colors',
                    reportProgress.step >= 2
                      ? 'text-indigo-700'
                      : 'text-gray-400',
                  ]"
                >
                  <svg
                    v-if="reportProgress.step > 2"
                    class="mr-2 h-5 w-5 text-green-500"
                    fill="none"
                    stroke="currentColor"
                    viewBox="0 0 24 24"
                  >
                    <path
                      stroke-linecap="round"
                      stroke-linejoin="round"
                      stroke-width="2"
                      d="M5 13l4 4L19 7"
                    />
                  </svg>
                  <LoadingSpinner
                    v-else-if="reportProgress.step === 2"
                    size="sm"
                  />
                  <span v-else class="mr-2 h-5 w-5"></span>
                  <span>Generating Full Report...</span>
                </li>
                <li
                  :class="[
                    'flex items-center transition-colors',
                    reportProgress.step >= 3
                      ? 'text-indigo-700'
                      : 'text-gray-400',
                  ]"
                >
                  <svg
                    v-if="reportProgress.step > 3"
                    class="mr-2 h-5 w-5 text-green-500"
                    fill="none"
                    stroke="currentColor"
                    viewBox="0 0 24 24"
                  >
                    <path
                      stroke-linecap="round"
                      stroke-linejoin="round"
                      stroke-width="2"
                      d="M5 13l4 4L19 7"
                    />
                  </svg>
                  <LoadingSpinner
                    v-else-if="reportProgress.step === 3"
                    size="sm"
                  />
                  <span v-else class="mr-2 h-5 w-5"></span>
                  <span>Generating EARL export...</span>
                </li>
                <li
                  :class="[
                    'flex items-center transition-colors',
                    reportProgress.step >= 4
                      ? 'text-indigo-700'
                      : 'text-gray-400',
                  ]"
                >
                  <svg
                    v-if="reportProgress.step > 4"
                    class="mr-2 h-5 w-5 text-green-500"
                    fill="none"
                    stroke="currentColor"
                    viewBox="0 0 24 24"
                  >
                    <path
                      stroke-linecap="round"
                      stroke-linejoin="round"
                      stroke-width="2"
                      d="M5 13l4 4L19 7"
                    />
                  </svg>
                  <LoadingSpinner
                    v-else-if="reportProgress.step === 4"
                    size="sm"
                  />
                  <span v-else class="mr-2 h-5 w-5"></span>
                  <span>Generating CSV export...</span>
                </li>
              </ul>
            </div>

            <p class="mt-6 text-sm text-indigo-600">
              {{
                reportProgress.message || 'This usually takes 15–30 seconds.'
              }}
            </p>
          </div>
        </div>
      </div>

      <!-- State D: Reports Exist -->
      <div v-else-if="reportsStore.hasReports" class="space-y-8">
        <!-- Verdict Banner -->
        <VerdictBanner
          v-if="latestReport"
          :verdict="latestReport.conformance_verdict || 'CANNOT_DETERMINE'"
          :criteria-failed="latestReport.criteria_failed || 0"
          :criteria-total="
            (latestReport.criteria_passed || 0) +
            (latestReport.criteria_failed || 0)
          "
        />

        <!-- Report Stats -->
        <ReportStats
          v-if="latestReport"
          :pages-scanned="findingsStats.pagesScanned"
          :total-findings="latestReport.total_findings || 0"
          :criteria-failed="latestReport.criteria_failed || 0"
          :criteria-passed="latestReport.criteria_passed || 0"
        />

        <!-- Download Reports Section -->
        <div>
          <h2 class="mb-4 text-lg font-semibold text-gray-900">
            Download Reports
          </h2>
          <div class="space-y-4">
            <ReportCard
              v-for="report in reportsStore.reports"
              :key="report.id"
              :report="report"
            />
          </div>
        </div>

        <!-- Failed Criteria List -->
        <div v-if="failedCriteria.length > 0">
          <h2 class="mb-4 text-lg font-semibold text-gray-900">
            Failed Criteria Details
          </h2>
          <FailedCriteriaList :failed-criteria="failedCriteria" />
        </div>

        <!-- Generate New Report Button -->
        <div v-if="canGenerateReport" class="border-t border-gray-200 pt-6">
          <button
            type="button"
            class="inline-flex items-center rounded-md border border-gray-300 bg-white px-4 py-2 text-sm font-medium text-gray-700 shadow-sm hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-indigo-500 focus:ring-offset-2"
            @click="showRegenerateModal = true"
          >
            <svg
              class="-ml-0.5 mr-2 h-4 w-4"
              fill="none"
              stroke="currentColor"
              viewBox="0 0 24 24"
            >
              <path
                stroke-linecap="round"
                stroke-linejoin="round"
                stroke-width="2"
                d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15"
              />
            </svg>
            Generate New Report
          </button>
        </div>
      </div>
    </template>

    <!-- Regenerate Report Modal -->
    <div
      v-if="showRegenerateModal"
      class="fixed inset-0 z-50 overflow-y-auto"
      aria-labelledby="modal-title"
      role="dialog"
      aria-modal="true"
    >
      <div class="flex min-h-full items-center justify-center p-4">
        <!-- Backdrop -->
        <div
          class="fixed inset-0 bg-gray-500 bg-opacity-75 transition-opacity"
          @click="showRegenerateModal = false"
        ></div>

        <!-- Modal Panel -->
        <div
          class="relative w-full max-w-md transform rounded-lg bg-white p-6 shadow-xl transition-all"
        >
          <h3 class="text-lg font-semibold text-gray-900" id="modal-title">
            Generate New Report
          </h3>
          <p class="mt-2 text-sm text-gray-500">
            Select the report formats to generate:
          </p>

          <div class="mt-4 space-y-3">
            <label class="flex items-center">
              <input
                v-model="reportTypeOptions.full"
                type="checkbox"
                class="h-4 w-4 rounded border-gray-300 text-indigo-600 focus:ring-indigo-500"
              />
              <span class="ml-2 text-sm text-gray-700">Full PDF Report</span>
            </label>
            <label class="flex items-center">
              <input
                v-model="reportTypeOptions.earl"
                type="checkbox"
                class="h-4 w-4 rounded border-gray-300 text-indigo-600 focus:ring-indigo-500"
              />
              <span class="ml-2 text-sm text-gray-700">EARL JSON-LD</span>
            </label>
            <label class="flex items-center">
              <input
                v-model="reportTypeOptions.csv"
                type="checkbox"
                class="h-4 w-4 rounded border-gray-300 text-indigo-600 focus:ring-indigo-500"
              />
              <span class="ml-2 text-sm text-gray-700">CSV Export</span>
            </label>
            <hr class="my-2" />
            <label class="flex items-center">
              <input
                v-model="includeDismissed"
                type="checkbox"
                class="h-4 w-4 rounded border-gray-300 text-indigo-600 focus:ring-indigo-500"
              />
              <span class="ml-2 text-sm text-gray-700"
                >Include dismissed findings</span
              >
            </label>
          </div>

          <div class="mt-6 flex justify-end space-x-3">
            <button
              type="button"
              class="rounded-md border border-gray-300 bg-white px-4 py-2 text-sm font-medium text-gray-700 hover:bg-gray-50"
              @click="showRegenerateModal = false"
            >
              Cancel
            </button>
            <button
              type="button"
              class="rounded-md bg-indigo-600 px-4 py-2 text-sm font-medium text-white hover:bg-indigo-500"
              @click="handleRegenerate"
            >
              Generate
            </button>
          </div>
        </div>
      </div>
    </div>
  </AppLayout>
</template>

<script setup>
import { computed, onMounted, onUnmounted, reactive, ref } from 'vue'
import { RouterLink, useRoute } from 'vue-router'

import LoadingSpinner from '../components/common/LoadingSpinner.vue'
import StatusBadge from '../components/common/StatusBadge.vue'
import AppLayout from '../components/layout/AppLayout.vue'
import PageHeader from '../components/layout/PageHeader.vue'
import FailedCriteriaList from '../components/reports/FailedCriteriaList.vue'
import ReportCard from '../components/reports/ReportCard.vue'
import ReportStats from '../components/reports/ReportStats.vue'
import VerdictBanner from '../components/reports/VerdictBanner.vue'
import { usePermissions } from '../composables/usePermissions'
import api from '../lib/api'
import { useEvaluationsStore } from '../stores/evaluations'
import { useFindingsStore } from '../stores/findings'
import { useReportsStore } from '../stores/reports'
import { useTasksStore } from '../stores/tasks'

const route = useRoute()
const evaluationsStore = useEvaluationsStore()
const reportsStore = useReportsStore()
const findingsStore = useFindingsStore()
const tasksStore = useTasksStore()
const { canGenerateReport } = usePermissions()

// State
const error = ref('')
const generating = ref(false)
const showOptions = ref(false)
const showRegenerateModal = ref(false)
const currentTaskId = ref(null)
const reportTypeOptions = reactive({
  full: true,
  earl: true,
  csv: true,
})
const includeDismissed = ref(false)
const failedCriteria = ref([])
const findingsStats = reactive({
  pagesScanned: 0,
})

// Computed
const evaluationId = computed(() => route.params.id)
const evaluation = computed(() => evaluationsStore.current)

const isReadyToGenerate = computed(() => {
  if (!evaluation.value) return false
  return ['AUDITING', 'REPORTING', 'COMPLETE'].includes(evaluation.value.status)
})

const latestReport = computed(() => {
  return reportsStore.latestFullReport || reportsStore.reports[0] || null
})

// SSE-driven report generation progress
const reportProgress = computed(() => {
  if (!currentTaskId.value) {
    return { step: 1, message: 'Starting...', percent: 0 }
  }
  const progress = tasksStore.getProgress(currentTaskId.value)
  // Map SSE step names to step numbers
  const stepMap = {
    verdict_computed: 2,
    full_generated: 3,
    earl_generated: 4,
    csv_generated: 5,
  }
  const step = stepMap[progress?.step] || 1
  return {
    step,
    message: progress?.message || 'Generating report...',
    percent: progress?.percent || 10,
  }
})

// Methods
async function loadData() {
  try {
    await evaluationsStore.fetchOne(evaluationId.value)
    await reportsStore.fetchReports(evaluationId.value)

    // Fetch pages count
    try {
      const pagesResponse = await api.get(
        `/evaluations/${evaluationId.value}/pages/summary`,
      )
      findingsStats.pagesScanned = pagesResponse.data.total_pages || 0
    } catch {
      findingsStats.pagesScanned = 0
    }

    // If we have reports, try to fetch failed criteria from findings
    if (reportsStore.hasReports) {
      await loadFailedCriteria()
    }
  } catch (err) {
    error.value = err.message || 'Failed to load report data'
  }
}

async function loadFailedCriteria() {
  try {
    // Fetch confirmed findings grouped by criteria
    const response = await api.get(
      `/evaluations/${evaluationId.value}/findings?status=CONFIRMED&limit=200`,
    )

    const findings = response.data.items || []

    // Group by criterion
    const criteriaMap = new Map()

    for (const finding of findings) {
      if (finding.criterion_code) {
        if (!criteriaMap.has(finding.criterion_code)) {
          criteriaMap.set(finding.criterion_code, {
            criterion_code: finding.criterion_code,
            criterion_name: finding.criterion_name || finding.criterion_code,
            criterion_level: finding.criterion_level || 'AA',
            finding_count: 0,
            findings: [],
          })
        }

        const criterion = criteriaMap.get(finding.criterion_code)
        criterion.finding_count++
        criterion.findings.push({
          description: finding.description,
          severity: finding.severity || 'moderate',
          page_url: finding.page_url || '',
          css_selector: finding.css_selector || '',
        })
      }
    }

    // Convert to array and sort
    failedCriteria.value = Array.from(criteriaMap.values()).sort((a, b) =>
      a.criterion_code.localeCompare(b.criterion_code),
    )
  } catch (err) {
    console.error('Failed to load failed criteria:', err)
    failedCriteria.value = []
  }
}

async function startGeneration() {
  generating.value = true

  // Build report types array
  const reportTypes = []
  if (reportTypeOptions.full) reportTypes.push('full')
  if (reportTypeOptions.earl) reportTypes.push('earl')
  if (reportTypeOptions.csv) reportTypes.push('csv')

  // If nothing selected, default to all
  if (reportTypes.length === 0) {
    reportTypes.push('full', 'earl', 'csv')
  }

  try {
    const response = await reportsStore.generateReport(evaluationId.value, {
      report_types: reportTypes,
      include_dismissed: includeDismissed.value,
    })

    const taskId = response.task_id
    currentTaskId.value = taskId

    // Start polling for task completion (uses SSE with polling fallback)
    tasksStore.startPolling(
      taskId,
      async (result) => {
        // Success
        currentTaskId.value = null
        generating.value = false

        // Refresh reports
        await reportsStore.fetchReports(evaluationId.value)
        await evaluationsStore.fetchOne(evaluationId.value)
        await loadFailedCriteria()

        // Show success message
        alert(`Report generated! Verdict: ${result.verdict}`)
      },
      (errorMessage) => {
        // Error
        currentTaskId.value = null
        generating.value = false

        alert(`Report generation failed: ${errorMessage}`)
      },
    )
  } catch (err) {
    generating.value = false
    currentTaskId.value = null
    alert(`Failed to start report generation: ${err.message}`)
  }
}

function handleRegenerate() {
  showRegenerateModal.value = false
  startGeneration()
}

// Lifecycle
onMounted(async () => {
  await loadData()
})

onUnmounted(() => {
  tasksStore.stopAll()
  reportsStore.clearReports()
})
</script>
