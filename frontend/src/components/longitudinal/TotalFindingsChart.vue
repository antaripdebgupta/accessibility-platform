<template>
  <div class="relative h-[250px] w-full">
    <canvas ref="chartCanvas"></canvas>
    <div
      v-if="dataPoints.length === 1"
      class="absolute inset-0 flex items-center justify-center"
    >
      <p class="text-sm text-gray-500">Run more evaluations to see trends</p>
    </div>
  </div>
</template>

<script setup>
import {
  CategoryScale,
  Chart,
  Filler,
  Legend,
  LinearScale,
  LineController,
  LineElement,
  PointElement,
  Tooltip,
} from 'chart.js'
import { onMounted, onUnmounted, ref, watch } from 'vue'

// Register Chart.js components
Chart.register(
  LineController,
  LineElement,
  PointElement,
  LinearScale,
  CategoryScale,
  Tooltip,
  Legend,
  Filler,
)

const props = defineProps({
  dataPoints: {
    type: Array,
    required: true,
    default: () => [],
  },
})

const emit = defineEmits(['select'])

const chartCanvas = ref(null)
let chartInstance = null

function formatDate(isoDate) {
  if (!isoDate) return ''
  const date = new Date(isoDate)
  return date.toLocaleDateString('en-US', {
    month: 'short',
    day: 'numeric',
    year: '2-digit',
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
  const labels = props.dataPoints.map((dp) => formatDate(dp.date))
  const data = props.dataPoints.map((dp) => dp.count)
  const evaluationIds = props.dataPoints.map((dp) => dp.evaluation_id)

  chartInstance = new Chart(ctx, {
    type: 'line',
    data: {
      labels,
      datasets: [
        {
          label: 'Confirmed Findings',
          data,
          borderColor: 'rgb(59, 130, 246)', // blue-500
          backgroundColor: 'rgba(59, 130, 246, 0.1)',
          borderWidth: 2,
          fill: true,
          tension: 0.3,
          pointRadius: 6,
          pointHoverRadius: 8,
          pointBackgroundColor: 'rgb(59, 130, 246)',
          pointBorderColor: '#fff',
          pointBorderWidth: 2,
        },
      ],
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      interaction: {
        intersect: false,
        mode: 'index',
      },
      onClick: (event, elements) => {
        if (elements.length > 0) {
          const index = elements[0].index
          const evaluationId = evaluationIds[index]
          if (evaluationId) {
            emit('select', evaluationId)
          }
        }
      },
      plugins: {
        legend: {
          display: true,
          position: 'top',
          labels: {
            usePointStyle: true,
            padding: 16,
          },
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
              return formatDate(props.dataPoints[index]?.date)
            },
            label: (context) => {
              return `${context.parsed.y} confirmed findings`
            },
            afterBody: () => {
              return 'Click to view evaluation'
            },
          },
        },
      },
      scales: {
        y: {
          beginAtZero: true,
          ticks: {
            precision: 0,
          },
          grid: {
            color: 'rgba(0, 0, 0, 0.05)',
          },
        },
        x: {
          grid: {
            display: false,
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
  () => props.dataPoints,
  () => {
    renderChart()
  },
  { deep: true },
)
</script>
