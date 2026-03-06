<template>
  <div class="grid grid-cols-2 gap-4 md:grid-cols-4" v-bind="$attrs">
    <!-- Critical Card -->
    <button
      type="button"
      class="rounded-lg p-4 text-left transition-all focus:outline-none focus:ring-2 focus:ring-red-500 focus:ring-offset-2"
      :class="[
        'bg-red-50',
        activeSeverity === 'critical'
          ? 'ring-2 ring-red-500'
          : 'hover:bg-red-100',
      ]"
      @click="$emit('filter', 'critical')"
    >
      <div class="text-3xl font-bold text-red-600">
        {{ summary.critical }}
      </div>
      <div class="mt-1 text-sm font-medium text-red-700">Critical</div>
    </button>

    <!-- Serious Card -->
    <button
      type="button"
      class="rounded-lg p-4 text-left transition-all focus:outline-none focus:ring-2 focus:ring-orange-500 focus:ring-offset-2"
      :class="[
        'bg-orange-50',
        activeSeverity === 'serious'
          ? 'ring-2 ring-orange-500'
          : 'hover:bg-orange-100',
      ]"
      @click="$emit('filter', 'serious')"
    >
      <div class="text-3xl font-bold text-orange-600">
        {{ summary.serious }}
      </div>
      <div class="mt-1 text-sm font-medium text-orange-700">Serious</div>
    </button>

    <!-- Moderate Card -->
    <button
      type="button"
      class="rounded-lg p-4 text-left transition-all focus:outline-none focus:ring-2 focus:ring-yellow-500 focus:ring-offset-2"
      :class="[
        'bg-yellow-50',
        activeSeverity === 'moderate'
          ? 'ring-2 ring-yellow-500'
          : 'hover:bg-yellow-100',
      ]"
      @click="$emit('filter', 'moderate')"
    >
      <div class="text-3xl font-bold text-yellow-600">
        {{ summary.moderate }}
      </div>
      <div class="mt-1 text-sm font-medium text-yellow-700">Moderate</div>
    </button>

    <!-- Minor Card -->
    <button
      type="button"
      class="rounded-lg p-4 text-left transition-all focus:outline-none focus:ring-2 focus:ring-blue-500 focus:ring-offset-2"
      :class="[
        'bg-blue-50',
        activeSeverity === 'minor'
          ? 'ring-2 ring-blue-500'
          : 'hover:bg-blue-100',
      ]"
      @click="$emit('filter', 'minor')"
    >
      <div class="text-3xl font-bold text-blue-500">
        {{ summary.minor }}
      </div>
      <div class="mt-1 text-sm font-medium text-blue-600">Minor</div>
    </button>
  </div>

  <!-- Total Summary -->
  <div class="mt-4 text-center text-sm text-gray-600">
    <span class="font-semibold">{{ summary.total }}</span> issues found
    <span v-if="criteriaCount"> across {{ criteriaCount }} WCAG criteria</span>
  </div>
</template>

<script setup>
const props = defineProps({
  summary: {
    type: Object,
    required: true,
    default: () => ({
      critical: 0,
      serious: 0,
      moderate: 0,
      minor: 0,
      info: 0,
      total: 0,
    }),
  },
  activeSeverity: {
    type: String,
    default: null,
  },
  criteriaCount: {
    type: Number,
    default: 0,
  },
})

defineEmits(['filter'])
</script>
