<template>
  <div class="relative rounded-lg border border-gray-200 bg-white p-4">
    <!-- Header with criterion info and direction badge -->
    <div class="mb-2 flex items-start justify-between">
      <div class="min-w-0 flex-1">
        <h4 class="truncate text-sm font-medium text-gray-900">
          {{ trend.criterion_code }}
        </h4>
        <p class="truncate text-xs text-gray-500">
          {{ trend.criterion_name }}
        </p>
      </div>
      <DirectionBadge :direction="trend.direction" />
    </div>

    <!-- Chart area -->
    <div class="relative h-[100px]">
      <canvas ref="chartCanvas"></canvas>

      <!-- Resolved overlay -->
      <div
        v-if="trend.direction === 'improving' && latestCount === 0"
        class="absolute inset-0 flex items-center justify-center rounded bg-green-50 bg-opacity-90"
      >
        <span class="text-sm font-medium text-green-700">✓ Resolved</span>
      </div>
    </div>

    <!-- Footer with change info -->
    <div class="mt-2 flex items-center justify-between text-xs">
      <span class="text-gray-500"> Level {{ trend.criterion_level }} </span>
      <span
        :class="{
          'text-red-600': trend.change > 0,
          'text-green-600': trend.change < 0,
          'text-gray-500': trend.change === 0,
        }"
      >
        <template v-if="trend.change > 0">↑ +{{ trend.change }}</template>
        <template v-else-if="trend.change < 0">↓ {{ trend.change }}</template>
        <template v-else>→ No change</template>
      </span>
    </div>
  </div>
</template>

<script setup>
import {
  CategoryScale,
  Chart,
  Filler,
  LinearScale,
  LineController,
  LineElement,
  PointElement,
} from 'chart.js'
import { computed, onMounted, onUnmounted, ref, watch } from 'vue'
import DirectionBadge from './DirectionBadge.vue'

// Register Chart.js components
Chart.register(
  LineController,
  LineElement,
  PointElement,
  LinearScale,
  CategoryScale,
  Filler,
)

const props = defineProps({
  trend: {
    type: Object,
    required: true,
  },
})

const chartCanvas = ref(null)
let chartInstance = null

const latestCount = computed(() => {
  const dataPoints = props.trend.data_points || []
  if (dataPoints.length === 0) return 0
  return dataPoints[dataPoints.length - 1].count
})

function getLineColor() {
  switch (props.trend.direction) {
    case 'regressing':
      return 'rgb(239, 68, 68)' // red-500
    case 'improving':
      return 'rgb(34, 197, 94)' // green-500
    case 'new':
      return 'rgb(249, 115, 22)' // orange-500
    default:
      return 'rgb(107, 114, 128)' // gray-500
  }
}

function getFillColor() {
  switch (props.trend.direction) {
    case 'regressing':
      return 'rgba(239, 68, 68, 0.1)'
    case 'improving':
      return 'rgba(34, 197, 94, 0.1)'
    case 'new':
      return 'rgba(249, 115, 22, 0.1)'
    default:
      return 'rgba(107, 114, 128, 0.1)'
  }
}

function formatDate(isoDate) {
  if (!isoDate) return ''
  const date = new Date(isoDate)
  return date.toLocaleDateString('en-US', {
    month: 'short',
    day: 'numeric',
  })
}

function renderChart() {
  if (!chartCanvas.value) return

  // Destroy existing chart
  if (chartInstance) {
    chartInstance.destroy()
    chartInstance = null
  }

  const ctx = chartCanvas.value.getContext('2d')
  const dataPoints = props.trend.data_points || []

  // Prepare data
  const labels = dataPoints.map((dp) => formatDate(dp.date))
  const data = dataPoints.map((dp) => dp.count)

  chartInstance = new Chart(ctx, {
    type: 'line',
    data: {
      labels,
      datasets: [
        {
          data,
          borderColor: getLineColor(),
          backgroundColor: getFillColor(),
          borderWidth: 2,
          fill: true,
          tension: 0.3,
          pointRadius: 3,
          pointHoverRadius: 5,
          pointBackgroundColor: getLineColor(),
          pointBorderColor: '#fff',
          pointBorderWidth: 1,
        },
      ],
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      plugins: {
        legend: {
          display: false,
        },
        tooltip: {
          enabled: true,
          backgroundColor: 'rgba(0, 0, 0, 0.8)',
          padding: 8,
          callbacks: {
            title: (items) => {
              const index = items[0].dataIndex
              return formatDate(dataPoints[index]?.date)
            },
            label: (context) => {
              return `${context.parsed.y} findings`
            },
          },
        },
      },
      scales: {
        y: {
          display: false,
          beginAtZero: true,
        },
        x: {
          display: false,
        },
      },
    },
  })
}

// Lifecycle
onMounted(() => {
  renderChart()
})

onUnmounted(() => {
  if (chartInstance) {
    chartInstance.destroy()
    chartInstance = null
  }
})

// Watch for data changes
watch(
  () => props.trend,
  () => {
    renderChart()
  },
  { deep: true },
)
</script>
