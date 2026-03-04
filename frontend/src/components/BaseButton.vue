<template>
  <!-- Render as a router link when `to` prop is provided to avoid nesting a button inside an anchor -->
  <RouterLink
    v-if="to"
    :to="to"
    :class="buttonClasses"
    v-bind="$attrs"
    role="button"
  >
    <span v-if="loading" class="mr-2">
      <svg class="animate-spin h-4 w-4" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
        <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"></circle>
        <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
      </svg>
    </span>
    <slot />
  </RouterLink>

  <button
    v-else
    :type="type"
    :disabled="disabled || loading"
    :class="buttonClasses"
    v-bind="$attrs"
  >
    <span v-if="loading" class="mr-2">
      <svg class="animate-spin h-4 w-4" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
        <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"></circle>
        <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
      </svg>
    </span>
    <slot />
  </button>
</template>

<script setup>
import { computed } from 'vue';
import { RouterLink } from 'vue-router';

const props = defineProps({
  variant: {
    type: String,
    default: 'secondary',
    validator: (value) => ['primary', 'secondary', 'danger', 'ghost'].includes(value)
  },
  size: {
    type: String,
    default: 'md',
    validator: (value) => ['sm', 'md', 'lg'].includes(value)
  },
  disabled: {
    type: Boolean,
    default: false
  },
  loading: {
    type: Boolean,
    default: false
  },
  type: {
    type: String,
    default: 'button'
  },
  fullWidth: {
    type: Boolean,
    default: false
  }
  ,
  to: {
    type: [String, Object],
    default: null
  }
});

const baseClasses = 'inline-flex items-center justify-center font-medium rounded-lg transition-all duration-150 focus:outline-none focus:ring-2 focus:ring-offset-2';

const sizeClasses = {
  sm: 'px-3 py-1.5 text-sm',
  md: 'px-4 py-2.5 text-sm',
  lg: 'px-6 py-3 text-base'
};

const variantClasses = {
  primary: 'bg-primary-600 text-white hover:bg-primary-700 focus:ring-primary-500 shadow-sm',
  secondary: 'bg-white text-gray-700 border border-gray-300 hover:bg-gray-50 focus:ring-primary-500 shadow-sm',
  danger: 'bg-red-600 text-white hover:bg-red-700 focus:ring-red-500 shadow-sm',
  ghost: 'bg-transparent text-gray-600 hover:bg-gray-100 hover:text-gray-900 focus:ring-primary-500'
};

const buttonClasses = computed(() => [
  baseClasses,
  sizeClasses[props.size],
  variantClasses[props.variant],
  props.disabled || props.loading ? 'opacity-50 cursor-not-allowed' : '',
  props.fullWidth ? 'w-full' : ''
]);
</script>

<!-- make RouterLink available in the template when used -->
<script>
export default {
  components: { RouterLink }
}
</script>
