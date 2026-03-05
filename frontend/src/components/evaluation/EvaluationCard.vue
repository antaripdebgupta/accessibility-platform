<template>
  <RouterLink
    :to="`/evaluations/${evaluation.id}`"
    class="group block rounded-lg border border-gray-200 bg-white p-5 shadow-sm transition-all hover:border-indigo-300 hover:shadow-md focus:outline-none focus:ring-2 focus:ring-indigo-500 focus:ring-offset-2"
  >
    <div class="flex items-start justify-between">
      <div class="min-w-0 flex-1">
        <!-- Title -->
        <h3
          class="truncate text-base font-semibold text-gray-900 group-hover:text-indigo-600"
        >
          {{ evaluation.title }}
        </h3>

        <!-- URL -->
        <p
          class="mt-1 truncate text-sm text-gray-500"
          :title="evaluation.target_url"
        >
          {{ truncatedUrl }}
        </p>
      </div>

      <!-- Status Badge -->
      <div class="ml-4 shrink-0">
        <StatusBadge :status="evaluation.status" />
      </div>
    </div>

    <!-- Meta information -->
    <div class="mt-4 flex items-center justify-between text-sm">
      <div class="flex items-center space-x-4 text-gray-500">
        <!-- WCAG Version & Level -->
        <span class="inline-flex items-center">
          <svg
            class="mr-1 h-4 w-4 text-gray-400"
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
          WCAG {{ evaluation.wcag_version }} {{ evaluation.conformance_level }}
        </span>
      </div>

      <!-- Created date -->
      <span class="text-gray-400">
        {{ formattedDate }}
      </span>
    </div>
  </RouterLink>
</template>

<script setup>
import { computed } from 'vue'
import { RouterLink } from 'vue-router'
import StatusBadge from '../common/StatusBadge.vue'

const props = defineProps({
  evaluation: {
    type: Object,
    required: true,
    validator: (value) => {
      return (
        typeof value.id !== 'undefined' &&
        typeof value.title === 'string' &&
        typeof value.target_url === 'string' &&
        typeof value.status === 'string'
      )
    },
  },
})

/**
 * Truncate URL for display, keeping domain and start of path.
 */
const truncatedUrl = computed(() => {
  const url = props.evaluation.target_url
  if (!url) return ''

  try {
    const parsed = new URL(url)
    const display = parsed.hostname + parsed.pathname
    return display.length > 50 ? display.substring(0, 47) + '...' : display
  } catch {
    return url.length > 50 ? url.substring(0, 47) + '...' : url
  }
})

/**
 * Format the created date for display.
 */
const formattedDate = computed(() => {
  if (!props.evaluation.created_at) return ''

  const date = new Date(props.evaluation.created_at)
  const now = new Date()
  const diffMs = now - date
  const diffDays = Math.floor(diffMs / (1000 * 60 * 60 * 24))

  if (diffDays === 0) {
    return 'Today'
  } else if (diffDays === 1) {
    return 'Yesterday'
  } else if (diffDays < 7) {
    return `${diffDays} days ago`
  } else {
    return date.toLocaleDateString('en-US', {
      month: 'short',
      day: 'numeric',
      year: date.getFullYear() !== now.getFullYear() ? 'numeric' : undefined,
    })
  }
})
</script>
