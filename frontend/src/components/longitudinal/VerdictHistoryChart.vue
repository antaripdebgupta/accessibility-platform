<template>
  <div class="h-[120px] w-full">
    <canvas ref="chartCanvas"></canvas>
  </div>
</template>

<script setup>
import {
  BarController,
  BarElement,
  CategoryScale,
  Chart,
  LinearScale,
  Tooltip,
} from 'chart.js'
import { onMounted, onUnmounted, ref, watch } from 'vue'

// Register Chart.js components
Chart.register(BarController, BarElement, LinearScale, CategoryScale, Tooltip)

const props = defineProps({
  verdictHistory: {
    type: Array,
    required: true,
    default: () => [],
  },
})

const chartCanvas = ref(null)
let chartInstance = null

function getVerdictColor(verdict) {
  switch (verdict) {
    case 'CONFORMS':
      return 'rgb(34, 197, 94)' // green-500
    case 'DOES_NOT_CONFORM':
      return 'rgb(239, 68, 68)' // red-500
    case 'CANNOT_DETERMINE':
      return 'rgb(234, 179, 8)' // yellow-500
    default:
      return 'rgb(156, 163, 175)' // gray-400
  }
}

function getVerdictLabel(verdict) {
  switch (verdict) {
    case 'CONFORMS':
      return 'Conforms'
    case 'DOES_NOT_CONFORM':
      return 'Does Not Conform'
    case 'CANNOT_DETERMINE':
      return 'Cannot Determine'
    default:
      return 'Unknown'
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

  // Prepare data
  const labels = props.verdictHistory.map((vh) => formatDate(vh.date))
  const data = props.verdictHistory.map(() => 1) // Fixed height bars
  const colors = props.verdictHistory.map((vh) => getVerdictColor(vh.verdict))

  chartInstance = new Chart(ctx, {
    type: 'bar',
    data: {
      labels,
      datasets: [
        {
          data,
          backgroundColor: colors,
          borderRadius: 4,
          barPercentage: 0.8,
          categoryPercentage: 0.9,
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
          backgroundColor: 'rgba(0, 0, 0, 0.8)',
          titleColor: '#fff',
          bodyColor: '#fff',
          padding: 12,
          cornerRadius: 8,
          callbacks: {
            title: (items) => {
              const index = items[0].dataIndex
              return formatDate(props.verdictHistory[index]?.date)
            },
            label: (context) => {
              const index = context.dataIndex
              const verdict = props.verdictHistory[index]?.verdict
              return getVerdictLabel(verdict)
            },
          },
        },
      },
      scales: {
        y: {
          display: false,
          min: 0,
          max: 1,
        },
        x: {
          grid: {
            display: false,
          },
          ticks: {
            font: {
              size: 10,
            },
          },
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
  () => props.verdictHistory,
  () => {
    renderChart()
  },
  { deep: true },
)
</script>
