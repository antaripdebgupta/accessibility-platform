<template>
  <div class="space-y-4">
    <!-- Empty State -->
    <div
      v-if="!failedCriteria || failedCriteria.length === 0"
      class="rounded-lg border border-green-200 bg-green-50 p-6 text-center"
    >
      <svg
        class="mx-auto h-12 w-12 text-green-500"
        fill="none"
        stroke="currentColor"
        viewBox="0 0 24 24"
        aria-hidden="true"
      >
        <path
          stroke-linecap="round"
          stroke-linejoin="round"
          stroke-width="2"
          d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z"
        />
      </svg>
      <h3 class="mt-3 text-lg font-medium text-green-800">
        No criteria failed — congratulations!
      </h3>
      <p class="mt-1 text-sm text-green-600">
        All evaluated WCAG criteria passed the automated assessment.
      </p>
    </div>

    <!-- Accordion List -->
    <div
      v-else
      class="divide-y divide-gray-200 rounded-lg border border-gray-200 bg-white"
    >
      <div
        v-for="(criterion, index) in failedCriteria"
        :key="criterion.criterion_code"
        class="criterion-item"
        :class="{ 'border-t border-gray-200': index > 0 }"
      >
        <!-- Accordion Header -->
        <button
          type="button"
          class="flex w-full items-center justify-between p-4 text-left hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-inset focus:ring-indigo-500"
          @click="toggleCriterion(criterion.criterion_code)"
        >
          <div class="flex items-center space-x-3">
            <!-- Level indicator border -->
            <div
              :class="[
                'h-10 w-1 rounded-full',
                levelColorClass(criterion.criterion_level),
              ]"
            ></div>

            <!-- Criterion info -->
            <div>
              <div class="flex items-center space-x-2">
                <span class="font-semibold text-gray-900">
                  {{ criterion.criterion_code }}
                </span>
                <span class="text-gray-700">—</span>
                <span class="text-gray-700">
                  {{ criterion.criterion_name }}
                </span>
                <span
                  :class="[
                    'inline-flex items-center rounded-full px-2 py-0.5 text-xs font-medium',
                    levelBadgeClass(criterion.criterion_level),
                  ]"
                >
                  Level {{ criterion.criterion_level }}
                </span>
              </div>
              <p class="mt-0.5 text-sm text-gray-500">
                {{ criterion.finding_count }} issue(s) found
              </p>
            </div>
          </div>

          <!-- Chevron -->
          <svg
            class="h-5 w-5 flex-shrink-0 text-gray-400 transition-transform duration-200"
            :class="{ 'rotate-180': isExpanded(criterion.criterion_code) }"
            fill="none"
            stroke="currentColor"
            viewBox="0 0 24 24"
          >
            <path
              stroke-linecap="round"
              stroke-linejoin="round"
              stroke-width="2"
              d="M19 9l-7 7-7-7"
            />
          </svg>
        </button>

        <!-- Accordion Content -->
        <div
          class="findings-content overflow-hidden transition-all duration-200"
          :style="contentStyle(criterion.criterion_code)"
        >
          <div
            :ref="(el) => setContentRef(criterion.criterion_code, el)"
            class="space-y-3 border-t border-gray-100 bg-gray-50 p-4"
          >
            <!-- Finding Items -->
            <div
              v-for="(finding, findingIndex) in criterion.findings"
              :key="findingIndex"
              class="finding-item rounded-md bg-white p-4 shadow-sm"
              :class="findingBorderClass(finding.severity)"
            >
              <!-- Severity Badge + Description -->
              <div class="flex items-start space-x-3">
                <span
                  :class="[
                    'inline-flex items-center rounded-full px-2 py-0.5 text-xs font-semibold',
                    severityBadgeClass(finding.severity),
                  ]"
                >
                  {{ capitalize(finding.severity) }}
                </span>
                <p class="flex-1 text-sm text-gray-800">
                  {{ finding.description }}
                </p>
              </div>

              <!-- Page URL -->
              <div class="mt-2 text-sm text-gray-500">
                <span class="font-medium">Page:</span>
                <a
                  v-if="finding.page_url"
                  :href="finding.page_url"
                  target="_blank"
                  rel="noopener noreferrer"
                  class="ml-1 text-indigo-600 hover:text-indigo-500 hover:underline"
                >
                  {{ truncateUrl(finding.page_url) }}
                </a>
                <span v-else class="ml-1 text-gray-400">Unknown</span>
              </div>

              <!-- CSS Selector -->
              <div v-if="finding.css_selector" class="mt-2">
                <code
                  class="block overflow-x-auto rounded bg-gray-800 p-2 text-xs text-gray-200"
                >
                  {{ finding.css_selector }}
                </code>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { reactive, ref } from 'vue'

defineProps({
  /**
   * Array of failed criteria with their findings
   */
  failedCriteria: {
    type: Array,
    default: () => [],
  },
})

// Track which criteria are expanded
const expandedCriteria = ref(new Set())

// Store refs to content elements for height calculation
const contentRefs = reactive({})

function setContentRef(code, el) {
  if (el) {
    contentRefs[code] = el
  }
}

function toggleCriterion(code) {
  if (expandedCriteria.value.has(code)) {
    expandedCriteria.value.delete(code)
  } else {
    expandedCriteria.value.add(code)
  }
  // Force reactivity
  expandedCriteria.value = new Set(expandedCriteria.value)
}

function isExpanded(code) {
  return expandedCriteria.value.has(code)
}

function contentStyle(code) {
  if (isExpanded(code)) {
    const el = contentRefs[code]
    if (el) {
      return { maxHeight: `${el.scrollHeight + 100}px` }
    }
    return { maxHeight: '2000px' }
  }
  return { maxHeight: '0px' }
}

// Level styling
function levelColorClass(level) {
  switch (level) {
    case 'A':
      return 'bg-blue-500'
    case 'AA':
      return 'bg-purple-500'
    case 'AAA':
      return 'bg-pink-500'
    default:
      return 'bg-gray-400'
  }
}

function levelBadgeClass(level) {
  switch (level) {
    case 'A':
      return 'bg-blue-100 text-blue-700'
    case 'AA':
      return 'bg-purple-100 text-purple-700'
    case 'AAA':
      return 'bg-pink-100 text-pink-700'
    default:
      return 'bg-gray-100 text-gray-700'
  }
}

// Severity styling
function severityBadgeClass(severity) {
  switch (severity) {
    case 'critical':
      return 'bg-red-100 text-red-700'
    case 'serious':
      return 'bg-orange-100 text-orange-700'
    case 'moderate':
      return 'bg-yellow-100 text-yellow-700'
    case 'minor':
      return 'bg-blue-100 text-blue-700'
    default:
      return 'bg-gray-100 text-gray-700'
  }
}

function findingBorderClass(severity) {
  switch (severity) {
    case 'critical':
      return 'border-l-4 border-l-red-500'
    case 'serious':
      return 'border-l-4 border-l-orange-500'
    case 'moderate':
      return 'border-l-4 border-l-yellow-500'
    case 'minor':
      return 'border-l-4 border-l-blue-500'
    default:
      return 'border-l-4 border-l-gray-300'
  }
}

// Utilities
function capitalize(str) {
  if (!str) return ''
  return str.charAt(0).toUpperCase() + str.slice(1)
}

function truncateUrl(url) {
  if (!url) return ''
  try {
    const parsed = new URL(url)
    const path = parsed.pathname
    if (path.length > 50) {
      return parsed.host + path.substring(0, 47) + '...'
    }
    return parsed.host + path
  } catch {
    return url.length > 60 ? url.substring(0, 57) + '...' : url
  }
}
</script>

<style scoped>
.rotate-180 {
  transform: rotate(180deg);
}

.findings-content {
  transition:
    max-height 0.2s ease-in-out,
    opacity 0.2s ease-in-out;
}
</style>
