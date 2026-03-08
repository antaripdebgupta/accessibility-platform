<template>
  <div :class="bannerClasses">
    <!-- Icon -->
    <div class="mb-3">
      <svg
        v-if="verdict === 'CONFORMS'"
        class="mx-auto h-12 w-12"
        fill="none"
        stroke="currentColor"
        viewBox="0 0 24 24"
        aria-hidden="true"
      >
        <path
          stroke-linecap="round"
          stroke-linejoin="round"
          stroke-width="2"
          d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z"
        />
      </svg>
      <svg
        v-else-if="verdict === 'DOES_NOT_CONFORM'"
        class="mx-auto h-12 w-12"
        fill="none"
        stroke="currentColor"
        viewBox="0 0 24 24"
        aria-hidden="true"
      >
        <path
          stroke-linecap="round"
          stroke-linejoin="round"
          stroke-width="2"
          d="M10 14l2-2m0 0l2-2m-2 2l-2-2m2 2l2 2m7-2a9 9 0 11-18 0 9 9 0 0118 0z"
        />
      </svg>
      <svg
        v-else
        class="mx-auto h-12 w-12"
        fill="none"
        stroke="currentColor"
        viewBox="0 0 24 24"
        aria-hidden="true"
      >
        <path
          stroke-linecap="round"
          stroke-linejoin="round"
          stroke-width="2"
          d="M8.228 9c.549-1.165 2.03-2 3.772-2 2.21 0 4 1.343 4 3 0 1.4-1.278 2.575-3.006 2.907-.542.104-.994.54-.994 1.093m0 3h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z"
        />
      </svg>
    </div>

    <!-- Verdict Text -->
    <h2 :class="verdictTextClasses">
      {{ verdictLabel }}
    </h2>

    <!-- Subtitle -->
    <p :class="subtitleClasses">
      {{ verdictSubtitle }}
    </p>

    <!-- Compact mode: show inline stats -->
    <div
      v-if="compact"
      class="mt-3 flex items-center justify-center space-x-4 text-sm"
    >
      <span>{{ criteriaFailed }} failed</span>
      <span class="text-current opacity-50">·</span>
      <span>{{ criteriaTotal - criteriaFailed }} passed</span>
    </div>
  </div>
</template>

<script setup>
import { computed } from 'vue'

const props = defineProps({
  verdict: {
    type: String,
    required: true,
    validator: (v) =>
      ['CONFORMS', 'DOES_NOT_CONFORM', 'CANNOT_DETERMINE'].includes(v),
  },
  criteriaFailed: {
    type: Number,
    default: 0,
  },
  criteriaTotal: {
    type: Number,
    default: 0,
  },
  compact: {
    type: Boolean,
    default: false,
  },
})

const bannerClasses = computed(() => {
  const base = ['rounded-lg', 'text-center', 'w-full']

  if (props.compact) {
    base.push('p-4')
  } else {
    base.push('p-8', 'min-h-[140px]')
  }

  switch (props.verdict) {
    case 'CONFORMS':
      base.push('bg-green-50', 'text-green-800', 'border', 'border-green-200')
      break
    case 'DOES_NOT_CONFORM':
      base.push('bg-red-50', 'text-red-800', 'border', 'border-red-200')
      break
    default:
      base.push(
        'bg-yellow-50',
        'text-yellow-800',
        'border',
        'border-yellow-200',
      )
  }

  return base
})

const verdictTextClasses = computed(() => {
  const base = ['font-bold']

  if (props.compact) {
    base.push('text-xl')
  } else {
    base.push('text-3xl')
  }

  return base
})

const subtitleClasses = computed(() => {
  const base = ['mt-2']

  if (props.compact) {
    base.push('text-sm')
  } else {
    base.push('text-base')
  }

  switch (props.verdict) {
    case 'CONFORMS':
      base.push('text-green-600')
      break
    case 'DOES_NOT_CONFORM':
      base.push('text-red-600')
      break
    default:
      base.push('text-yellow-600')
  }

  return base
})

const verdictLabel = computed(() => {
  switch (props.verdict) {
    case 'CONFORMS':
      return 'Conforms to WCAG'
    case 'DOES_NOT_CONFORM':
      return 'Does Not Conform to WCAG'
    default:
      return 'Cannot Determine Conformance'
  }
})

const verdictSubtitle = computed(() => {
  switch (props.verdict) {
    case 'CONFORMS':
      return 'All evaluated criteria passed'
    case 'DOES_NOT_CONFORM':
      return `${props.criteriaFailed} of ${props.criteriaTotal} criteria failed`
    default:
      return 'Insufficient data — ensure scan and review are complete'
  }
})
</script>
