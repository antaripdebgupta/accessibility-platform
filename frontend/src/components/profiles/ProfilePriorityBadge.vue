<template>
  <span
    class="inline-flex items-center rounded-full px-2 py-0.5 text-xs font-medium"
    :class="priorityClasses"
  >
    {{ priorityLabel }}
  </span>
</template>

<script setup>
import { computed } from 'vue'

const props = defineProps({
  priority: {
    type: String,
    required: true,
    validator: (v) => ['critical', 'high', 'medium', 'low', 'na'].includes(v),
  },
})

const priorityClasses = computed(() => {
  const classMap = {
    critical: 'bg-red-100 text-red-800 border border-red-200',
    high: 'bg-orange-100 text-orange-800 border border-orange-200',
    medium: 'bg-yellow-100 text-yellow-800 border border-yellow-200',
    low: 'bg-blue-100 text-blue-800 border border-blue-200',
    na: 'bg-gray-100 text-gray-500 border border-gray-200 line-through',
  }
  return classMap[props.priority] || classMap.medium
})

const priorityLabel = computed(() => {
  const labelMap = {
    critical: 'Critical for profile',
    high: 'High for profile',
    medium: 'Medium',
    low: 'Low',
    na: 'N/A for this profile',
  }
  return labelMap[props.priority] || 'Unknown'
})
</script>
