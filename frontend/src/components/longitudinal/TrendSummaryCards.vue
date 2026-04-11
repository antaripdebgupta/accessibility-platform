<template>
  <div class="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-4">
    <!-- Total Evaluations Card -->
    <div
      class="rounded-lg border border-gray-200 bg-white p-4 shadow-sm dark:border-gray-700 dark:bg-gray-800"
    >
      <div class="flex items-center gap-3">
        <div class="rounded-lg bg-blue-100 p-2 dark:bg-blue-900/40">
          <svg
            class="h-6 w-6 text-blue-600 dark:text-blue-400"
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
        </div>
        <div>
          <p class="text-sm font-medium text-gray-500 dark:text-gray-400">
            Total Evaluations
          </p>
          <p class="text-2xl font-bold text-gray-900 dark:text-white">
            {{ totalEvaluations }}
          </p>
        </div>
      </div>
    </div>

    <!-- Net Change Card -->
    <div
      class="rounded-lg border border-gray-200 bg-white p-4 shadow-sm dark:border-gray-700 dark:bg-gray-800"
    >
      <div class="flex items-center gap-3">
        <div
          :class="[
            'rounded-lg p-2',
            netChange < 0
              ? 'bg-green-100 dark:bg-green-900/40'
              : netChange > 0
                ? 'bg-red-100 dark:bg-red-900/40'
                : 'bg-gray-100 dark:bg-gray-700',
          ]"
        >
          <svg
            v-if="netChange < 0"
            class="h-6 w-6 text-green-600 dark:text-green-400"
            fill="none"
            stroke="currentColor"
            viewBox="0 0 24 24"
            aria-hidden="true"
          >
            <path
              stroke-linecap="round"
              stroke-linejoin="round"
              stroke-width="2"
              d="M13 17h8m0 0V9m0 8l-8-8-4 4-6-6"
            />
          </svg>
          <svg
            v-else-if="netChange > 0"
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
              d="M13 7h8m0 0v8m0-8l-8 8-4-4-6 6"
            />
          </svg>
          <svg
            v-else
            class="h-6 w-6 text-gray-600 dark:text-gray-400"
            fill="none"
            stroke="currentColor"
            viewBox="0 0 24 24"
            aria-hidden="true"
          >
            <path
              stroke-linecap="round"
              stroke-linejoin="round"
              stroke-width="2"
              d="M5 12h14"
            />
          </svg>
        </div>
        <div>
          <p class="text-sm font-medium text-gray-500 dark:text-gray-400">
            Net Change
          </p>
          <p
            :class="[
              'text-2xl font-bold',
              netChange < 0
                ? 'text-green-600 dark:text-green-400'
                : netChange > 0
                  ? 'text-red-600 dark:text-red-400'
                  : 'text-gray-900 dark:text-white',
            ]"
          >
            {{ netChange > 0 ? '+' : '' }}{{ netChange }}
          </p>
        </div>
      </div>
    </div>

    <!-- Regressions Card -->
    <div
      class="rounded-lg border border-gray-200 bg-white p-4 shadow-sm dark:border-gray-700 dark:bg-gray-800"
    >
      <div class="flex items-center gap-3">
        <div
          :class="[
            'rounded-lg p-2',
            regressionsCount > 0
              ? 'bg-red-100 dark:bg-red-900/40'
              : 'bg-gray-100 dark:bg-gray-700',
          ]"
        >
          <svg
            class="h-6 w-6"
            :class="
              regressionsCount > 0
                ? 'text-red-600 dark:text-red-400'
                : 'text-gray-600 dark:text-gray-400'
            "
            fill="none"
            stroke="currentColor"
            viewBox="0 0 24 24"
            aria-hidden="true"
          >
            <path
              stroke-linecap="round"
              stroke-linejoin="round"
              stroke-width="2"
              d="M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z"
            />
          </svg>
        </div>
        <div>
          <p class="text-sm font-medium text-gray-500 dark:text-gray-400">
            Regressions
          </p>
          <p
            :class="[
              'text-2xl font-bold',
              regressionsCount > 0
                ? 'text-red-600 dark:text-red-400'
                : 'text-gray-900 dark:text-white',
            ]"
          >
            {{ regressionsCount }}
          </p>
        </div>
      </div>
    </div>

    <!-- Improvements Card -->
    <div
      class="rounded-lg border border-gray-200 bg-white p-4 shadow-sm dark:border-gray-700 dark:bg-gray-800"
    >
      <div class="flex items-center gap-3">
        <div
          :class="[
            'rounded-lg p-2',
            improvementsCount > 0
              ? 'bg-green-100 dark:bg-green-900/40'
              : 'bg-gray-100 dark:bg-gray-700',
          ]"
        >
          <svg
            class="h-6 w-6"
            :class="
              improvementsCount > 0
                ? 'text-green-600 dark:text-green-400'
                : 'text-gray-600 dark:text-gray-400'
            "
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
        </div>
        <div>
          <p class="text-sm font-medium text-gray-500 dark:text-gray-400">
            Improvements
          </p>
          <p
            :class="[
              'text-2xl font-bold',
              improvementsCount > 0
                ? 'text-green-600 dark:text-green-400'
                : 'text-gray-900 dark:text-white',
            ]"
          >
            {{ improvementsCount }}
          </p>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
defineProps({
  totalEvaluations: {
    type: Number,
    default: 0,
  },
  netChange: {
    type: Number,
    default: 0,
  },
  regressionsCount: {
    type: Number,
    default: 0,
  },
  improvementsCount: {
    type: Number,
    default: 0,
  },
})
</script>
