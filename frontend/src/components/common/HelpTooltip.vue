<template>
  <div class="relative inline-flex items-center">
    <button
      type="button"
      class="ml-1 rounded-full p-0.5 text-gray-400 hover:text-gray-600 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:ring-offset-1 dark:text-gray-500 dark:hover:text-gray-300"
      :aria-label="ariaLabel || 'Show help'"
      @mouseenter="showTooltip = true"
      @mouseleave="showTooltip = false"
      @focus="showTooltip = true"
      @blur="showTooltip = false"
      @click="showTooltip = !showTooltip"
    >
      <svg
        class="h-4 w-4"
        fill="none"
        stroke="currentColor"
        viewBox="0 0 24 24"
        aria-hidden="true"
      >
        <path
          stroke-linecap="round"
          stroke-linejoin="round"
          stroke-width="2"
          d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z"
        />
      </svg>
    </button>

    <Transition
      enter-active-class="transition ease-out duration-200"
      enter-from-class="opacity-0 translate-y-1"
      enter-to-class="opacity-100 translate-y-0"
      leave-active-class="transition ease-in duration-150"
      leave-from-class="opacity-100 translate-y-0"
      leave-to-class="opacity-0 translate-y-1"
    >
      <div
        v-if="showTooltip"
        :class="[
          'absolute z-50 w-72 rounded-lg border bg-white p-3 text-sm shadow-lg dark:border-gray-700 dark:bg-gray-800',
          positionClasses,
        ]"
        role="tooltip"
      >
        <h4
          v-if="title"
          class="mb-1 font-semibold text-gray-900 dark:text-white"
        >
          {{ title }}
        </h4>
        <p class="text-gray-600 dark:text-gray-300">
          <slot>{{ content }}</slot>
        </p>
        <!-- Arrow -->
        <div
          :class="[
            'absolute h-2 w-2 rotate-45 border bg-white dark:border-gray-700 dark:bg-gray-800',
            arrowClasses,
          ]"
        />
      </div>
    </Transition>
  </div>
</template>

<script setup>
import { computed, ref } from 'vue'

const props = defineProps({
  title: {
    type: String,
    default: '',
  },
  content: {
    type: String,
    default: '',
  },
  position: {
    type: String,
    default: 'bottom',
    validator: (value) => ['top', 'bottom', 'left', 'right'].includes(value),
  },
  ariaLabel: {
    type: String,
    default: '',
  },
})

const showTooltip = ref(false)

const positionClasses = computed(() => {
  switch (props.position) {
    case 'top':
      return 'bottom-full left-1/2 -translate-x-1/2 mb-2'
    case 'bottom':
      return 'top-full left-1/2 -translate-x-1/2 mt-2'
    case 'left':
      return 'right-full top-1/2 -translate-y-1/2 mr-2'
    case 'right':
      return 'left-full top-1/2 -translate-y-1/2 ml-2'
    default:
      return 'top-full left-1/2 -translate-x-1/2 mt-2'
  }
})

const arrowClasses = computed(() => {
  switch (props.position) {
    case 'top':
      return 'bottom-[-5px] left-1/2 -translate-x-1/2 border-r border-b'
    case 'bottom':
      return 'top-[-5px] left-1/2 -translate-x-1/2 border-l border-t'
    case 'left':
      return 'right-[-5px] top-1/2 -translate-y-1/2 border-t border-r'
    case 'right':
      return 'left-[-5px] top-1/2 -translate-y-1/2 border-b border-l'
    default:
      return 'top-[-5px] left-1/2 -translate-x-1/2 border-l border-t'
  }
})
</script>
