<template>
  <div class="flex flex-col items-center justify-center py-12 px-4 text-center">
    <!-- Icon slot or default icon -->
    <div
      class="mx-auto flex h-16 w-16 items-center justify-center rounded-full bg-gray-100"
    >
      <slot name="icon">
        <svg
          class="h-8 w-8 text-gray-400"
          fill="none"
          stroke="currentColor"
          viewBox="0 0 24 24"
        >
          <path
            stroke-linecap="round"
            stroke-linejoin="round"
            stroke-width="1.5"
            d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z"
          />
        </svg>
      </slot>
    </div>

    <!-- Title -->
    <h3 class="mt-4 text-lg font-medium text-gray-900">
      {{ title }}
    </h3>

    <!-- Message -->
    <p class="mt-2 max-w-sm text-sm text-gray-500">
      {{ message }}
    </p>

    <!-- Action button -->
    <div v-if="actionLabel" class="mt-6">
      <button
        type="button"
        class="inline-flex items-center rounded-md bg-indigo-600 px-4 py-2 text-sm font-semibold text-white shadow-sm hover:bg-indigo-500 focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-indigo-600"
        @click="$emit('action')"
      >
        <slot name="action-icon">
          <svg
            class="-ml-0.5 mr-1.5 h-4 w-4"
            fill="none"
            stroke="currentColor"
            viewBox="0 0 24 24"
          >
            <path
              stroke-linecap="round"
              stroke-linejoin="round"
              stroke-width="2"
              d="M12 4v16m8-8H4"
            />
          </svg>
        </slot>
        {{ actionLabel }}
      </button>
    </div>

    <!-- Additional slot for custom content -->
    <slot></slot>
  </div>
</template>

<script setup>
defineProps({
  title: {
    type: String,
    required: true,
  },
  message: {
    type: String,
    default: '',
  },
  actionLabel: {
    type: String,
    default: '',
  },
})

defineEmits(['action'])
</script>
