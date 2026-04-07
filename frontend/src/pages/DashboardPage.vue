<template>
  <AppLayout>
    <!-- Page Header -->
    <PageHeader
      title="Evaluations"
      subtitle="Manage your WCAG accessibility evaluation projects"
    >
      <RouterLink
        v-if="canCreateEvaluation"
        to="/evaluations/new"
        class="inline-flex items-center rounded-md px-4 py-2 text-sm font-semibold text-white shadow-sm hover:bg-indigo-200 focus:outline-none focus:ring-2 focus:ring-indigo-500 focus:ring-offset-2"
      >
        <svg
          class="-ml-0.5 mr-1.5 h-5 w-5"
          fill="none"
          stroke="currentColor"
          viewBox="0 0 24 24"
          aria-hidden="true"
        >
          <path
            stroke-linecap="round"
            stroke-linejoin="round"
            stroke-width="2"
            d="M12 4v16m8-8H4"
          />
        </svg>
        New Evaluation
      </RouterLink>
    </PageHeader>

    <!-- Loading State -->
    <div
      v-if="evaluationsStore.loading"
      class="flex items-center justify-center py-16"
    >
      <LoadingSpinner size="lg" />
    </div>

    <!-- Error State -->
    <div
      v-else-if="evaluationsStore.error"
      class="rounded-lg border border-red-200 bg-red-50 p-6 text-center"
    >
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
        Failed to load evaluations
      </h3>
      <p class="mt-2 text-sm text-red-600">
        {{ evaluationsStore.error }}
      </p>
      <button
        @click="loadEvaluations"
        class="mt-4 inline-flex items-center rounded-md bg-red-100 px-4 py-2 text-sm font-medium text-red-700 hover:bg-red-200 focus:outline-none focus:ring-2 focus:ring-red-500 focus:ring-offset-2"
      >
        Try again
      </button>
    </div>

    <!-- Empty State -->
    <EmptyState
      v-else-if="!evaluationsStore.hasEvaluations"
      title="No evaluations yet"
      :message="
        canCreateEvaluation
          ? 'Get started by creating a new WCAG accessibility evaluation project.'
          : 'No evaluations have been created for this organisation yet.'
      "
      :actionLabel="canCreateEvaluation ? 'Create your first evaluation' : null"
      @action="canCreateEvaluation ? navigateToCreate() : null"
    >
      <template #icon>
        <svg
          class="h-8 w-8 text-gray-400"
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
      </template>
    </EmptyState>

    <!-- Evaluations Grid -->
    <div v-else class="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-3">
      <EvaluationCard
        v-for="evaluation in evaluationsStore.list"
        :key="evaluation.id"
        :evaluation="evaluation"
      />
    </div>

    <!-- Pagination info -->
    <div
      v-if="evaluationsStore.hasEvaluations"
      class="mt-6 text-center text-sm text-gray-500"
    >
      Showing {{ evaluationsStore.list.length }} of
      {{ evaluationsStore.total }} evaluations
    </div>
  </AppLayout>
</template>

<script setup>
import { onMounted } from 'vue'
import { RouterLink, useRouter } from 'vue-router'

import EmptyState from '../components/common/EmptyState.vue'
import LoadingSpinner from '../components/common/LoadingSpinner.vue'
import EvaluationCard from '../components/evaluation/EvaluationCard.vue'
import AppLayout from '../components/layout/AppLayout.vue'
import PageHeader from '../components/layout/PageHeader.vue'
import { usePermissions } from '../composables/usePermissions'
import { useAuthStore } from '../stores/auth'
import { useEvaluationsStore } from '../stores/evaluations'

const router = useRouter()
const authStore = useAuthStore()
const evaluationsStore = useEvaluationsStore()
const { canCreateEvaluation } = usePermissions()

function navigateToCreate() {
  router.push('/evaluations/new')
}

async function loadEvaluations() {
  try {
    await evaluationsStore.fetchList()
  } catch (error) {
    console.error('Failed to fetch evaluations:', error)
  }
}

onMounted(() => {
  loadEvaluations()
})
</script>
