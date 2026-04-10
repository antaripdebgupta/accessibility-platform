<template>
  <div class="rounded-lg border p-4" :class="cardClasses">
    <!-- Header -->
    <div class="flex items-center justify-between">
      <div class="flex items-center space-x-2">
        <span class="text-sm font-medium text-gray-700">
          Viewing as <strong>{{ profileName }}</strong>
        </span>
      </div>
      <button
        v-if="showChangeButton"
        type="button"
        class="text-sm font-medium text-indigo-600 hover:text-indigo-500"
        @click="$emit('change')"
      >
        Change
      </button>
    </div>

    <!-- Stats Row -->
    <div class="mt-4 grid grid-cols-2 gap-4 sm:grid-cols-4">
      <!-- Critical for Profile -->
      <div class="flex flex-col">
        <span class="text-2xl font-bold text-red-600">
          {{ summary.critical_for_profile }}
        </span>
        <span class="text-xs text-gray-500">Critical for profile</span>
      </div>

      <!-- High for Profile -->
      <div class="flex flex-col">
        <span class="text-2xl font-bold text-orange-600">
          {{ summary.high_for_profile }}
        </span>
        <span class="text-xs text-gray-500">High for profile</span>
      </div>

      <!-- Not Applicable -->
      <div class="flex flex-col">
        <span class="text-2xl font-bold text-gray-400">
          {{ summary.not_applicable }}
        </span>
        <span class="text-xs text-gray-500">Not applicable</span>
      </div>

      <!-- Total Relevant -->
      <div class="flex flex-col">
        <span class="text-2xl font-bold text-blue-600">
          {{ summary.total_relevant }}
        </span>
        <span class="text-xs text-gray-500">Total relevant</span>
      </div>
    </div>

    <!-- Boosted Note -->
    <div
      v-if="summary.boosted_count > 0"
      class="mt-3 flex items-center space-x-1 text-xs text-gray-500"
    >
      <svg
        class="h-4 w-4 text-amber-500"
        fill="currentColor"
        viewBox="0 0 20 20"
      >
        <path
          fill-rule="evenodd"
          d="M5.293 7.707a1 1 0 010-1.414l4-4a1 1 0 011.414 0l4 4a1 1 0 01-1.414 1.414L11 5.414V17a1 1 0 11-2 0V5.414L6.707 7.707a1 1 0 01-1.414 0z"
          clip-rule="evenodd"
        />
      </svg>
      <span>
        <strong>{{ summary.boosted_count }}</strong> finding{{
          summary.boosted_count === 1 ? ' has' : 's have'
        }}
        elevated severity for this user group
      </span>
    </div>
  </div>
</template>

<script setup>
import { computed } from 'vue'

const props = defineProps({
  summary: {
    type: Object,
    required: true,
    default: () => ({
      profile_id: '',
      profile_name: '',
      critical_for_profile: 0,
      high_for_profile: 0,
      not_applicable: 0,
      total_relevant: 0,
      boosted_count: 0,
    }),
  },
  showChangeButton: {
    type: Boolean,
    default: true,
  },
})

const emit = defineEmits(['change'])

const profileName = computed(() => {
  return props.summary.profile_name || 'Unknown Profile'
})

const cardClasses = computed(() => {
  const profileId = props.summary.profile_id
  const colorMap = {
    blind: 'border-blue-200 bg-blue-50',
    low_vision: 'border-amber-200 bg-amber-50',
    motor: 'border-green-200 bg-green-50',
    cognitive: 'border-purple-200 bg-purple-50',
  }
  return colorMap[profileId] || 'border-gray-200 bg-gray-50'
})
</script>
