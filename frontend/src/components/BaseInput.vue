<template>
  <div class="space-y-1.5">
    <label 
      v-if="$slots.label || label" 
      :for="id" 
      class="block text-sm font-medium text-gray-700"
    >
      <slot name="label">{{ label }}</slot>
      <span v-if="required" class="text-red-500 ml-0.5">*</span>
    </label>
    <div class="relative">
      <input
        :id="id"
        :type="type"
        :value="modelValue"
        :disabled="disabled"
        :placeholder="placeholder"
        :required="required"
        :aria-invalid="!!error"
        :aria-describedby="error ? `${id}-error` : undefined"
        :class="inputClasses"
        @input="$emit('update:modelValue', $event.target.value)"
        v-bind="$attrs"
      />
      <div 
        v-if="error" 
        class="absolute inset-y-0 right-0 flex items-center pr-3 pointer-events-none"
      >
        <svg class="h-5 w-5 text-red-500" viewBox="0 0 20 20" fill="currentColor">
          <path fill-rule="evenodd" d="M18 10a8 8 0 11-16 0 8 8 0 0116 0zm-7 4a1 1 0 11-2 0 1 1 0 012 0zm-1-9a1 1 0 00-1 1v4a1 1 0 102 0V6a1 1 0 00-1-1z" clip-rule="evenodd" />
        </svg>
      </div>
    </div>
    <p 
      v-if="error" 
      :id="`${id}-error`" 
      class="text-sm text-red-600"
      role="alert"
    >
      {{ error }}
    </p>
    <p 
      v-else-if="hint" 
      class="text-sm text-gray-500"
    >
      {{ hint }}
    </p>
  </div>
</template>

<script setup>
import { computed } from 'vue';

const props = defineProps({
  id: {
    type: String,
    required: true
  },
  modelValue: {
    type: [String, Number],
    default: ''
  },
  type: {
    type: String,
    default: 'text'
  },
  label: {
    type: String,
    default: ''
  },
  placeholder: {
    type: String,
    default: ''
  },
  error: {
    type: String,
    default: ''
  },
  hint: {
    type: String,
    default: ''
  },
  disabled: {
    type: Boolean,
    default: false
  },
  required: {
    type: Boolean,
    default: false
  }
});

defineEmits(['update:modelValue']);

const inputClasses = computed(() => [
  'block w-full px-3.5 py-2.5 text-gray-900 text-sm rounded-lg border transition-colors duration-150',
  'placeholder:text-gray-400',
  'focus:ring-2 focus:ring-offset-0',
  props.error 
    ? 'border-red-300 focus:border-red-500 focus:ring-red-500/20 pr-10' 
    : 'border-gray-300 focus:border-primary-500 focus:ring-primary-500/20',
  props.disabled ? 'bg-gray-50 text-gray-500 cursor-not-allowed' : 'bg-white'
]);
</script>
