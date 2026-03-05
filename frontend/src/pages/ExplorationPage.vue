<template>
  <AppLayout>
    <PageHeader
      title="Website Exploration"
      subtitle="Discover and select pages for accessibility evaluation"
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
            d="M21 12a9 9 0 01-9 9m9-9a9 9 0 00-9-9m9 9H3m9 9a9 9 0 01-9-9m9 9c1.657 0 3-4.03 3-9s-1.343-9-3-9m0 18c-1.657 0-3-4.03-3-9s1.343-9 3-9m-9 9a9 9 0 019-9"
          />
        </svg>
        <h3 class="mt-4 text-lg font-medium text-gray-900">
          Crawler Coming on Day 4
        </h3>
        <p class="mt-2 text-sm text-gray-500">
          This page will allow you to crawl the target website, discover pages,
          and select which ones to include in your accessibility audit.
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
