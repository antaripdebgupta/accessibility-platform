<template>
  <AppLayout>
    <PageHeader
      title="Findings Review"
      subtitle="Review and manage accessibility issues"
      :back-to="{ name: 'EvaluationDetail', params: { id: evaluationId } }"
    />

    <!-- Placeholder Card -->
    <div class="rounded-lg border border-gray-200 bg-white p-8">
      <div class="text-center">
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
            d="M9 5H7a2 2 0 00-2 2v12a2 2 0 002 2h10a2 2 0 002-2V7a2 2 0 00-2-2h-2M9 5a2 2 0 002 2h2a2 2 0 002-2M9 5a2 2 0 012-2h2a2 2 0 012 2m-6 9l2 2 4-4"
          />
        </svg>
        <h3 class="mt-4 text-lg font-medium text-gray-900">
          Findings Review Coming Soon
        </h3>
        <p class="mt-2 text-sm text-gray-500">
          This page will display all accessibility findings from the automated
          scan, allowing you to review, confirm, or dismiss each issue.
        </p>
        <div class="mt-6">
          <RouterLink
            :to="{ name: 'EvaluationDetail', params: { id: evaluationId } }"
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
                d="M10 19l-7-7m0 0l7-7m-7 7h18"
              />
            </svg>
            Back to Evaluation
          </RouterLink>
        </div>
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
