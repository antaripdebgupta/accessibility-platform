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

    <!-- Profile Priority Filter (only shown when a profile is active) -->
    <div v-if="activeProfile">
      <label for="profile-priority-filter" class="sr-only"
        >Filter by profile priority</label
      >
      <select
        id="profile-priority-filter"
        :value="profilePriority || ''"
        class="block w-full rounded-md border-purple-300 bg-purple-50 py-2 pl-3 pr-10 text-sm focus:border-purple-500 focus:outline-none focus:ring-purple-500"
        @change="$emit('update:profilePriority', $event.target.value || null)"
      >
        <option value="">All Profile Priorities</option>
        <option value="critical">Critical for Profile</option>
        <option value="high">High for Profile</option>
        <option value="medium">Medium for Profile</option>
        <option value="low">Low for Profile</option>
        <option value="na">N/A for Profile</option>
      </select>
    </div>

    <!-- Exclude N/A Checkbox (only shown when a profile is active) -->
    <div v-if="activeProfile" class="flex items-center">
      <input
        id="exclude-na"
        type="checkbox"
        :checked="excludeNa"
        class="h-4 w-4 rounded border-gray-300 text-purple-600 focus:ring-purple-500"
        @change="$emit('update:excludeNa', $event.target.checked)"
      />
      <label for="exclude-na" class="ml-2 text-sm text-gray-700">
        Hide N/A findings
      </label>
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
  activeProfile: {
    type: String,
    default: null,
  },
  excludeNa: {
    type: Boolean,
    default: false,
  },
  profilePriority: {
    type: String,
    default: null,
  },
})

const emit = defineEmits([
  'update:modelValue',
  'update:excludeNa',
  'update:profilePriority',
])

const hasActiveFilters = computed(() => {
  return (
    props.modelValue.severity ||
    props.modelValue.status ||
    props.modelValue.source ||
    props.profilePriority ||
    props.excludeNa
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
  // Also clear profile-related filters
  if (props.activeProfile) {
    emit('update:profilePriority', null)
    emit('update:excludeNa', false)
  }
}
</script>
