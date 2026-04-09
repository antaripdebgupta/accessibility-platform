<template>
  <Transition
    enter-active-class="transform ease-out duration-300 transition"
    enter-from-class="translate-y-2 opacity-0 sm:translate-y-0 sm:translate-x-2"
    enter-to-class="translate-y-0 opacity-100 sm:translate-x-0"
    leave-active-class="transition ease-in duration-100"
    leave-from-class="opacity-100"
    leave-to-class="opacity-0"
  >
    <div
      v-if="visible"
      class="pointer-events-auto w-full max-w-md overflow-hidden rounded-lg bg-red-50 shadow-lg ring-1 ring-red-200"
      role="alert"
      aria-live="assertive"
    >
      <div class="p-4">
        <div class="flex items-start">
          <!-- Error Icon -->
          <div class="shrink-0">
            <svg
              class="h-5 w-5 text-red-500"
              fill="none"
              stroke="currentColor"
              viewBox="0 0 24 24"
              aria-hidden="true"
            >
              <path
                stroke-linecap="round"
                stroke-linejoin="round"
                stroke-width="2"
                d="M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z"
              />
            </svg>
          </div>

          <!-- Message -->
          <div class="ml-3 w-0 flex-1">
            <p class="text-sm font-medium text-red-800">
              {{ title }}
            </p>
            <p v-if="message" class="mt-1 text-sm text-red-600">
              {{ message }}
            </p>
          </div>

          <!-- Close Button -->
          <div class="ml-4 flex shrink-0">
            <button
              type="button"
              class="inline-flex rounded-md text-red-400 hover:text-red-500 focus:outline-none focus:ring-2 focus:ring-red-500 focus:ring-offset-2"
              @click="handleClose"
            >
              <span class="sr-only">Close</span>
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
                  d="M6 18L18 6M6 6l12 12"
                />
              </svg>
            </button>
          </div>
        </div>
      </div>
    </div>
  </Transition>
</template>

<script setup>
import { onUnmounted, ref, watch } from 'vue'

const props = defineProps({
  title: {
    type: String,
    default: 'Error',
  },
  message: {
    type: String,
    default: '',
  },
  show: {
    type: Boolean,
    default: false,
  },
  duration: {
    type: Number,
    default: 5000, // Auto-dismiss after 5 seconds
  },
})

const emit = defineEmits(['close'])

const visible = ref(props.show)
let dismissTimer = null

// Watch for show prop changes
watch(
  () => props.show,
  (newVal) => {
    visible.value = newVal
    if (newVal && props.duration > 0) {
      startDismissTimer()
    }
  },
)

function startDismissTimer() {
  clearDismissTimer()
  dismissTimer = setTimeout(() => {
    handleClose()
  }, props.duration)
}

function clearDismissTimer() {
  if (dismissTimer) {
    clearTimeout(dismissTimer)
    dismissTimer = null
  }
}

function handleClose() {
  clearDismissTimer()
  visible.value = false
  emit('close')
}

onUnmounted(() => {
  clearDismissTimer()
})
</script>
