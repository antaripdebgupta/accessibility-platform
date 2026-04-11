<template>
  <div
    v-if="hasIssues"
    class="rounded-lg border border-red-300 bg-red-50 p-4 dark:border-red-700 dark:bg-red-900/20"
  >
    <div class="flex items-start gap-3">
      <div class="flex-shrink-0">
        <svg
          class="h-6 w-6 text-red-600 dark:text-red-400"
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
      </div>
      <div class="flex-1">
        <h3 class="text-lg font-semibold text-red-800 dark:text-red-200">
          Attention Required
        </h3>
        <p class="mt-1 text-sm text-red-700 dark:text-red-300">
          {{ summaryText }}
        </p>

        <!-- Regressions Section -->
        <div v-if="regressions.length > 0" class="mt-4">
          <h4 class="text-sm font-medium text-red-800 dark:text-red-200">
            Regressions ({{ regressions.length }})
          </h4>
          <ul class="mt-2 space-y-2">
            <li
              v-for="item in regressions"
              :key="item.criterion_id"
              class="flex items-center justify-between rounded bg-red-100 px-3 py-2 text-sm dark:bg-red-900/40"
            >
              <div class="flex items-center gap-2">
                <span class="font-mono text-red-900 dark:text-red-100">
                  {{ item.criterion_id }}
                </span>
                <span class="text-red-700 dark:text-red-300">
                  {{ item.criterion_name || 'Unknown Criterion' }}
                </span>
                <span
                  v-if="item.level"
                  class="rounded bg-red-200 px-1.5 py-0.5 text-xs font-medium text-red-800 dark:bg-red-800 dark:text-red-100"
                >
                  Level {{ item.level }}
                </span>
              </div>
              <div
                class="flex items-center gap-1 font-medium text-red-700 dark:text-red-300"
              >
                <svg
                  class="h-4 w-4"
                  fill="none"
                  stroke="currentColor"
                  viewBox="0 0 24 24"
                  aria-hidden="true"
                >
                  <path
                    stroke-linecap="round"
                    stroke-linejoin="round"
                    stroke-width="2"
                    d="M5 15l7-7 7 7"
                  />
                </svg>
                <span>+{{ item.change }}</span>
              </div>
            </li>
          </ul>
        </div>

        <!-- New Failures Section -->
        <div v-if="newFailures.length > 0" class="mt-4">
          <h4 class="text-sm font-medium text-red-800 dark:text-red-200">
            New Failures ({{ newFailures.length }})
          </h4>
          <ul class="mt-2 space-y-2">
            <li
              v-for="item in newFailures"
              :key="item.criterion_id"
              class="flex items-center justify-between rounded bg-orange-100 px-3 py-2 text-sm dark:bg-orange-900/40"
            >
              <div class="flex items-center gap-2">
                <span
                  class="rounded bg-orange-200 px-1.5 py-0.5 text-xs font-medium text-orange-800 dark:bg-orange-800 dark:text-orange-100"
                >
                  NEW
                </span>
                <span class="font-mono text-orange-900 dark:text-orange-100">
                  {{ item.criterion_id }}
                </span>
                <span class="text-orange-700 dark:text-orange-300">
                  {{ item.criterion_name || 'Unknown Criterion' }}
                </span>
                <span
                  v-if="item.level"
                  class="rounded bg-orange-200 px-1.5 py-0.5 text-xs font-medium text-orange-800 dark:bg-orange-800 dark:text-orange-100"
                >
                  Level {{ item.level }}
                </span>
              </div>
              <div class="font-medium text-orange-700 dark:text-orange-300">
                {{ item.latest_count }} issue{{
                  item.latest_count !== 1 ? 's' : ''
                }}
              </div>
            </li>
          </ul>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { computed } from 'vue'

const props = defineProps({
  regressions: {
    type: Array,
    default: () => [],
  },
  newFailures: {
    type: Array,
    default: () => [],
  },
})

const hasIssues = computed(() => {
  return props.regressions.length > 0 || props.newFailures.length > 0
})

const summaryText = computed(() => {
  const parts = []
  if (props.regressions.length > 0) {
    parts.push(
      `${props.regressions.length} criterion${props.regressions.length !== 1 ? 'criteria' : ''} regressed`,
    )
  }
  if (props.newFailures.length > 0) {
    parts.push(
      `${props.newFailures.length} new failure${props.newFailures.length !== 1 ? 's' : ''} detected`,
    )
  }
  return parts.join(' and ') + ' compared to the previous evaluation.'
})
</script>
