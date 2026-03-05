<template>
  <div class="grid grid-cols-1 gap-4 sm:grid-cols-2">
    <!-- Target URL -->
    <div>
      <dt class="text-xs font-medium uppercase tracking-wide text-gray-500">
        Target URL
      </dt>
      <dd class="mt-1 text-sm font-medium text-gray-900">
        <a
          :href="evaluation.target_url"
          target="_blank"
          rel="noopener noreferrer"
          class="inline-flex items-center text-indigo-600 hover:text-indigo-800 focus:outline-none focus:ring-2 focus:ring-indigo-500 focus:ring-offset-2"
        >
          <span class="truncate">{{ evaluation.target_url }}</span>
          <svg
            class="ml-1 h-4 w-4 shrink-0"
            fill="none"
            stroke="currentColor"
            viewBox="0 0 24 24"
            aria-hidden="true"
          >
            <path
              stroke-linecap="round"
              stroke-linejoin="round"
              stroke-width="2"
              d="M10 6H6a2 2 0 00-2 2v10a2 2 0 002 2h10a2 2 0 002-2v-4M14 4h6m0 0v6m0-6L10 14"
            />
          </svg>
          <span class="sr-only">(opens in new tab)</span>
        </a>
      </dd>
    </div>

    <!-- WCAG Version -->
    <div>
      <dt class="text-xs font-medium uppercase tracking-wide text-gray-500">
        WCAG Version
      </dt>
      <dd class="mt-1 text-sm font-medium text-gray-900">
        WCAG {{ evaluation.wcag_version || '2.1' }}
      </dd>
    </div>

    <!-- Conformance Level -->
    <div>
      <dt class="text-xs font-medium uppercase tracking-wide text-gray-500">
        Conformance Level
      </dt>
      <dd class="mt-1 text-sm font-medium text-gray-900">
        Level {{ evaluation.conformance_level || 'AA' }}
      </dd>
    </div>

    <!-- Audit Type -->
    <div>
      <dt class="text-xs font-medium uppercase tracking-wide text-gray-500">
        Audit Type
      </dt>
      <dd class="mt-1 text-sm font-medium capitalize text-gray-900">
        {{ formatAuditType(evaluation.audit_type) }}
      </dd>
    </div>

    <!-- Created Date -->
    <div>
      <dt class="text-xs font-medium uppercase tracking-wide text-gray-500">
        Created
      </dt>
      <dd class="mt-1 text-sm font-medium text-gray-900">
        {{ formatDate(evaluation.created_at) }}
      </dd>
    </div>

    <!-- Last Updated Date -->
    <div>
      <dt class="text-xs font-medium uppercase tracking-wide text-gray-500">
        Last Updated
      </dt>
      <dd class="mt-1 text-sm font-medium text-gray-900">
        {{ formatDate(evaluation.updated_at) }}
      </dd>
    </div>
  </div>
</template>

<script setup>
defineProps({
  /**
   * The evaluation object containing all metadata fields.
   */
  evaluation: {
    type: Object,
    required: true,
  },
})

/**
 * Formats a date string into a human-readable format.
 */
function formatDate(dateString) {
  if (!dateString) return '—'

  const date = new Date(dateString)
  return date.toLocaleDateString('en-US', {
    month: 'long',
    day: 'numeric',
    year: 'numeric',
  })
}

/**
 * Formats the audit type into a readable label.
 */
function formatAuditType(auditType) {
  if (!auditType) return 'In-depth'

  const typeMap = {
    'in-depth': 'In-depth',
    'quick-scan': 'Quick Scan',
    'sample-based': 'Sample-based',
  }

  return typeMap[auditType] || auditType
}
</script>
