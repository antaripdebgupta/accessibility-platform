<template>
  <div class="flex flex-wrap items-center gap-4">
    <!-- Severity Filter -->
    <div>
      <label for="severity-filter" class="sr-only">Filter by severity</label>
      <select
        id="severity-filter"
        :value="modelValue.severity || ''"
        class="block w-full rounded-md border-gray-300 py-2 pl-3 pr-10 text-sm focus:border-indigo-500 focus:outline-none focus:ring-indigo-500"
        @change="updateFilter('severity', $event.target.value)"
      >
        <option value="">All Severities</option>
        <option value="critical">Critical</option>
        <option value="serious">Serious</option>
        <option value="moderate">Moderate</option>
        <option value="minor">Minor</option>
      </select>
    </div>

    <!-- Status Filter -->
    <div>
      <label for="status-filter" class="sr-only">Filter by status</label>
      <select
        id="status-filter"
        :value="modelValue.status || ''"
        class="block w-full rounded-md border-gray-300 py-2 pl-3 pr-10 text-sm focus:border-indigo-500 focus:outline-none focus:ring-indigo-500"
        @change="updateFilter('status', $event.target.value)"
      >
        <option value="">All Statuses</option>
        <option value="OPEN">Open</option>
        <option value="CONFIRMED">Confirmed</option>
        <option value="DISMISSED">Dismissed</option>
      </select>
    </div>

    <!-- Source Filter -->
    <div>
      <label for="source-filter" class="sr-only">Filter by source</label>
      <select
        id="source-filter"
        :value="modelValue.source || ''"
        class="block w-full rounded-md border-gray-300 py-2 pl-3 pr-10 text-sm focus:border-indigo-500 focus:outline-none focus:ring-indigo-500"
        @change="updateFilter('source', $event.target.value)"
      >
        <option value="">All Sources</option>
        <option value="axe-core">axe-core</option>
        <option value="manual">Manual</option>
      </select>
    </div>

    <!-- Clear Filters -->
    <button
      v-if="hasActiveFilters"
      type="button"
      class="inline-flex items-center text-sm text-indigo-600 hover:text-indigo-500 focus:outline-none"
      @click="clearFilters"
    >
      <svg
        class="mr-1 h-4 w-4"
        fill="none"
        stroke="currentColor"
        viewBox="0 0 24 24"
      >
        <path
          stroke-linecap="round"
          stroke-linejoin="round"
          stroke-width="2"
          d="M6 18L18 6M6 6l12 12"
        />
      </svg>
      Clear filters
    </button>
  </div>
</template>

<script setup>
import { computed } from 'vue'

const props = defineProps({
  modelValue: {
    type: Object,
    required: true,
    default: () => ({
      severity: null,
      status: null,
      source: null,
    }),
  },
})

const emit = defineEmits(['update:modelValue'])

const hasActiveFilters = computed(() => {
  return (
    props.modelValue.severity ||
    props.modelValue.status ||
    props.modelValue.source
  )
})

function updateFilter(key, value) {
  emit('update:modelValue', {
    ...props.modelValue,
    [key]: value || null,
  })
}

function clearFilters() {
  emit('update:modelValue', {
    severity: null,
    status: null,
    source: null,
  })
}
</script>
