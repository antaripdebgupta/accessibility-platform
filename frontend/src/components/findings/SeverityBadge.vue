<template>
  <span :class="badgeClasses">
    {{ displayLabel }}
  </span>
</template>

<script setup>
import { computed } from 'vue'

const props = defineProps({
  severity: {
    type: String,
    required: true,
  },
})

// Severity configuration mapping severity values to colors.
const severityConfig = {
  critical: {
    label: 'Critical',
    bgColor: 'bg-red-100',
    textColor: 'text-red-700',
  },
  serious: {
    label: 'Serious',
    bgColor: 'bg-orange-100',
    textColor: 'text-orange-700',
  },
  moderate: {
    label: 'Moderate',
    bgColor: 'bg-yellow-100',
    textColor: 'text-yellow-700',
  },
  minor: {
    label: 'Minor',
    bgColor: 'bg-blue-100',
    textColor: 'text-blue-700',
  },
  info: {
    label: 'Info',
    bgColor: 'bg-gray-100',
    textColor: 'text-gray-700',
  },
}

const defaultConfig = {
  label: 'Unknown',
  bgColor: 'bg-gray-100',
  textColor: 'text-gray-700',
}

const config = computed(() => {
  const lowerSeverity = props.severity?.toLowerCase() || ''
  return severityConfig[lowerSeverity] || defaultConfig
})

const displayLabel = computed(() => config.value.label)

const badgeClasses = computed(() => [
  'inline-flex items-center rounded-full px-2 py-0.5 text-xs font-medium',
  config.value.bgColor,
  config.value.textColor,
])
</script>
