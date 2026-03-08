<template>
  <div class="grid grid-cols-2 gap-4 sm:grid-cols-4">
    <!-- Pages Scanned -->
    <div class="rounded-lg border border-gray-200 bg-white p-6 text-center">
      <dt class="text-sm font-medium text-gray-500">Pages Scanned</dt>
      <dd class="mt-1 text-3xl font-semibold text-gray-900">
        {{ pagesScanned }}
      </dd>
    </div>

    <!-- Issues Found -->
    <div class="rounded-lg border border-gray-200 bg-white p-6 text-center">
      <dt class="text-sm font-medium text-gray-500">Issues Found</dt>
      <dd class="mt-1 text-3xl font-semibold text-gray-900">
        {{ totalFindings }}
      </dd>
    </div>

    <!-- Criteria Failed -->
    <div class="rounded-lg border border-gray-200 bg-white p-6 text-center">
      <dt class="text-sm font-medium text-gray-500">Criteria Failed</dt>
      <dd
        class="mt-1 text-3xl font-semibold"
        :class="criteriaFailed > 0 ? 'text-red-600' : 'text-green-600'"
      >
        {{ criteriaFailed }}
      </dd>
    </div>

    <!-- Criteria Passed -->
    <div class="rounded-lg border border-gray-200 bg-white p-6 text-center">
      <dt class="text-sm font-medium text-gray-500">Criteria Passed</dt>
      <dd class="mt-1 text-3xl font-semibold text-green-600">
        {{ criteriaPassed }}
      </dd>
    </div>
  </div>
</template>

<script setup>
defineProps({
  pagesScanned: {
    type: Number,
    default: 0,
  },
  totalFindings: {
    type: Number,
    default: 0,
  },
  criteriaFailed: {
    type: Number,
    default: 0,
  },
  criteriaPassed: {
    type: Number,
    default: 0,
  },
})
</script>
