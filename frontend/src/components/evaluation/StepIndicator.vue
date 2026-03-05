<template>
  <nav aria-label="Evaluation progress" class="w-full">
    <ol class="flex items-center justify-between">
      <li
        v-for="(step, index) in steps"
        :key="step.name"
        class="relative flex flex-1 flex-col items-center"
      >
        <!-- Connector line (before circle) -->
        <div
          v-if="index > 0"
          class="absolute left-0 right-1/2 top-4 -translate-y-1/2"
        >
          <div
            class="h-0.5 w-full"
            :class="[
              index <= currentStepIndex ? 'bg-green-500' : 'bg-gray-200',
            ]"
          ></div>
        </div>

        <!-- Connector line (after circle) -->
        <div
          v-if="index < steps.length - 1"
          class="absolute left-1/2 right-0 top-4 -translate-y-1/2"
        >
          <div
            class="h-0.5 w-full"
            :class="[index < currentStepIndex ? 'bg-green-500' : 'bg-gray-200']"
          ></div>
        </div>

        <!-- Step circle -->
        <div
          class="relative z-10 flex h-8 w-8 items-center justify-center rounded-full border-2 text-sm font-medium"
          :class="stepCircleClasses(index)"
          :aria-label="stepAriaLabel(step, index)"
          :aria-current="index === currentStepIndex ? 'step' : undefined"
          role="listitem"
        >
          <!-- Completed: checkmark -->
          <svg
            v-if="index < currentStepIndex"
            class="h-4 w-4 text-white"
            fill="currentColor"
            viewBox="0 0 20 20"
            aria-hidden="true"
          >
            <path
              fill-rule="evenodd"
              d="M16.707 5.293a1 1 0 010 1.414l-8 8a1 1 0 01-1.414 0l-4-4a1 1 0 011.414-1.414L8 12.586l7.293-7.293a1 1 0 011.414 0z"
              clip-rule="evenodd"
            />
          </svg>

          <!-- Current or upcoming: step number -->
          <span v-else aria-hidden="true">{{ index + 1 }}</span>
        </div>

        <!-- Step label -->
        <span class="mt-2 text-xs font-medium" :class="stepLabelClasses(index)">
          {{ step.name }}
        </span>
      </li>
    </ol>
  </nav>
</template>

<script setup>
import { computed } from 'vue'

const props = defineProps({
  /**
   * The current evaluation status string.
   * Used to determine which step is active.
   */
  currentStatus: {
    type: String,
    required: true,
  },
})

// Step definitions
const steps = [
  { name: 'Explore', statuses: ['EXPLORING', 'SAMPLING'] },
  { name: 'Scan', statuses: ['AUDITING'] },
  { name: 'Review', statuses: ['REPORTING'] },
  { name: 'Report', statuses: ['COMPLETE'] },
]

/**
 * Maps evaluation status to step index.
 *
 * DRAFT, SCOPING → step -1 (none active yet, all gray)
 * EXPLORING, SAMPLING → step 0 active (Explore)
 * AUDITING → step 1 active (Scan)
 * REPORTING → step 2 active (Review)
 * COMPLETE → step 3 (all complete, all green)
 */
const currentStepIndex = computed(() => {
  const status = props.currentStatus?.toUpperCase() || 'DRAFT'

  switch (status) {
    case 'EXPLORING':
    case 'SAMPLING':
      return 0
    case 'AUDITING':
      return 1
    case 'REPORTING':
      return 2
    case 'COMPLETE':
      return 4 // All steps complete
    case 'DRAFT':
    case 'SCOPING':
    default:
      return -1 // None active
  }
})

/**
 * Returns the CSS classes for a step circle based on its state.
 */
function stepCircleClasses(index) {
  // Completed step
  if (index < currentStepIndex.value) {
    return 'border-green-500 bg-green-500 text-white'
  }

  // Active step
  if (index === currentStepIndex.value) {
    return 'border-indigo-600 bg-indigo-600 text-white'
  }

  // Upcoming step
  return 'border-gray-300 bg-white text-gray-500'
}

/**
 * Returns the CSS classes for a step label based on its state.
 */
function stepLabelClasses(index) {
  // Completed step
  if (index < currentStepIndex.value) {
    return 'text-green-600'
  }

  // Active step
  if (index === currentStepIndex.value) {
    return 'text-indigo-600'
  }

  // Upcoming step
  return 'text-gray-500'
}

/**
 * Returns the aria-label for a step based on its state.
 */
function stepAriaLabel(step, index) {
  if (index < currentStepIndex.value) {
    return `${step.name} - Completed`
  }
  if (index === currentStepIndex.value) {
    return `${step.name} - Current step`
  }
  return `${step.name} - Upcoming`
}
</script>
