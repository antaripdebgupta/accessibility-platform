<template>
  <span :class="badgeClasses">
    {{ displayLabel }}
  </span>
</template>

<script setup>
import { computed } from 'vue'

const props = defineProps({
  status: {
    type: String,
    required: true,
  },
})

/**
 * Status configuration mapping status values to colors and labels.
 */
const statusConfig = {
  DRAFT: {
    label: 'Draft',
    bgColor: 'bg-gray-100',
    textColor: 'text-gray-700',
    ringColor: 'ring-gray-500/20',
  },
  SCOPING: {
    label: 'Scoping',
    bgColor: 'bg-blue-100',
    textColor: 'text-blue-700',
    ringColor: 'ring-blue-500/20',
  },
  EXPLORING: {
    label: 'Exploring',
    bgColor: 'bg-sky-100',
    textColor: 'text-sky-700',
    ringColor: 'ring-sky-500/20',
  },
  SAMPLING: {
    label: 'Sampling',
    bgColor: 'bg-cyan-100',
    textColor: 'text-cyan-700',
    ringColor: 'ring-cyan-500/20',
  },
  AUDITING: {
    label: 'Auditing',
    bgColor: 'bg-amber-100',
    textColor: 'text-amber-700',
    ringColor: 'ring-amber-500/20',
  },
  REPORTING: {
    label: 'Reporting',
    bgColor: 'bg-purple-100',
    textColor: 'text-purple-700',
    ringColor: 'ring-purple-500/20',
  },
  COMPLETE: {
    label: 'Complete',
    bgColor: 'bg-green-100',
    textColor: 'text-green-700',
    ringColor: 'ring-green-500/20',
  },
  DELETED: {
    label: 'Deleted',
    bgColor: 'bg-red-100',
    textColor: 'text-red-700',
    ringColor: 'ring-red-500/20',
  },
}

const defaultConfig = {
  label: 'Unknown',
  bgColor: 'bg-gray-100',
  textColor: 'text-gray-700',
  ringColor: 'ring-gray-500/20',
}

const config = computed(() => {
  const upperStatus = props.status?.toUpperCase() || ''
  return statusConfig[upperStatus] || defaultConfig
})

const displayLabel = computed(() => config.value.label)

const badgeClasses = computed(() => [
  'inline-flex items-center rounded-full px-2.5 py-0.5 text-xs font-medium ring-1 ring-inset',
  config.value.bgColor,
  config.value.textColor,
  config.value.ringColor,
])
</script>
