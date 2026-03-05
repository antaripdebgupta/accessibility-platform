<template>
  <div class="min-h-screen bg-gray-50">
    <!-- Navigation -->
    <nav class="border-b border-gray-200 bg-white">
      <div class="mx-auto max-w-7xl px-4 sm:px-6 lg:px-8">
        <div class="flex h-16 items-center">
          <RouterLink
            to="/dashboard"
            class="flex items-center text-gray-500 hover:text-gray-700"
          >
            <svg
              class="mr-2 h-5 w-5"
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
            Back to Dashboard
          </RouterLink>
        </div>
      </div>
    </nav>

    <!-- Loading State -->
    <div
      v-if="evaluationsStore.loading"
      class="flex items-center justify-center py-24"
    >
      <LoadingSpinner size="lg" />
    </div>

    <!-- Error State -->
    <div v-else-if="error" class="mx-auto max-w-2xl px-4 py-16 sm:px-6 lg:px-8">
      <div class="rounded-lg border border-red-200 bg-red-50 p-6 text-center">
        <svg
          class="mx-auto h-12 w-12 text-red-400"
          fill="none"
          stroke="currentColor"
          viewBox="0 0 24 24"
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

    <!-- Evaluation Detail -->
    <main v-else-if="evaluation" class="py-8">
      <div class="mx-auto max-w-4xl px-4 sm:px-6 lg:px-8">
        <!-- Header -->
        <div class="mb-8">
          <div class="flex items-start justify-between">
            <div>
              <h1 class="text-2xl font-bold text-gray-900">
                {{ evaluation.title }}
              </h1>
              <a
                :href="evaluation.target_url"
                target="_blank"
                rel="noopener noreferrer"
                class="mt-1 inline-flex items-center text-sm text-indigo-600 hover:text-indigo-800"
              >
                {{ evaluation.target_url }}
                <svg
                  class="ml-1 h-4 w-4"
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
            <StatusBadge :status="evaluation.status" />
          </div>

          <!-- Meta information -->
          <div
            class="mt-4 flex flex-wrap items-center gap-4 text-sm text-gray-500"
          >
            <span class="inline-flex items-center">
              <svg
                class="mr-1.5 h-4 w-4 text-gray-400"
                fill="none"
                stroke="currentColor"
                viewBox="0 0 24 24"
              >
                <path
                  stroke-linecap="round"
                  stroke-linejoin="round"
                  stroke-width="2"
                  d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z"
                />
              </svg>
              WCAG {{ evaluation.wcag_version }} Level
              {{ evaluation.conformance_level }}
            </span>
            <span class="inline-flex items-center">
              <svg
                class="mr-1.5 h-4 w-4 text-gray-400"
                fill="none"
                stroke="currentColor"
                viewBox="0 0 24 24"
              >
                <path
                  stroke-linecap="round"
                  stroke-linejoin="round"
                  stroke-width="2"
                  d="M8 7V3m8 4V3m-9 8h10M5 21h14a2 2 0 002-2V7a2 2 0 00-2-2H5a2 2 0 00-2 2v12a2 2 0 002 2z"
                />
              </svg>
              Created {{ formattedDate }}
            </span>
          </div>
        </div>

        <!-- Workflow Steps -->
        <div class="mb-8 rounded-lg border border-gray-200 bg-white p-6">
          <h2 class="mb-4 text-lg font-medium text-gray-900">
            Evaluation Progress
          </h2>

          <nav aria-label="Progress">
            <ol class="flex items-center">
              <li
                v-for="(step, index) in workflowSteps"
                :key="step.name"
                :class="[
                  index !== workflowSteps.length - 1 ? 'flex-1' : '',
                  'relative',
                ]"
              >
                <div class="flex items-center">
                  <span
                    :class="[
                      'flex h-10 w-10 items-center justify-center rounded-full border-2',
                      step.status === 'current'
                        ? 'border-indigo-600 bg-indigo-600 text-white'
                        : step.status === 'complete'
                          ? 'border-indigo-600 bg-indigo-600 text-white'
                          : 'border-gray-300 bg-white text-gray-500',
                    ]"
                  >
                    <svg
                      v-if="step.status === 'complete'"
                      class="h-5 w-5"
                      fill="currentColor"
                      viewBox="0 0 20 20"
                    >
                      <path
                        fill-rule="evenodd"
                        d="M16.707 5.293a1 1 0 010 1.414l-8 8a1 1 0 01-1.414 0l-4-4a1 1 0 011.414-1.414L8 12.586l7.293-7.293a1 1 0 011.414 0z"
                        clip-rule="evenodd"
                      />
                    </svg>
                    <span v-else>{{ index + 1 }}</span>
                  </span>
                  <span
                    v-if="index !== workflowSteps.length - 1"
                    class="ml-4 flex-1 border-t-2"
                    :class="[
                      step.status === 'complete'
                        ? 'border-indigo-600'
                        : 'border-gray-300',
                    ]"
                  ></span>
                </div>
                <span
                  :class="[
                    'absolute -bottom-6 left-0 text-xs font-medium',
                    step.status === 'current'
                      ? 'text-indigo-600'
                      : 'text-gray-500',
                  ]"
                >
                  {{ step.name }}
                </span>
              </li>
            </ol>
          </nav>
        </div>

        <!-- Actions Card -->
        <div class="rounded-lg border border-gray-200 bg-white p-6">
          <h2 class="mb-4 text-lg font-medium text-gray-900">Next Steps</h2>

          <div class="space-y-4">
            <div
              class="flex items-center justify-between rounded-lg border border-gray-200 bg-gray-50 p-4"
            >
              <div>
                <h3 class="font-medium text-gray-900">Start Exploration</h3>
                <p class="mt-1 text-sm text-gray-500">
                  Crawl the website to discover pages for evaluation
                </p>
              </div>
              <div class="relative">
                <button
                  disabled
                  class="inline-flex cursor-not-allowed items-center rounded-md bg-gray-300 px-4 py-2 text-sm font-medium text-gray-500"
                  title="Coming soon"
                >
                  Start Exploration
                </button>
                <span
                  class="absolute -right-2 -top-2 inline-flex items-center rounded-full bg-amber-100 px-2 py-0.5 text-xs font-medium text-amber-800"
                >
                  Coming soon
                </span>
              </div>
            </div>

            <div
              class="flex items-center justify-between rounded-lg border border-dashed border-gray-300 p-4"
            >
              <div>
                <h3 class="font-medium text-gray-400">Run Automated Scan</h3>
                <p class="mt-1 text-sm text-gray-400">
                  Scan selected pages with axe-core and pa11y
                </p>
              </div>
              <span class="text-sm text-gray-400">Locked</span>
            </div>

            <div
              class="flex items-center justify-between rounded-lg border border-dashed border-gray-300 p-4"
            >
              <div>
                <h3 class="font-medium text-gray-400">Review Findings</h3>
                <p class="mt-1 text-sm text-gray-400">
                  Manually review and confirm accessibility issues
                </p>
              </div>
              <span class="text-sm text-gray-400">Locked</span>
            </div>

            <div
              class="flex items-center justify-between rounded-lg border border-dashed border-gray-300 p-4"
            >
              <div>
                <h3 class="font-medium text-gray-400">Generate Report</h3>
                <p class="mt-1 text-sm text-gray-400">
                  Create accessibility conformance report
                </p>
              </div>
              <span class="text-sm text-gray-400">Locked</span>
            </div>
          </div>
        </div>
      </div>
    </main>
  </div>
</template>

<script setup>
import { computed, onMounted, ref } from 'vue'
import { RouterLink, useRoute } from 'vue-router'
import LoadingSpinner from '../components/common/LoadingSpinner.vue'
import StatusBadge from '../components/common/StatusBadge.vue'
import { useEvaluationsStore } from '../stores/evaluations'

const route = useRoute()
const evaluationsStore = useEvaluationsStore()

const error = ref('')

const evaluation = computed(() => evaluationsStore.current)

const formattedDate = computed(() => {
  if (!evaluation.value?.created_at) return ''

  const date = new Date(evaluation.value.created_at)
  return date.toLocaleDateString('en-US', {
    month: 'long',
    day: 'numeric',
    year: 'numeric',
  })
})

const workflowSteps = computed(() => {
  const status = evaluation.value?.status || 'DRAFT'

  const steps = [
    { name: 'Explore', status: 'upcoming' },
    { name: 'Scan', status: 'upcoming' },
    { name: 'Review', status: 'upcoming' },
    { name: 'Report', status: 'upcoming' },
  ]

  // Determine step statuses based on evaluation status
  const statusIndex = {
    DRAFT: 0,
    SCOPING: 0,
    EXPLORING: 0,
    SAMPLING: 1,
    AUDITING: 2,
    REPORTING: 3,
    COMPLETE: 4,
  }

  const currentIndex = statusIndex[status] ?? 0

  steps.forEach((step, index) => {
    if (index < currentIndex) {
      step.status = 'complete'
    } else if (index === currentIndex) {
      step.status = 'current'
    }
  })

  return steps
})

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
