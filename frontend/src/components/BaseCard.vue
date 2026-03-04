<template>
  <div :class="cardClasses">
    <div v-if="$slots.header || title" :class="headerClasses">
      <slot name="header">
        <h2 v-if="title" class="text-lg font-semibold text-gray-900">{{ title }}</h2>
        <p v-if="description" class="mt-1 text-sm text-gray-500">{{ description }}</p>
      </slot>
    </div>
    <div :class="bodyClasses">
      <slot />
    </div>
    <div v-if="$slots.footer" :class="footerClasses">
      <slot name="footer" />
    </div>
  </div>
</template>

<script setup>
import { computed } from 'vue';

const props = defineProps({
  title: {
    type: String,
    default: ''
  },
  description: {
    type: String,
    default: ''
  },
  padding: {
    type: String,
    default: 'md',
    validator: (value) => ['none', 'sm', 'md', 'lg'].includes(value)
  },
  shadow: {
    type: String,
    default: 'soft',
    validator: (value) => ['none', 'soft', 'medium'].includes(value)
  },
  rounded: {
    type: String,
    default: 'xl',
    validator: (value) => ['md', 'lg', 'xl', '2xl'].includes(value)
  }
});

const paddingClasses = {
  none: '',
  sm: 'px-4 py-3',
  md: 'px-6 py-5',
  lg: 'px-8 py-6'
};

const shadowClasses = {
  none: '',
  soft: 'shadow-soft',
  medium: 'shadow-medium'
};

const roundedClasses = {
  md: 'rounded-md',
  lg: 'rounded-lg',
  xl: 'rounded-xl',
  '2xl': 'rounded-2xl'
};

const cardClasses = computed(() => [
  'bg-white border border-gray-200',
  shadowClasses[props.shadow],
  roundedClasses[props.rounded]
]);

const headerClasses = computed(() => [
  'border-b border-gray-200',
  paddingClasses[props.padding]
]);

const bodyClasses = computed(() => [
  paddingClasses[props.padding]
]);

const footerClasses = computed(() => [
  'border-t border-gray-100 bg-gray-50/50',
  paddingClasses[props.padding],
  props.rounded === '2xl' ? 'rounded-b-2xl' : props.rounded === 'xl' ? 'rounded-b-xl' : 'rounded-b-lg'
]);
</script>
