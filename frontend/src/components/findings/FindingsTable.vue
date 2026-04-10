<template>
  <div class="rounded-lg border border-gray-200 bg-white">
    <!-- Loading State -->
    <div v-if="loading" class="divide-y divide-gray-200">
      <div
        v-for="n in 5"
        :key="n"
        class="flex items-center space-x-4 px-6 py-4"
      >
        <div class="h-6 w-16 animate-pulse rounded-full bg-gray-200"></div>
        <div class="flex-1 space-y-2">
          <div class="h-4 w-1/3 animate-pulse rounded bg-gray-200"></div>
          <div class="h-3 w-2/3 animate-pulse rounded bg-gray-200"></div>
        </div>
        <div class="h-6 w-20 animate-pulse rounded-full bg-gray-200"></div>
      </div>
    </div>

    <!-- Empty State -->
    <div
      v-else-if="!findings || findings.length === 0"
      class="py-12 text-center"
    >
      <svg
        class="mx-auto h-12 w-12 text-gray-400"
        fill="none"
        stroke="currentColor"
        viewBox="0 0 24 24"
        aria-hidden="true"
      >
        <path
          stroke-linecap="round"
          stroke-linejoin="round"
          stroke-width="1.5"
          d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z"
        />
      </svg>
      <h3 class="mt-4 text-sm font-medium text-gray-900">
        No findings match your filters
      </h3>
      <p class="mt-2 text-sm text-gray-500">
        Try adjusting your filters or run a new scan.
      </p>
    </div>

    <!-- Findings Table Wrapper for mobile scroll -->
    <div v-else class="overflow-x-auto">
      <table class="min-w-full divide-y divide-gray-200">
        <thead class="bg-gray-50">
          <tr>
            <!-- Checkbox Header -->
            <th v-if="selectable" scope="col" class="w-12 px-4 py-3">
              <input
                type="checkbox"
                class="h-4 w-4 rounded border-gray-300 text-indigo-600 focus:ring-indigo-500"
                :checked="allSelected"
                :indeterminate="someSelected && !allSelected"
                @change="handleSelectAll"
              />
            </th>
            <th
              scope="col"
              class="px-6 py-3 text-left text-xs font-medium uppercase tracking-wider text-gray-500"
            >
              Severity
            </th>
            <!-- Profile Priority Column Header (only shown when profile active) -->
            <th
              v-if="activeProfile"
              scope="col"
              class="hidden px-6 py-3 text-left text-xs font-medium uppercase tracking-wider text-purple-600 sm:table-cell"
            >
              Profile Priority
            </th>
            <th
              scope="col"
              class="hidden px-6 py-3 text-left text-xs font-medium uppercase tracking-wider text-gray-500 md:table-cell"
            >
              WCAG Criterion
            </th>
            <th
              scope="col"
              class="hidden px-6 py-3 text-left text-xs font-medium uppercase tracking-wider text-gray-500 lg:table-cell"
            >
              Page
            </th>
            <th
              scope="col"
              class="px-6 py-3 text-left text-xs font-medium uppercase tracking-wider text-gray-500"
            >
              Description
            </th>
            <th
              scope="col"
              class="hidden px-6 py-3 text-left text-xs font-medium uppercase tracking-wider text-gray-500 sm:table-cell"
            >
              Status
            </th>
            <th
              scope="col"
              class="px-6 py-3 text-right text-xs font-medium uppercase tracking-wider text-gray-500"
            >
              Actions
            </th>
          </tr>
        </thead>
        <tbody class="divide-y divide-gray-200 bg-white">
          <tr
            v-for="finding in findings"
            :key="finding.id"
            class="cursor-pointer transition-colors"
            :class="[
              isSelected(finding.id) ? 'bg-blue-50' : 'hover:bg-gray-50',
              isNaForProfile(finding) ? 'opacity-50' : '',
            ]"
            @click="$emit('select', finding)"
          >
            <!-- Checkbox -->
            <td v-if="selectable" class="w-12 px-4 py-4" @click.stop>
              <input
                type="checkbox"
                class="h-4 w-4 rounded border-gray-300 text-indigo-600 focus:ring-indigo-500"
                :checked="isSelected(finding.id)"
                @change="toggleSelection(finding.id)"
              />
            </td>
            <!-- Severity -->
            <td class="whitespace-nowrap px-6 py-4">
              <SeverityBadge :severity="finding.severity || 'info'" />
            </td>

            <!-- Profile Priority (only shown when profile active) -->
            <td
              v-if="activeProfile"
              class="hidden whitespace-nowrap px-6 py-4 sm:table-cell"
            >
              <ProfilePriorityBadge
                v-if="finding.profile_priority"
                :priority="finding.profile_priority"
              />
              <span v-else class="text-xs text-gray-400">—</span>
            </td>

            <!-- WCAG Criterion -->
            <td class="hidden px-6 py-4 md:table-cell">
              <div class="text-sm font-medium text-gray-900">
                {{
                  finding.criterion_code ||
                  (finding.rule_id ? `Rule: ${finding.rule_id}` : 'N/A')
                }}
              </div>
              <div
                v-if="finding.criterion_name"
                class="max-w-xs truncate text-xs text-gray-500"
              >
                {{ finding.criterion_name }}
              </div>
            </td>

            <!-- Page URL -->
            <td class="hidden max-w-xs px-6 py-4 lg:table-cell">
              <a
                v-if="finding.page_url"
                :href="finding.page_url"
                target="_blank"
                rel="noopener noreferrer"
                class="flex items-center text-sm text-indigo-600 hover:text-indigo-500"
                @click.stop
              >
                <span class="truncate">{{
                  truncateUrl(finding.page_url)
                }}</span>
                <svg
                  class="ml-1 h-3 w-3 shrink-0"
                  fill="none"
                  stroke="currentColor"
                  viewBox="0 0 24 24"
                >
                  <path
                    stroke-linecap="round"
                    stroke-linejoin="round"
                    stroke-width="2"
                    d="M10 6H6a2 2 0 00-2 2v10a2 2 0 002 2h10a2 2 0 002-2v-4M14 4h6m0 0v6m0-6L10 14"
                  />
                </svg>
              </a>
              <span v-else class="text-sm text-gray-400">—</span>
            </td>

            <!-- Description -->
            <td class="px-6 py-4">
              <p class="line-clamp-2 text-sm text-gray-900">
                {{ finding.description }}
              </p>
            </td>

            <!-- Status -->
            <td class="hidden whitespace-nowrap px-6 py-4 sm:table-cell">
              <span
                class="inline-flex items-center rounded-full px-2.5 py-0.5 text-xs font-medium"
                :class="getStatusClasses(finding.status)"
              >
                {{ finding.status }}
              </span>
            </td>

            <!-- Actions -->
            <td
              class="whitespace-nowrap px-6 py-4 text-right text-sm font-medium"
            >
              <div class="flex items-center justify-end space-x-2">
                <button
                  v-if="finding.status === 'OPEN'"
                  type="button"
                  class="rounded px-2 py-1 text-xs font-medium text-green-600 hover:bg-green-50 focus:outline-none focus:ring-2 focus:ring-green-500 focus:ring-offset-1"
                  @click.stop="$emit('confirm', finding.id)"
                >
                  Confirm
                </button>
                <button
                  v-if="
                    finding.status === 'OPEN' || finding.status === 'CONFIRMED'
                  "
                  type="button"
                  class="rounded px-2 py-1 text-xs font-medium text-gray-600 hover:bg-gray-100 focus:outline-none focus:ring-2 focus:ring-gray-500 focus:ring-offset-1"
                  @click.stop="$emit('dismiss', finding.id)"
                >
                  Dismiss
                </button>
              </div>
            </td>
          </tr>
        </tbody>
      </table>
    </div>
  </div>
</template>

<script setup>
import { computed } from 'vue'
import ProfilePriorityBadge from '../profiles/ProfilePriorityBadge.vue'
import SeverityBadge from './SeverityBadge.vue'

const props = defineProps({
  findings: {
    type: Array,
    required: true,
  },
  loading: {
    type: Boolean,
    default: false,
  },
  selectedIds: {
    type: Array,
    default: () => [],
  },
  selectable: {
    type: Boolean,
    default: false,
  },
  activeProfile: {
    type: String,
    default: null,
  },
})

const emit = defineEmits(['select', 'confirm', 'dismiss', 'update:selectedIds'])

const allSelected = computed(() => {
  return (
    props.findings.length > 0 &&
    props.selectedIds.length === props.findings.length
  )
})

const someSelected = computed(() => {
  return (
    props.selectedIds.length > 0 &&
    props.selectedIds.length < props.findings.length
  )
})

function isSelected(id) {
  return props.selectedIds.includes(id)
}

function isNaForProfile(finding) {
  // Dim findings that are N/A for the active profile
  return props.activeProfile && finding.profile_priority === 'na'
}

function handleSelectAll() {
  if (allSelected.value) {
    emit('update:selectedIds', [])
  } else {
    emit(
      'update:selectedIds',
      props.findings.map((f) => f.id),
    )
  }
}

function toggleSelection(id) {
  if (isSelected(id)) {
    emit(
      'update:selectedIds',
      props.selectedIds.filter((i) => i !== id),
    )
  } else {
    emit('update:selectedIds', [...props.selectedIds, id])
  }
}

function truncateUrl(url) {
  try {
    const parsed = new URL(url)
    const path = parsed.pathname
    return path.length > 30 ? path.substring(0, 27) + '...' : path || '/'
  } catch {
    return url.length > 30 ? url.substring(0, 27) + '...' : url
  }
}

function truncateText(text, maxLength) {
  if (!text) return ''
  return text.length > maxLength ? text.substring(0, maxLength) + '...' : text
}

function getStatusClasses(status) {
  switch (status) {
    case 'OPEN':
      return 'bg-gray-100 text-gray-700'
    case 'CONFIRMED':
      return 'bg-orange-100 text-orange-700'
    case 'DISMISSED':
      return 'bg-gray-100 text-gray-400 line-through'
    case 'RESOLVED':
      return 'bg-green-100 text-green-700'
    case 'WONT_FIX':
      return 'bg-yellow-100 text-yellow-700'
    default:
      return 'bg-gray-100 text-gray-700'
  }
}
</script>
