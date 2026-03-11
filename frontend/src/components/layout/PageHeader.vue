<template>
  <div class="mb-8">
    <div
      class="flex flex-col gap-4 sm:flex-row sm:items-start sm:justify-between"
    >
      <!-- Left side: Back arrow + Title/Subtitle -->
      <div class="flex items-start">
        <!-- Back arrow link -->
        <RouterLink
          v-if="backTo"
          :to="backTo"
          class="mr-4 mt-1 flex h-8 w-8 items-center justify-center rounded-full text-gray-400 hover:bg-gray-100 hover:text-gray-600 focus:outline-none focus:ring-2 focus:ring-indigo-500 focus:ring-offset-2"
          aria-label="Go back"
        >
          <svg
            class="h-5 w-5"
            fill="none"
            stroke="currentColor"
            viewBox="0 0 24 24"
            aria-hidden="true"
          >
            <path
              stroke-linecap="round"
              stroke-linejoin="round"
              stroke-width="2"
              d="M10 19l-7-7m0 0l7-7m-7 7h18"
            />
          </svg>
        </RouterLink>

        <!-- Title and subtitle -->
        <div>
          <h1 class="text-xl font-bold text-gray-900 sm:text-2xl">
            {{ title }}
          </h1>
          <p v-if="subtitle" class="mt-1 text-sm text-gray-500">
            {{ subtitle }}
          </p>
        </div>
      </div>

      <!-- Right side: Action buttons slot -->
      <div class="flex items-center space-x-3">
        <slot></slot>
      </div>
    </div>
  </div>
</template>

<script setup>
import { RouterLink } from 'vue-router'

defineProps({
  /**
   * Page title (required)
   */
  title: {
    type: String,
    required: true,
  },
  /**
   * Optional subtitle displayed below the title
   */
  subtitle: {
    type: String,
    default: null,
  },
  /**
   * Optional route object for the back arrow link.
   * If provided, shows a back arrow on the left side.
   */
  backTo: {
    type: [Object, String],
    default: null,
  },
})
</script>
