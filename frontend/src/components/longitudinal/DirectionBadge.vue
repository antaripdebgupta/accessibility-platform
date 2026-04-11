<template>
  <span
    :class="[
      'inline-flex items-center rounded-full px-2 py-0.5 text-xs font-medium',
      directionClasses,
    ]"
  >
    <component :is="directionIcon" class="mr-1 h-3 w-3" />
    {{ directionLabel }}
  </span>
</template>

<script setup>
import { computed, h } from 'vue'

const props = defineProps({
  direction: {
    type: String,
    required: true,
  },
})

const directionClasses = computed(() => {
  switch (props.direction) {
    case 'improving':
      return 'bg-green-100 text-green-800'
    case 'regressing':
      return 'bg-red-100 text-red-800'
    case 'new':
      return 'bg-orange-100 text-orange-800'
    default:
      return 'bg-gray-100 text-gray-800'
  }
})

const directionLabel = computed(() => {
  switch (props.direction) {
    case 'improving':
      return 'Improving'
    case 'regressing':
      return 'Regressing'
    case 'new':
      return 'New'
    default:
      return 'Stable'
  }
})

// Inline SVG icons
const ArrowDownIcon = {
  render() {
    return h(
      'svg',
      {
        xmlns: 'http://www.w3.org/2000/svg',
        fill: 'none',
        viewBox: '0 0 24 24',
        'stroke-width': '2',
        stroke: 'currentColor',
      },
      [
        h('path', {
          'stroke-linecap': 'round',
          'stroke-linejoin': 'round',
          d: 'M19 9l-7 7-7-7',
        }),
      ],
    )
  },
}

const ArrowUpIcon = {
  render() {
    return h(
      'svg',
      {
        xmlns: 'http://www.w3.org/2000/svg',
        fill: 'none',
        viewBox: '0 0 24 24',
        'stroke-width': '2',
        stroke: 'currentColor',
      },
      [
        h('path', {
          'stroke-linecap': 'round',
          'stroke-linejoin': 'round',
          d: 'M5 15l7-7 7 7',
        }),
      ],
    )
  },
}

const ArrowRightIcon = {
  render() {
    return h(
      'svg',
      {
        xmlns: 'http://www.w3.org/2000/svg',
        fill: 'none',
        viewBox: '0 0 24 24',
        'stroke-width': '2',
        stroke: 'currentColor',
      },
      [
        h('path', {
          'stroke-linecap': 'round',
          'stroke-linejoin': 'round',
          d: 'M17 8l4 4m0 0l-4 4m4-4H3',
        }),
      ],
    )
  },
}

const PlusIcon = {
  render() {
    return h(
      'svg',
      {
        xmlns: 'http://www.w3.org/2000/svg',
        fill: 'none',
        viewBox: '0 0 24 24',
        'stroke-width': '2',
        stroke: 'currentColor',
      },
      [
        h('path', {
          'stroke-linecap': 'round',
          'stroke-linejoin': 'round',
          d: 'M12 4.5v15m7.5-7.5h-15',
        }),
      ],
    )
  },
}

const directionIcon = computed(() => {
  switch (props.direction) {
    case 'improving':
      return ArrowDownIcon // Down = less issues = good
    case 'regressing':
      return ArrowUpIcon // Up = more issues = bad
    case 'new':
      return PlusIcon
    default:
      return ArrowRightIcon
  }
})
</script>
