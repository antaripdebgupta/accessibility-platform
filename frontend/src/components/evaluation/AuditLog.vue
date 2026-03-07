<template>
  <div class="audit-log">
    <!-- Loading State -->
    <div v-if="loading" class="space-y-4">
      <div v-for="n in 3" :key="n" class="flex items-start space-x-3">
        <div
          class="h-3 w-3 rounded-full bg-gray-200 animate-pulse mt-1.5"
        ></div>
        <div class="flex-1 space-y-2">
          <div class="h-4 w-1/3 bg-gray-200 rounded animate-pulse"></div>
          <div class="h-3 w-1/2 bg-gray-200 rounded animate-pulse"></div>
        </div>
      </div>
    </div>

    <!-- Empty State -->
    <div v-else-if="!entries.length" class="text-center py-8">
      <svg
        class="mx-auto h-8 w-8 text-gray-400"
        fill="none"
        stroke="currentColor"
        viewBox="0 0 24 24"
        aria-hidden="true"
      >
        <path
          stroke-linecap="round"
          stroke-linejoin="round"
          stroke-width="1.5"
          d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z"
        />
      </svg>
      <p class="mt-2 text-sm text-gray-500">No activity recorded yet</p>
    </div>

    <!-- Timeline -->
    <div v-else class="relative">
      <!-- Vertical line -->
      <div
        class="absolute left-[5px] top-2 bottom-2 w-0.5 bg-gray-200"
        aria-hidden="true"
      ></div>

      <!-- Entries -->
      <ul class="space-y-4">
        <li v-for="entry in entries" :key="entry.id" class="relative pl-6">
          <!-- Dot -->
          <div
            class="absolute left-0 top-1.5 h-3 w-3 rounded-full border-2 border-white"
            :class="getDotColor(entry.action)"
          ></div>

          <!-- Content -->
          <div class="min-w-0">
            <div class="flex items-center justify-between">
              <p class="text-sm font-medium text-gray-900">
                {{ getActionLabel(entry.action) }}
              </p>
              <span class="text-xs text-gray-500">
                {{ getRelativeTime(entry.created_at) }}
              </span>
            </div>
            <!-- Entity label (which issue/finding this refers to) -->
            <p
              v-if="entry.entity_label"
              class="mt-0.5 text-xs font-medium text-indigo-600"
            >
              {{ entry.entity_label }}
            </p>
            <p class="mt-0.5 text-xs text-gray-500">
              {{ entry.display_name || entry.user_email || 'System' }}
            </p>

            <!-- Expandable diff section -->
            <div v-if="entry.before_state && entry.after_state" class="mt-2">
              <button
                type="button"
                class="flex items-center text-xs text-gray-500 hover:text-gray-700"
                @click="toggleExpanded(entry.id)"
              >
                <svg
                  class="h-4 w-4 transition-transform"
                  :class="{ 'rotate-90': expandedIds.has(entry.id) }"
                  fill="none"
                  stroke="currentColor"
                  viewBox="0 0 24 24"
                >
                  <path
                    stroke-linecap="round"
                    stroke-linejoin="round"
                    stroke-width="2"
                    d="M9 5l7 7-7 7"
                  />
                </svg>
                <span class="ml-1">View changes</span>
              </button>

              <div
                v-if="expandedIds.has(entry.id)"
                class="mt-2 rounded-md bg-gray-50 p-3 text-xs"
              >
                <div class="space-y-1">
                  <div
                    v-for="(value, key) in entry.after_state"
                    :key="key"
                    class="flex"
                  >
                    <span class="font-medium text-gray-600 w-24"
                      >{{ key }}:</span
                    >
                    <span
                      class="text-red-600 line-through mr-2"
                      v-if="entry.before_state[key] !== undefined"
                    >
                      {{ entry.before_state[key] }}
                    </span>
                    <span class="text-green-600">{{ value }}</span>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </li>
      </ul>
    </div>
  </div>
</template>

<script setup>
import { onMounted, ref, watch } from 'vue'
import api from '../../lib/api'

const props = defineProps({
  evaluationId: {
    type: String,
    required: true,
  },
})

const loading = ref(false)
const entries = ref([])
const expandedIds = ref(new Set())

// Action labels map
const actionLabels = {
  'evaluation.created': 'Evaluation created',
  'evaluation.updated': 'Evaluation updated',
  'evaluation.deleted': 'Evaluation deleted',
  'evaluation.advanced': 'Status advanced',
  'finding.confirmed': 'Finding confirmed',
  'finding.dismissed': 'Finding dismissed',
  'finding.reopened': 'Finding reopened',
  'finding.created': 'Finding added',
  'finding.updated': 'Finding updated',
  'scan.started': 'Scan started',
  'scan.completed': 'Scan completed',
  'crawl.started': 'Exploration started',
  'crawl.completed': 'Exploration completed',
  'report.generated': 'Report generated',
  'report.downloaded': 'Report downloaded',
}

function getActionLabel(action) {
  return (
    actionLabels[action] ||
    action.replace('.', ' ').replace(/^\w/, (c) => c.toUpperCase())
  )
}

function getDotColor(action) {
  if (action.includes('confirmed')) return 'bg-green-500'
  if (action.includes('dismissed')) return 'bg-gray-400'
  if (action.includes('created')) return 'bg-blue-500'
  if (action.includes('deleted')) return 'bg-red-500'
  if (action.includes('started')) return 'bg-yellow-500'
  if (action.includes('completed')) return 'bg-green-500'
  return 'bg-indigo-500'
}

function getRelativeTime(dateString) {
  const date = new Date(dateString)
  const now = new Date()
  const diffMs = now - date
  const diffSec = Math.floor(diffMs / 1000)
  const diffMin = Math.floor(diffSec / 60)
  const diffHour = Math.floor(diffMin / 60)
  const diffDay = Math.floor(diffHour / 24)

  if (diffSec < 60) return 'just now'
  if (diffMin < 60) return `${diffMin} minute${diffMin === 1 ? '' : 's'} ago`
  if (diffHour < 24) return `${diffHour} hour${diffHour === 1 ? '' : 's'} ago`
  if (diffDay < 7) return `${diffDay} day${diffDay === 1 ? '' : 's'} ago`

  return date.toLocaleDateString()
}

function toggleExpanded(id) {
  if (expandedIds.value.has(id)) {
    expandedIds.value.delete(id)
  } else {
    expandedIds.value.add(id)
  }
  // Trigger reactivity
  expandedIds.value = new Set(expandedIds.value)
}

async function fetchAuditLog() {
  loading.value = true
  try {
    const response = await api.get(
      `/evaluations/${props.evaluationId}/audit-log`,
    )
    entries.value = response.data.items || []
  } catch (error) {
    console.error('Failed to fetch audit log:', error)
    entries.value = []
  } finally {
    loading.value = false
  }
}

onMounted(() => {
  fetchAuditLog()
})

watch(
  () => props.evaluationId,
  () => {
    fetchAuditLog()
  },
)
</script>

<style scoped>
.rotate-90 {
  transform: rotate(90deg);
}
</style>
