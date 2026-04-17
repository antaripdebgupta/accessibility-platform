<template>
  <div class="mb-6">
    <!-- Help Toggle Button -->
    <button
      type="button"
      class="inline-flex items-center gap-2 rounded-lg border border-blue-200 bg-blue-50 px-4 py-2 text-sm font-medium text-blue-700 transition-colors hover:bg-blue-100 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:ring-offset-2 dark:border-blue-800 dark:bg-blue-900/30 dark:text-blue-300 dark:hover:bg-blue-900/50"
      :aria-expanded="isExpanded"
      @click="isExpanded = !isExpanded"
    >
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
          d="M8.228 9c.549-1.165 2.03-2 3.772-2 2.21 0 4 1.343 4 3 0 1.4-1.278 2.575-3.006 2.907-.542.104-.994.54-.994 1.093m0 3h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z"
        />
      </svg>
      <span>{{ isExpanded ? 'Hide Help Guide' : 'Show Help Guide' }}</span>
      <svg
        :class="[
          'h-4 w-4 transition-transform',
          isExpanded ? 'rotate-180' : '',
        ]"
        fill="none"
        stroke="currentColor"
        viewBox="0 0 24 24"
        aria-hidden="true"
      >
        <path
          stroke-linecap="round"
          stroke-linejoin="round"
          stroke-width="2"
          d="M19 9l-7 7-7-7"
        />
      </svg>
    </button>

    <!-- Help Content Panel -->
    <Transition
      enter-active-class="transition ease-out duration-300"
      enter-from-class="opacity-0 -translate-y-2"
      enter-to-class="opacity-100 translate-y-0"
      leave-active-class="transition ease-in duration-200"
      leave-from-class="opacity-100 translate-y-0"
      leave-to-class="opacity-0 -translate-y-2"
    >
      <div
        v-if="isExpanded"
        class="mt-4 rounded-xl border border-blue-200 bg-linear-to-br from-blue-50 to-indigo-50 p-6 dark:border-blue-800 dark:from-blue-900/20 dark:to-indigo-900/20"
      >
        <div class="mb-4 flex items-center gap-2">
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
              d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z"
            />
          </svg>
          <h3 class="text-lg font-semibold text-gray-900 dark:text-white">
            Understanding the Longitudinal Dashboard
          </h3>
        </div>

        <p class="mb-6 text-gray-600 dark:text-gray-300">
          The Longitudinal Dashboard helps you track accessibility trends over
          time by comparing multiple evaluations of the same website. This
          enables you to detect regressions, measure improvements, and ensure
          continuous accessibility compliance.
        </p>

        <!-- Summary Cards Section -->
        <div class="mb-6">
          <h4
            class="mb-3 flex items-center gap-2 font-semibold text-gray-900 dark:text-white"
          >
            <svg
              class="h-5 w-5 text-blue-500"
              fill="none"
              stroke="currentColor"
              viewBox="0 0 24 24"
              aria-hidden="true"
            >
              <path
                stroke-linecap="round"
                stroke-linejoin="round"
                stroke-width="2"
                d="M4 6a2 2 0 012-2h2a2 2 0 012 2v2a2 2 0 01-2 2H6a2 2 0 01-2-2V6zM14 6a2 2 0 012-2h2a2 2 0 012 2v2a2 2 0 01-2 2h-2a2 2 0 01-2-2V6zM4 16a2 2 0 012-2h2a2 2 0 012 2v2a2 2 0 01-2 2H6a2 2 0 01-2-2v-2zM14 16a2 2 0 012-2h2a2 2 0 012 2v2a2 2 0 01-2 2h-2a2 2 0 01-2-2v-2z"
              />
            </svg>
            Summary Cards Explained
          </h4>
          <div class="grid gap-4 md:grid-cols-2">
            <div
              class="rounded-lg border border-blue-100 bg-white p-4 dark:border-gray-700 dark:bg-gray-800"
            >
              <div class="mb-2 flex items-center gap-2">
                <span
                  class="inline-flex h-8 w-8 items-center justify-center rounded-lg bg-blue-100 dark:bg-blue-900/40"
                >
                  <svg
                    class="h-4 w-4 text-blue-600 dark:text-blue-400"
                    fill="none"
                    stroke="currentColor"
                    viewBox="0 0 24 24"
                  >
                    <path
                      stroke-linecap="round"
                      stroke-linejoin="round"
                      stroke-width="2"
                      d="M9 5H7a2 2 0 00-2 2v12a2 2 0 002 2h10a2 2 0 002-2V7a2 2 0 00-2-2h-2M9 5a2 2 0 002 2h2a2 2 0 002-2M9 5a2 2 0 012-2h2a2 2 0 012 2"
                    />
                  </svg>
                </span>
                <h5 class="font-medium text-gray-900 dark:text-white">
                  Total Evaluations
                </h5>
              </div>
              <p class="text-sm text-gray-600 dark:text-gray-300">
                The number of accessibility evaluations completed for this
                website. More evaluations provide better trend data and help
                identify patterns in your accessibility journey.
              </p>
            </div>

            <div
              class="rounded-lg border border-blue-100 bg-white p-4 dark:border-gray-700 dark:bg-gray-800"
            >
              <div class="mb-2 flex items-center gap-2">
                <span
                  class="inline-flex h-8 w-8 items-center justify-center rounded-lg bg-gray-100 dark:bg-gray-700"
                >
                  <svg
                    class="h-4 w-4 text-gray-600 dark:text-gray-400"
                    fill="none"
                    stroke="currentColor"
                    viewBox="0 0 24 24"
                  >
                    <path
                      stroke-linecap="round"
                      stroke-linejoin="round"
                      stroke-width="2"
                      d="M5 12h14"
                    />
                  </svg>
                </span>
                <h5 class="font-medium text-gray-900 dark:text-white">
                  Net Change (No Change)
                </h5>
              </div>
              <p class="text-sm text-gray-600 dark:text-gray-300">
                The difference in total findings between the latest and previous
                evaluation. <strong class="text-green-600">Negative</strong>
                means fewer issues (improvement).
                <strong class="text-red-600">Positive</strong> means more issues
                (regression). <strong>Zero</strong> means no change.
              </p>
            </div>

            <div
              class="rounded-lg border border-blue-100 bg-white p-4 dark:border-gray-700 dark:bg-gray-800"
            >
              <div class="mb-2 flex items-center gap-2">
                <span
                  class="inline-flex h-8 w-8 items-center justify-center rounded-lg bg-red-100 dark:bg-red-900/40"
                >
                  <svg
                    class="h-4 w-4 text-red-600 dark:text-red-400"
                    fill="none"
                    stroke="currentColor"
                    viewBox="0 0 24 24"
                  >
                    <path
                      stroke-linecap="round"
                      stroke-linejoin="round"
                      stroke-width="2"
                      d="M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z"
                    />
                  </svg>
                </span>
                <h5 class="font-medium text-gray-900 dark:text-white">
                  Regressions
                </h5>
              </div>
              <p class="text-sm text-gray-600 dark:text-gray-300">
                WCAG criteria that have <strong>more issues</strong> than in the
                previous evaluation. Regressions indicate areas where
                accessibility has worsened and require immediate attention.
              </p>
            </div>

            <div
              class="rounded-lg border border-blue-100 bg-white p-4 dark:border-gray-700 dark:bg-gray-800"
            >
              <div class="mb-2 flex items-center gap-2">
                <span
                  class="inline-flex h-8 w-8 items-center justify-center rounded-lg bg-green-100 dark:bg-green-900/40"
                >
                  <svg
                    class="h-4 w-4 text-green-600 dark:text-green-400"
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
                </span>
                <h5 class="font-medium text-gray-900 dark:text-white">
                  Improvements
                </h5>
              </div>
              <p class="text-sm text-gray-600 dark:text-gray-300">
                WCAG criteria that have <strong>fewer issues</strong> than in
                the previous evaluation. This shows your accessibility
                remediation efforts are working!
              </p>
            </div>
          </div>
        </div>

        <!-- Charts Section -->
        <div class="mb-6">
          <h4
            class="mb-3 flex items-center gap-2 font-semibold text-gray-900 dark:text-white"
          >
            <svg
              class="h-5 w-5 text-blue-500"
              fill="none"
              stroke="currentColor"
              viewBox="0 0 24 24"
              aria-hidden="true"
            >
              <path
                stroke-linecap="round"
                stroke-linejoin="round"
                stroke-width="2"
                d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z"
              />
            </svg>
            Chart Visualizations
          </h4>
          <div class="grid gap-4 md:grid-cols-2">
            <div
              class="rounded-lg border border-blue-100 bg-white p-4 dark:border-gray-700 dark:bg-gray-800"
            >
              <h5 class="mb-2 font-medium text-gray-900 dark:text-white">
                Total Findings Over Time
              </h5>
              <p class="text-sm text-gray-600 dark:text-gray-300">
                A line chart showing how the total number of accessibility
                issues has changed across evaluations. A downward trend
                indicates your accessibility is improving over time.
              </p>
            </div>

            <div
              class="rounded-lg border border-blue-100 bg-white p-4 dark:border-gray-700 dark:bg-gray-800"
            >
              <h5 class="mb-2 font-medium text-gray-900 dark:text-white">
                Conformance Verdict History
              </h5>
              <p class="text-sm text-gray-600 dark:text-gray-300">
                Shows the overall conformance verdict for each evaluation.
                Verdicts indicate whether the website met the target WCAG
                conformance level (A, AA, AAA) at each point in time.
              </p>
            </div>
          </div>
        </div>

        <!-- Verdict Section -->
        <div>
          <h4
            class="mb-3 flex items-center gap-2 font-semibold text-gray-900 dark:text-white"
          >
            <svg
              class="h-5 w-5 text-blue-500"
              fill="none"
              stroke="currentColor"
              viewBox="0 0 24 24"
              aria-hidden="true"
            >
              <path
                stroke-linecap="round"
                stroke-linejoin="round"
                stroke-width="2"
                d="M9 12l2 2 4-4M7.835 4.697a3.42 3.42 0 001.946-.806 3.42 3.42 0 014.438 0 3.42 3.42 0 001.946.806 3.42 3.42 0 013.138 3.138 3.42 3.42 0 00.806 1.946 3.42 3.42 0 010 4.438 3.42 3.42 0 00-.806 1.946 3.42 3.42 0 01-3.138 3.138 3.42 3.42 0 00-1.946.806 3.42 3.42 0 01-4.438 0 3.42 3.42 0 00-1.946-.806 3.42 3.42 0 01-3.138-3.138 3.42 3.42 0 00-.806-1.946 3.42 3.42 0 010-4.438 3.42 3.42 0 00.806-1.946 3.42 3.42 0 013.138-3.138z"
              />
            </svg>
            What is a Verdict?
          </h4>
          <div
            class="rounded-lg border border-blue-100 bg-white p-4 dark:border-gray-700 dark:bg-gray-800"
          >
            <p class="mb-3 text-sm text-gray-600 dark:text-gray-300">
              A <strong>Verdict</strong> is the overall accessibility
              conformance status of your website based on WCAG-EM methodology.
              Each WCAG criterion is assigned a verdict, and the overall website
              verdict is calculated based on all criteria.
            </p>
            <div class="grid gap-2 sm:grid-cols-2 lg:grid-cols-4">
              <div class="flex items-center gap-2">
                <span
                  class="inline-block rounded-full bg-green-100 px-2 py-1 text-xs font-medium text-green-800 dark:bg-green-900/40 dark:text-green-300"
                >
                  Pass
                </span>
                <span class="text-sm text-gray-600 dark:text-gray-300"
                  >Meets requirements</span
                >
              </div>
              <div class="flex items-center gap-2">
                <span
                  class="inline-block rounded-full bg-red-100 px-2 py-1 text-xs font-medium text-red-800 dark:bg-red-900/40 dark:text-red-300"
                >
                  Fail
                </span>
                <span class="text-sm text-gray-600 dark:text-gray-300"
                  >Has accessibility issues</span
                >
              </div>
              <div class="flex items-center gap-2">
                <span
                  class="inline-block rounded-full bg-yellow-100 px-2 py-1 text-xs font-medium text-yellow-800 dark:bg-yellow-900/40 dark:text-yellow-300"
                >
                  Cannot Tell
                </span>
                <span class="text-sm text-gray-600 dark:text-gray-300"
                  >Needs manual review</span
                >
              </div>
              <div class="flex items-center gap-2">
                <span
                  class="inline-block rounded-full bg-gray-100 px-2 py-1 text-xs font-medium text-gray-800 dark:bg-gray-700 dark:text-gray-300"
                >
                  N/A
                </span>
                <span class="text-sm text-gray-600 dark:text-gray-300"
                  >Not applicable</span
                >
              </div>
            </div>
          </div>
        </div>

        <!-- Pro Tips -->
        <div
          class="mt-6 rounded-lg border border-amber-200 bg-amber-50 p-4 dark:border-amber-800 dark:bg-amber-900/20"
        >
          <h4
            class="mb-2 flex items-center gap-2 font-semibold text-amber-800 dark:text-amber-300"
          >
            Tips
          </h4>
          <ul
            class="list-inside list-disc space-y-1 text-sm text-amber-700 dark:text-amber-200"
          >
            <li>
              Run evaluations regularly (e.g., after each release) to catch
              regressions early
            </li>
            <li>
              Focus on fixing critical and serious issues first — they have the
              biggest impact on users
            </li>
            <li>
              Use the criterion trend charts to identify persistent problem
              areas
            </li>
            <li>
              A consistent downward trend in total findings indicates successful
              accessibility remediation
            </li>
          </ul>
        </div>
      </div>
    </Transition>
  </div>
</template>

<script setup>
import { ref } from 'vue'

const isExpanded = ref(false)
</script>
