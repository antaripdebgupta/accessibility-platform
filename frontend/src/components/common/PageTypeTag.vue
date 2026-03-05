<template>
  <span :class="tagClasses">
    {{ displayLabel }}
  </span>
</template>

<script setup>
import { computed } from 'vue'

const props = defineProps({
  pageType: {
    type: String,
    default: 'other',
  },
})

/**
 * Page type configuration mapping types to colors and labels.
 */
const pageTypeConfig = {
  home: {
    label: 'Home',
    bgColor: 'bg-indigo-100',
    textColor: 'text-indigo-700',
  },
  form: {
    label: 'Form',
    bgColor: 'bg-purple-100',
    textColor: 'text-purple-700',
  },
  navigation: {
    label: 'Navigation',
    bgColor: 'bg-blue-100',
    textColor: 'text-blue-700',
  },
  media: {
    label: 'Media',
    bgColor: 'bg-pink-100',
    textColor: 'text-pink-700',
  },
  search: {
    label: 'Search',
    bgColor: 'bg-cyan-100',
    textColor: 'text-cyan-700',
  },
  auth: {
    label: 'Auth',
    bgColor: 'bg-yellow-100',
    textColor: 'text-yellow-700',
  },
  error: {
    label: 'Error',
    bgColor: 'bg-red-100',
    textColor: 'text-red-700',
  },
  other: {
    label: 'Other',
    bgColor: 'bg-gray-100',
    textColor: 'text-gray-700',
  },
  unknown: {
    label: 'Unknown',
    bgColor: 'bg-gray-100',
    textColor: 'text-gray-500',
  },
}

const normalizedType = computed(() => {
  const type = props.pageType?.toLowerCase() || 'other'
  return pageTypeConfig[type] ? type : 'other'
})

const config = computed(() => pageTypeConfig[normalizedType.value])

const displayLabel = computed(() => config.value.label)

const tagClasses = computed(() => [
  'inline-flex items-center rounded-md px-2 py-1 text-xs font-medium',
  config.value.bgColor,
  config.value.textColor,
])
</script>
