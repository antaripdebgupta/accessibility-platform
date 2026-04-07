<template>
  <!-- Backdrop -->
  <Transition name="fade">
    <div
      v-if="show"
      class="fixed inset-0 z-40 bg-black/50"
      @click="$emit('close')"
    ></div>
  </Transition>

  <!-- Panel -->
  <Transition name="slide">
    <div
      v-if="show && displayFinding"
      class="fixed right-0 top-0 z-50 flex h-full w-full flex-col bg-white shadow-xl sm:w-120"
    >
      <!-- Header -->
      <div
        class="flex items-start justify-between border-b border-gray-200 p-6"
      >
        <div class="flex-1">
          <h2 class="text-lg font-semibold text-gray-900">
            {{ displayFinding.criterion_code || 'N/A' }}
            <span
              v-if="displayFinding.criterion_name"
              class="font-normal text-gray-600"
            >
              — {{ displayFinding.criterion_name }}
            </span>
          </h2>
          <div class="mt-2 flex items-center space-x-2">
            <SeverityBadge :severity="displayFinding.severity || 'info'" />
            <span
              class="inline-flex items-center rounded-full px-2.5 py-0.5 text-xs font-medium"
              :class="getStatusClasses(displayFinding.status)"
            >
              {{ displayFinding.status }}
            </span>
          </div>
        </div>
        <button
          type="button"
          class="ml-4 rounded-full p-1 text-gray-400 hover:bg-gray-100 hover:text-gray-500 focus:outline-none focus:ring-2 focus:ring-indigo-500"
          @click="$emit('close')"
        >
          <span class="sr-only">Close</span>
          <svg
            class="h-6 w-6"
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
        </button>
      </div>

      <!-- Content -->
      <div class="flex-1 overflow-y-auto p-6">
        <!-- Page Section -->
        <div class="mb-6">
          <h3
            class="text-xs font-medium uppercase tracking-wider text-gray-500"
          >
            Found on
          </h3>
          <a
            v-if="displayFinding.page_url"
            :href="displayFinding.page_url"
            target="_blank"
            rel="noopener noreferrer"
            class="mt-1 flex items-center text-sm text-indigo-600 hover:text-indigo-500"
          >
            {{ displayFinding.page_url }}
            <svg
              class="ml-1 h-3 w-3"
              fill="none"
              stroke="currentColor"
              viewBox="0 0 24 24"
            >
              <path
                stroke-linecap="round"
                stroke-linejoin="round"
                stroke-width="2"
                d="M10 6H6a2 2 0 00-2 2v10a2 2 0 002 2h10a2 2 0 002-2v-4M14 4h6m0 0v6m0-6L10 14"
              />
            </svg>
          </a>
          <span v-else class="mt-1 text-sm text-gray-400"
            >No URL available</span
          >
        </div>

        <!-- Rule Section -->
        <div class="mb-6">
          <h3
            class="text-xs font-medium uppercase tracking-wider text-gray-500"
          >
            Rule ID
          </h3>
          <code
            class="mt-1 inline-block rounded bg-gray-100 px-2 py-1 font-mono text-sm text-gray-900"
          >
            {{ displayFinding.rule_id || 'N/A' }}
          </code>
          <div v-if="displayFinding.impact" class="mt-2">
            <span
              class="text-xs font-medium uppercase tracking-wider text-gray-500"
              >Impact:</span
            >
            <span class="ml-1 text-sm text-gray-700">{{
              displayFinding.impact
            }}</span>
          </div>
        </div>

        <!-- Description -->
        <div class="mb-6">
          <h3
            class="text-xs font-medium uppercase tracking-wider text-gray-500"
          >
            Description
          </h3>
          <p class="mt-1 text-sm text-gray-700">
            {{ displayFinding.description }}
          </p>
        </div>

        <!-- HTML Snippet -->
        <div v-if="displayFinding.html_snippet" class="mb-6">
          <h3
            class="text-xs font-medium uppercase tracking-wider text-gray-500"
          >
            Affected Element
          </h3>
          <pre
            class="mt-1 overflow-x-auto rounded bg-gray-900 p-3 text-xs text-green-400"
          ><code>{{ displayFinding.html_snippet }}</code></pre>
        </div>

        <!-- CSS Selector -->
        <div v-if="displayFinding.css_selector" class="mb-6">
          <h3
            class="text-xs font-medium uppercase tracking-wider text-gray-500"
          >
            CSS Selector
          </h3>
          <code
            class="mt-1 inline-block rounded bg-gray-100 px-2 py-1 font-mono text-xs text-gray-700"
          >
            {{ displayFinding.css_selector }}
          </code>
        </div>

        <!-- Screenshot -->
        <div class="mb-6">
          <h3
            class="text-xs font-medium uppercase tracking-wider text-gray-500"
          >
            Screenshot
          </h3>
          <div
            v-if="loadingDetails"
            class="mt-2 flex h-32 items-center justify-center rounded border border-dashed border-gray-300 bg-gray-50"
          >
            <span class="text-sm text-gray-400">Loading...</span>
          </div>
          <div
            v-else-if="displayFinding.screenshot_url && !screenshotError"
            class="mt-2"
          >
            <img
              :src="displayFinding.screenshot_url"
              alt="Page screenshot showing the accessibility issue"
              class="max-h-48 w-full rounded border border-gray-200 object-contain"
              @error="handleImageError"
              @load="screenshotError = false"
            />
          </div>
          <div
            v-else
            class="mt-2 flex h-32 flex-col items-center justify-center rounded border border-dashed border-gray-300 bg-gray-50"
          >
            <svg
              class="h-8 w-8 text-gray-300"
              fill="none"
              stroke="currentColor"
              viewBox="0 0 24 24"
            >
              <path
                stroke-linecap="round"
                stroke-linejoin="round"
                stroke-width="1.5"
                d="M4 16l4.586-4.586a2 2 0 012.828 0L16 16m-2-2l1.586-1.586a2 2 0 012.828 0L20 14m-6-6h.01M6 20h12a2 2 0 002-2V6a2 2 0 00-2-2H6a2 2 0 00-2 2v12a2 2 0 002 2z"
              />
            </svg>
            <span class="mt-2 text-sm text-gray-400">
              {{
                screenshotError
                  ? 'Screenshot unavailable'
                  : 'No screenshot available'
              }}
            </span>
          </div>
        </div>

        <!-- Remediation -->
        <div v-if="displayFinding.remediation" class="mb-6">
          <h3
            class="text-xs font-medium uppercase tracking-wider text-gray-500"
          >
            How to Fix
          </h3>
          <a
            :href="displayFinding.remediation"
            target="_blank"
            rel="noopener noreferrer"
            class="mt-1 inline-flex items-center text-sm text-indigo-600 hover:text-indigo-500"
          >
            View remediation guidance
            <svg
              class="ml-1 h-3 w-3"
              fill="none"
              stroke="currentColor"
              viewBox="0 0 24 24"
            >
              <path
                stroke-linecap="round"
                stroke-linejoin="round"
                stroke-width="2"
                d="M10 6H6a2 2 0 00-2 2v10a2 2 0 002 2h10a2 2 0 002-2v-4M14 4h6m0 0v6m0-6L10 14"
              />
            </svg>
          </a>
        </div>

        <!-- Reviewer Note -->
        <div class="mb-6">
          <h3
            class="text-xs font-medium uppercase tracking-wider text-gray-500"
          >
            Reviewer Note
          </h3>
          <textarea
            v-model="reviewerNote"
            rows="3"
            class="mt-1 block w-full rounded-md border-gray-300 text-sm shadow-sm focus:border-indigo-500 focus:ring-indigo-500"
            placeholder="Add a note..."
          ></textarea>
        </div>
      </div>

      <!-- Footer Actions -->
      <div class="border-t border-gray-200 bg-gray-50 p-4">
        <div class="flex items-center justify-between">
          <div class="flex space-x-3">
            <button
              v-if="canConfirmFinding"
              type="button"
              class="inline-flex items-center rounded-md bg-green-600 px-4 py-2 text-sm font-semibold text-white shadow-sm hover:bg-green-500 focus:outline-none focus:ring-2 focus:ring-green-500 focus:ring-offset-2 disabled:cursor-not-allowed disabled:opacity-50"
              :disabled="displayFinding.status === 'CONFIRMED'"
              @click="handleConfirm"
            >
              Confirm Issue
            </button>
            <button
              v-if="canDismissFinding"
              type="button"
              class="inline-flex items-center rounded-md border border-gray-300 bg-white px-4 py-2 text-sm font-medium text-gray-700 shadow-sm hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-gray-500 focus:ring-offset-2 disabled:cursor-not-allowed disabled:opacity-50"
              :disabled="displayFinding.status === 'DISMISSED'"
              @click="handleDismiss"
            >
              Dismiss
            </button>
          </div>
        </div>
        <p v-if="displayFinding.reviewed_by" class="mt-2 text-xs text-gray-500">
          Reviewed by {{ displayFinding.reviewed_by }}
        </p>
      </div>
    </div>
  </Transition>
</template>

<script setup>
import { computed, ref, watch } from 'vue'
import { usePermissions } from '../../composables/usePermissions'
import api from '../../lib/api'
import SeverityBadge from './SeverityBadge.vue'

const { canConfirmFinding, canDismissFinding } = usePermissions()

const props = defineProps({
  finding: {
    type: Object,
    default: null,
  },
  show: {
    type: Boolean,
    default: false,
  },
})

const emit = defineEmits(['close', 'confirm', 'dismiss'])

const reviewerNote = ref('')
const fullFinding = ref(null)
const loadingDetails = ref(false)
const screenshotError = ref(false)

// Computed to use either the full finding (with screenshot_url) or the prop
const displayFinding = computed(() => fullFinding.value || props.finding)

// Fetch full finding details when panel opens
watch(
  () => [props.show, props.finding?.id],
  async ([isShow, findingId]) => {
    if (isShow && findingId) {
      screenshotError.value = false // Reset screenshot error state
      loadingDetails.value = true
      try {
        const response = await api.get(`/findings/${findingId}`)
        fullFinding.value = response.data
        reviewerNote.value = response.data?.reviewer_note || ''
      } catch (err) {
        console.error('Failed to fetch finding details:', err)
        // Fall back to the prop finding
        fullFinding.value = null
        reviewerNote.value = props.finding?.reviewer_note || ''
      } finally {
        loadingDetails.value = false
      }
    } else if (!isShow) {
      // Reset when panel closes
      fullFinding.value = null
    }
  },
  { immediate: true },
)

function getStatusClasses(status) {
  switch (status) {
    case 'OPEN':
      return 'bg-gray-100 text-gray-700'
    case 'CONFIRMED':
      return 'bg-orange-100 text-orange-700'
    case 'DISMISSED':
      return 'bg-gray-100 text-gray-400'
    case 'RESOLVED':
      return 'bg-green-100 text-green-700'
    default:
      return 'bg-gray-100 text-gray-700'
  }
}

function handleConfirm() {
  emit('confirm', {
    id: displayFinding.value?.id || props.finding?.id,
    reviewer_note: reviewerNote.value,
  })
}

function handleDismiss() {
  emit('dismiss', {
    id: displayFinding.value?.id || props.finding?.id,
    reviewer_note: reviewerNote.value,
  })
}

function handleImageError() {
  // Set error state to show placeholder instead of broken image
  screenshotError.value = true
}
</script>

<style scoped>
/* Fade transition for backdrop */
.fade-enter-active,
.fade-leave-active {
  transition: opacity 0.2s ease;
}

.fade-enter-from,
.fade-leave-to {
  opacity: 0;
}

/* Slide transition for panel */
.slide-enter-active,
.slide-leave-active {
  transition: transform 0.3s ease;
}

.slide-enter-from,
.slide-leave-to {
  transform: translateX(100%);
}
</style>
