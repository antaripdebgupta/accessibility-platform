<template>
  <!-- Backdrop -->
  <Transition name="fade">
    <div
      v-if="show"
      class="fixed inset-0 z-50 bg-black/50"
      @click="$emit('close')"
    ></div>
  </Transition>

  <!-- Modal -->
  <Transition name="zoom">
    <div
      v-if="show"
      class="fixed inset-0 z-50 flex items-center justify-center p-4"
      @click.self="$emit('close')"
    >
      <div class="w-full max-w-lg rounded-lg bg-white shadow-xl" @click.stop>
        <!-- Header -->
        <div
          class="flex items-center justify-between border-b border-gray-200 px-6 py-4"
        >
          <h2 class="text-lg font-semibold text-gray-900">
            Add Manual Finding
          </h2>
          <button
            type="button"
            class="rounded-full p-1 text-gray-400 hover:bg-gray-100 hover:text-gray-500 focus:outline-none focus:ring-2 focus:ring-indigo-500"
            @click="$emit('close')"
          >
            <span class="sr-only">Close</span>
            <svg
              class="h-5 w-5"
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

        <!-- Form -->
        <form class="p-6" @submit.prevent="handleSubmit">
          <!-- Page Selection -->
          <div class="mb-4">
            <label
              for="page-select"
              class="block text-sm font-medium text-gray-700"
            >
              Page <span class="text-red-500">*</span>
            </label>
            <select
              id="page-select"
              v-model="formData.page_id"
              required
              class="mt-1 block w-full rounded-md border-gray-300 py-2 pl-3 pr-10 text-sm focus:border-indigo-500 focus:outline-none focus:ring-indigo-500"
            >
              <option value="">Select a page</option>
              <option v-for="page in pages" :key="page.id" :value="page.id">
                {{ truncateUrl(page.url, 60) }}
              </option>
            </select>
          </div>

          <!-- WCAG Criterion Selection -->
          <div class="mb-4">
            <label
              for="criterion-select"
              class="block text-sm font-medium text-gray-700"
            >
              WCAG Criterion <span class="text-red-500">*</span>
            </label>
            <select
              id="criterion-select"
              v-model="formData.criterion_id"
              required
              class="mt-1 block w-full rounded-md border-gray-300 py-2 pl-3 pr-10 text-sm focus:border-indigo-500 focus:outline-none focus:ring-indigo-500"
            >
              <option value="">Select a criterion</option>
              <optgroup
                v-for="level in criteriaByLevel"
                :key="level.level"
                :label="`Level ${level.level}`"
              >
                <option
                  v-for="criterion in level.criteria"
                  :key="criterion.id"
                  :value="criterion.id"
                >
                  {{ criterion.criterion_id }} - {{ criterion.name }}
                </option>
              </optgroup>
            </select>
          </div>

          <!-- Severity -->
          <div class="mb-4">
            <label
              for="severity-select"
              class="block text-sm font-medium text-gray-700"
            >
              Severity <span class="text-red-500">*</span>
            </label>
            <select
              id="severity-select"
              v-model="formData.severity"
              required
              class="mt-1 block w-full rounded-md border-gray-300 py-2 pl-3 pr-10 text-sm focus:border-indigo-500 focus:outline-none focus:ring-indigo-500"
            >
              <option value="critical">Critical</option>
              <option value="serious">Serious</option>
              <option value="moderate">Moderate</option>
              <option value="minor">Minor</option>
            </select>
          </div>

          <!-- Description -->
          <div class="mb-4">
            <label
              for="description"
              class="block text-sm font-medium text-gray-700"
            >
              Description <span class="text-red-500">*</span>
            </label>
            <textarea
              id="description"
              v-model="formData.description"
              required
              rows="3"
              placeholder="Describe the accessibility issue..."
              class="mt-1 block w-full rounded-md border-gray-300 text-sm shadow-sm focus:border-indigo-500 focus:ring-indigo-500"
            ></textarea>
          </div>

          <!-- CSS Selector (optional) -->
          <div class="mb-4">
            <label
              for="css-selector"
              class="block text-sm font-medium text-gray-700"
            >
              CSS Selector
              <span class="text-xs text-gray-400">(optional)</span>
            </label>
            <input
              id="css-selector"
              v-model="formData.css_selector"
              type="text"
              placeholder="e.g., #main-content img"
              class="mt-1 block w-full rounded-md border-gray-300 text-sm shadow-sm focus:border-indigo-500 focus:ring-indigo-500"
            />
          </div>

          <!-- HTML Snippet (optional) -->
          <div class="mb-6">
            <label
              for="html-snippet"
              class="block text-sm font-medium text-gray-700"
            >
              HTML Snippet
              <span class="text-xs text-gray-400">(optional)</span>
            </label>
            <textarea
              id="html-snippet"
              v-model="formData.html_snippet"
              rows="2"
              placeholder="<img src='...' />"
              class="mt-1 block w-full rounded-md border-gray-300 font-mono text-sm shadow-sm focus:border-indigo-500 focus:ring-indigo-500"
            ></textarea>
          </div>

          <!-- Error Message -->
          <div
            v-if="error"
            class="mb-4 rounded-md bg-red-50 p-3 text-sm text-red-700"
          >
            {{ error }}
          </div>

          <!-- Actions -->
          <div class="flex items-center justify-end space-x-3">
            <button
              type="button"
              class="rounded-md border border-gray-300 bg-white px-4 py-2 text-sm font-medium text-gray-700 shadow-sm hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-indigo-500 focus:ring-offset-2"
              @click="$emit('close')"
            >
              Cancel
            </button>
            <button
              type="submit"
              class="inline-flex items-center rounded-md bg-indigo-600 px-4 py-2 text-sm font-semibold text-white shadow-sm hover:bg-indigo-500 focus:outline-none focus:ring-2 focus:ring-indigo-500 focus:ring-offset-2 disabled:cursor-not-allowed disabled:opacity-50"
              :disabled="submitting"
            >
              <LoadingSpinner
                v-if="submitting"
                size="sm"
                color="white"
                class="mr-2"
              />
              Add Finding
            </button>
          </div>
        </form>
      </div>
    </div>
  </Transition>
</template>

<script setup>
import { computed, reactive, ref } from 'vue'
import LoadingSpinner from '../common/LoadingSpinner.vue'

const props = defineProps({
  show: {
    type: Boolean,
    default: false,
  },
  pages: {
    type: Array,
    default: () => [],
  },
  criteria: {
    type: Array,
    default: () => [],
  },
})

const emit = defineEmits(['close', 'submit'])

const formData = reactive({
  page_id: '',
  criterion_id: '',
  severity: 'moderate',
  description: '',
  css_selector: '',
  html_snippet: '',
})

const submitting = ref(false)
const error = ref(null)

// Group criteria by level for select optgroups
const criteriaByLevel = computed(() => {
  const groups = {
    A: { level: 'A', criteria: [] },
    AA: { level: 'AA', criteria: [] },
    AAA: { level: 'AAA', criteria: [] },
  }

  for (const criterion of props.criteria) {
    if (groups[criterion.level]) {
      groups[criterion.level].criteria.push(criterion)
    }
  }

  return Object.values(groups).filter((g) => g.criteria.length > 0)
})

function truncateUrl(url, maxLength) {
  if (!url) return ''
  return url.length > maxLength ? url.substring(0, maxLength - 3) + '...' : url
}

function resetForm() {
  formData.page_id = ''
  formData.criterion_id = ''
  formData.severity = 'moderate'
  formData.description = ''
  formData.css_selector = ''
  formData.html_snippet = ''
  error.value = null
}

async function handleSubmit() {
  submitting.value = true
  error.value = null

  try {
    // Emit submit with form data
    emit('submit', {
      page_id: formData.page_id,
      criterion_id: formData.criterion_id,
      severity: formData.severity,
      description: formData.description,
      css_selector: formData.css_selector || null,
      html_snippet: formData.html_snippet || null,
    })

    // Reset form on success (parent will close modal)
    resetForm()
  } catch (err) {
    error.value = err.message || 'Failed to create finding'
  } finally {
    submitting.value = false
  }
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

/* Zoom transition for modal */
.zoom-enter-active,
.zoom-leave-active {
  transition: all 0.2s ease;
}

.zoom-enter-from,
.zoom-leave-to {
  opacity: 0;
  transform: scale(0.95);
}
</style>
