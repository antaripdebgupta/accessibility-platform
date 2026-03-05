<template>
  <div class="min-h-screen bg-gray-50">
    <!-- Navigation -->
    <nav class="border-b border-gray-200 bg-white">
      <div class="mx-auto max-w-7xl px-4 sm:px-6 lg:px-8">
        <div class="flex h-16 items-center">
          <RouterLink
            to="/dashboard"
            class="flex items-center text-gray-500 hover:text-gray-700"
          >
            <svg
              class="mr-2 h-5 w-5"
              fill="none"
              stroke="currentColor"
              viewBox="0 0 24 24"
            >
              <path
                stroke-linecap="round"
                stroke-linejoin="round"
                stroke-width="2"
                d="M10 19l-7-7m0 0l7-7m-7 7h18"
              />
            </svg>
            Back to Dashboard
          </RouterLink>
        </div>
      </div>
    </nav>

    <!-- Main Content -->
    <main class="py-8">
      <div class="mx-auto max-w-2xl px-4 sm:px-6 lg:px-8">
        <!-- Page Header -->
        <div class="mb-8">
          <h1 class="text-2xl font-bold text-gray-900">New Evaluation</h1>
          <p class="mt-2 text-sm text-gray-500">
            Create a new WCAG accessibility evaluation project
          </p>
        </div>

        <!-- Form Card -->
        <div class="rounded-lg border border-gray-200 bg-white p-6 shadow-sm">
          <form @submit.prevent="handleSubmit" class="space-y-6">
            <!-- Title -->
            <div>
              <label
                for="title"
                class="block text-sm font-medium text-gray-700"
              >
                Project Title <span class="text-red-500">*</span>
              </label>
              <input
                id="title"
                v-model="form.title"
                type="text"
                required
                placeholder="e.g., Company Website Accessibility Audit"
                class="mt-1 block w-full rounded-md border border-gray-300 px-3 py-2 shadow-sm focus:border-indigo-500 focus:outline-none focus:ring-1 focus:ring-indigo-500"
                :class="{ 'border-red-300': errors.title }"
              />
              <p v-if="errors.title" class="mt-1 text-sm text-red-600">
                {{ errors.title }}
              </p>
            </div>

            <!-- Target URL -->
            <div>
              <label
                for="target_url"
                class="block text-sm font-medium text-gray-700"
              >
                Target URL <span class="text-red-500">*</span>
              </label>
              <input
                id="target_url"
                v-model="form.target_url"
                type="url"
                required
                placeholder="https://example.com"
                class="mt-1 block w-full rounded-md border border-gray-300 px-3 py-2 shadow-sm focus:border-indigo-500 focus:outline-none focus:ring-1 focus:ring-indigo-500"
                :class="{ 'border-red-300': errors.target_url }"
              />
              <p v-if="errors.target_url" class="mt-1 text-sm text-red-600">
                {{ errors.target_url }}
              </p>
              <p class="mt-1 text-xs text-gray-500">
                The website URL to evaluate. Must start with https://
              </p>
            </div>

            <!-- WCAG Version -->
            <div>
              <label
                for="wcag_version"
                class="block text-sm font-medium text-gray-700"
              >
                WCAG Version
              </label>
              <select
                id="wcag_version"
                v-model="form.wcag_version"
                class="mt-1 block w-full rounded-md border border-gray-300 px-3 py-2 shadow-sm focus:border-indigo-500 focus:outline-none focus:ring-1 focus:ring-indigo-500"
              >
                <option value="2.1">WCAG 2.1</option>
                <option value="2.2">WCAG 2.2</option>
              </select>
            </div>

            <!-- Conformance Level -->
            <div>
              <label
                for="conformance_level"
                class="block text-sm font-medium text-gray-700"
              >
                Conformance Level
              </label>
              <select
                id="conformance_level"
                v-model="form.conformance_level"
                class="mt-1 block w-full rounded-md border border-gray-300 px-3 py-2 shadow-sm focus:border-indigo-500 focus:outline-none focus:ring-1 focus:ring-indigo-500"
              >
                <option value="A">Level A</option>
                <option value="AA">Level AA (Recommended)</option>
                <option value="AAA">Level AAA</option>
              </select>
              <p class="mt-1 text-xs text-gray-500">
                Level AA is recommended for most websites and is required by
                many regulations.
              </p>
            </div>

            <!-- Error Message -->
            <div v-if="submitError" class="rounded-md bg-red-50 p-4">
              <div class="flex">
                <svg
                  class="h-5 w-5 text-red-400"
                  fill="none"
                  stroke="currentColor"
                  viewBox="0 0 24 24"
                >
                  <path
                    stroke-linecap="round"
                    stroke-linejoin="round"
                    stroke-width="2"
                    d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z"
                  />
                </svg>
                <div class="ml-3">
                  <p class="text-sm font-medium text-red-800">
                    {{ submitError }}
                  </p>
                </div>
              </div>
            </div>

            <!-- Actions -->
            <div class="flex items-center justify-end space-x-4 pt-4">
              <RouterLink
                to="/dashboard"
                class="rounded-md px-4 py-2 text-sm font-medium text-gray-700 hover:bg-gray-100"
              >
                Cancel
              </RouterLink>
              <button
                type="submit"
                :disabled="isSubmitting"
                class="inline-flex items-center rounded-md bg-indigo-600 px-4 py-2 text-sm font-semibold text-white shadow-sm hover:bg-indigo-500 disabled:cursor-not-allowed disabled:opacity-50"
              >
                <svg
                  v-if="isSubmitting"
                  class="-ml-0.5 mr-2 h-4 w-4 animate-spin"
                  fill="none"
                  viewBox="0 0 24 24"
                >
                  <circle
                    class="opacity-25"
                    cx="12"
                    cy="12"
                    r="10"
                    stroke="currentColor"
                    stroke-width="4"
                  ></circle>
                  <path
                    class="opacity-75"
                    fill="currentColor"
                    d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"
                  ></path>
                </svg>
                {{ isSubmitting ? 'Creating...' : 'Create Evaluation' }}
              </button>
            </div>
          </form>
        </div>
      </div>
    </main>
  </div>
</template>

<script setup>
import { reactive, ref } from 'vue'
import { RouterLink, useRouter } from 'vue-router'
import { useEvaluationsStore } from '../stores/evaluations'

const router = useRouter()
const evaluationsStore = useEvaluationsStore()

const form = reactive({
  title: '',
  target_url: '',
  wcag_version: '2.1',
  conformance_level: 'AA',
})

const errors = reactive({
  title: '',
  target_url: '',
})

const isSubmitting = ref(false)
const submitError = ref('')

function validateForm() {
  let isValid = true
  errors.title = ''
  errors.target_url = ''

  // Validate title
  if (!form.title.trim()) {
    errors.title = 'Title is required'
    isValid = false
  } else if (form.title.length > 255) {
    errors.title = 'Title must be 255 characters or less'
    isValid = false
  }

  // Validate URL
  if (!form.target_url.trim()) {
    errors.target_url = 'Target URL is required'
    isValid = false
  } else if (!form.target_url.startsWith('https://')) {
    errors.target_url = 'URL must start with https://'
    isValid = false
  } else {
    try {
      new URL(form.target_url)
    } catch {
      errors.target_url = 'Please enter a valid URL'
      isValid = false
    }
  }

  return isValid
}

async function handleSubmit() {
  submitError.value = ''

  if (!validateForm()) {
    return
  }

  isSubmitting.value = true

  try {
    const created = await evaluationsStore.create({
      title: form.title.trim(),
      target_url: form.target_url.trim(),
      wcag_version: form.wcag_version,
      conformance_level: form.conformance_level,
    })

    router.push(`/evaluations/${created.id}`)
  } catch (error) {
    submitError.value =
      error.message || 'Failed to create evaluation. Please try again.'
  } finally {
    isSubmitting.value = false
  }
}
</script>
