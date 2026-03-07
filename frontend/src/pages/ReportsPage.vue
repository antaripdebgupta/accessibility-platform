<template>
  <AppLayout>
    <PageHeader
      title="Reports"
      subtitle="View and download accessibility conformance reports"
      :back-to="{ name: 'EvaluationDetail', params: { id: evaluationId } }"
    />

    <!-- Ready to Generate Card -->
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
          Once findings are reviewed, you can generate comprehensive
          accessibility conformance reports in multiple formats including PDF,
          HTML, and JSON.
        </p>

        <!-- Feature List -->
        <div class="mx-auto mt-6 max-w-sm">
          <ul class="space-y-2 text-left text-sm text-gray-600">
            <li class="flex items-start">
              <svg
                class="mr-2 mt-0.5 h-4 w-4 flex-shrink-0 text-indigo-500"
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
              VPAT/WCAG 2.1 conformance level summary
            </li>
            <li class="flex items-start">
              <svg
                class="mr-2 mt-0.5 h-4 w-4 flex-shrink-0 text-indigo-500"
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
              Per-criterion pass/fail breakdown
            </li>
            <li class="flex items-start">
              <svg
                class="mr-2 mt-0.5 h-4 w-4 flex-shrink-0 text-indigo-500"
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
              Remediation recommendations
            </li>
            <li class="flex items-start">
              <svg
                class="mr-2 mt-0.5 h-4 w-4 flex-shrink-0 text-indigo-500"
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
              Export in PDF, HTML, and JSON formats
            </li>
          </ul>
        </div>

        <!-- Action Buttons -->
        <div class="mt-8 flex items-center justify-center space-x-4">
          <RouterLink
            :to="{ name: 'Findings', params: { id: evaluationId } }"
            class="inline-flex items-center rounded-md border border-gray-300 bg-white px-4 py-2 text-sm font-medium text-gray-700 shadow-sm hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-indigo-500 focus:ring-offset-2"
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
                d="M9 5H7a2 2 0 00-2 2v12a2 2 0 002 2h10a2 2 0 002-2V7a2 2 0 00-2-2h-2M9 5a2 2 0 002 2h2a2 2 0 002-2M9 5a2 2 0 012-2h2a2 2 0 012 2"
              />
            </svg>
            Review Findings
          </RouterLink>
          <button
            type="button"
            disabled
            class="inline-flex items-center rounded-md bg-indigo-600 px-4 py-2 text-sm font-semibold text-white shadow-sm hover:bg-indigo-500 focus:outline-none focus:ring-2 focus:ring-indigo-500 focus:ring-offset-2 disabled:cursor-not-allowed disabled:opacity-50"
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
                d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z"
              />
            </svg>
            Generate Report (Coming Soon)
          </button>
        </div>

        <!-- Coming in Day 7 notice -->
        <p class="mt-6 text-xs text-gray-400">
          Report generation will be available after findings review is complete.
        </p>
      </div>
    </div>
  </AppLayout>
</template>

<script setup>
import { computed } from 'vue'
import { RouterLink, useRoute } from 'vue-router'

import AppLayout from '../components/layout/AppLayout.vue'
import PageHeader from '../components/layout/PageHeader.vue'

const route = useRoute()

const evaluationId = computed(() => route.params.id)
</script>
