<template>
  <div class="rounded-lg border border-gray-200 bg-white p-6">
    <div class="flex items-start justify-between">
      <!-- Left: Report type and info -->
      <div class="flex items-start space-x-4">
        <!-- Type Badge -->
        <div :class="typeBadgeClasses">
          <component :is="typeIcon" class="h-5 w-5" />
        </div>

        <div>
          <!-- Report Type Label -->
          <h3 class="font-semibold text-gray-900">
            {{ typeLabel }}
          </h3>

          <!-- Verdict Badge -->
          <div class="mt-1 flex items-center space-x-2">
            <span :class="verdictBadgeClasses">
              {{ verdictLabel }}
            </span>
            <span class="text-sm text-gray-500">
              {{ formattedDate }}
            </span>
          </div>

          <!-- Stats Row -->
          <div class="mt-2 flex items-center space-x-4 text-sm text-gray-600">
            <span v-if="report.total_findings !== null">
              {{ report.total_findings }} issues
            </span>
            <span v-if="report.criteria_failed !== null">
              {{ report.criteria_failed }} criteria failed
            </span>
            <span v-if="report.criteria_passed !== null">
              {{ report.criteria_passed }} passed
            </span>
          </div>
        </div>
      </div>

      <!-- Right: Download Button -->
      <a
        v-if="report.download_url"
        :href="report.download_url"
        target="_blank"
        rel="noopener noreferrer"
        class="inline-flex items-center rounded-md px-4 py-2 text-sm font-semibold text-white shadow-sm hover:bg-indigo-200 focus:outline-none focus:ring-2 focus:ring-indigo-500 focus:ring-offset-2"
      >
        <svg
          class="-ml-0.5 mr-2 h-4 w-4"
          fill="none"
          stroke="currentColor"
          viewBox="0 0 24 24"
          aria-hidden="true"
        >
          <path
            stroke-linecap="round"
            stroke-linejoin="round"
            stroke-width="2"
            d="M4 16v1a3 3 0 003 3h10a3 3 0 003-3v-1m-4-4l-4 4m0 0l-4-4m4 4V4"
          />
        </svg>
        {{ downloadLabel }}
      </a>
    </div>
  </div>
</template>

<script setup>
import { computed, h } from 'vue'

const props = defineProps({
  report: {
    type: Object,
    required: true,
  },
})

// Type configuration
const typeConfig = {
  full: {
    label: 'Full PDF Report',
    badgeClass: 'bg-red-100 text-red-700',
    downloadLabel: 'Download PDF',
  },
  earl: {
    label: 'EARL JSON-LD',
    badgeClass: 'bg-blue-100 text-blue-700',
    downloadLabel: 'Download EARL JSON-LD',
  },
  csv: {
    label: 'CSV Export',
    badgeClass: 'bg-green-100 text-green-700',
    downloadLabel: 'Download CSV',
  },
  executive: {
    label: 'Executive Summary',
    badgeClass: 'bg-purple-100 text-purple-700',
    downloadLabel: 'Download PDF',
  },
}

const config = computed(() => {
  return typeConfig[props.report.report_type] || typeConfig.full
})

const typeLabel = computed(() => config.value.label)
const downloadLabel = computed(() => config.value.downloadLabel)

const typeBadgeClasses = computed(() => [
  'flex h-10 w-10 items-center justify-center rounded-lg',
  config.value.badgeClass,
])

// Type icons as render functions
const typeIcon = computed(() => {
  const type = props.report.report_type

  if (type === 'full' || type === 'executive') {
    // Document icon
    return {
      render() {
        return h(
          'svg',
          { fill: 'none', stroke: 'currentColor', viewBox: '0 0 24 24' },
          [
            h('path', {
              'stroke-linecap': 'round',
              'stroke-linejoin': 'round',
              'stroke-width': '2',
              d: 'M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z',
            }),
          ],
        )
      },
    }
  } else if (type === 'earl') {
    // Code icon
    return {
      render() {
        return h(
          'svg',
          { fill: 'none', stroke: 'currentColor', viewBox: '0 0 24 24' },
          [
            h('path', {
              'stroke-linecap': 'round',
              'stroke-linejoin': 'round',
              'stroke-width': '2',
              d: 'M10 20l4-16m4 4l4 4-4 4M6 16l-4-4 4-4',
            }),
          ],
        )
      },
    }
  } else {
    // Table icon
    return {
      render() {
        return h(
          'svg',
          { fill: 'none', stroke: 'currentColor', viewBox: '0 0 24 24' },
          [
            h('path', {
              'stroke-linecap': 'round',
              'stroke-linejoin': 'round',
              'stroke-width': '2',
              d: 'M3 10h18M3 14h18m-9-4v8m-7 0h14a2 2 0 002-2V8a2 2 0 00-2-2H5a2 2 0 00-2 2v8a2 2 0 002 2z',
            }),
          ],
        )
      },
    }
  }
})

// Verdict display
const verdictLabel = computed(() => {
  switch (props.report.conformance_verdict) {
    case 'CONFORMS':
      return 'Conforms'
    case 'DOES_NOT_CONFORM':
      return 'Does Not Conform'
    case 'CANNOT_DETERMINE':
      return 'Cannot Determine'
    default:
      return 'Unknown'
  }
})

const verdictBadgeClasses = computed(() => {
  const base = [
    'inline-flex items-center rounded-full px-2 py-0.5 text-xs font-medium',
  ]

  switch (props.report.conformance_verdict) {
    case 'CONFORMS':
      base.push('bg-green-100', 'text-green-700')
      break
    case 'DOES_NOT_CONFORM':
      base.push('bg-red-100', 'text-red-700')
      break
    default:
      base.push('bg-yellow-100', 'text-yellow-700')
  }

  return base
})

// Date formatting
const formattedDate = computed(() => {
  if (!props.report.generated_at) return ''

  const date = new Date(props.report.generated_at)
  return date.toLocaleDateString('en-US', {
    year: 'numeric',
    month: 'short',
    day: 'numeric',
    hour: '2-digit',
    minute: '2-digit',
  })
})
</script>
