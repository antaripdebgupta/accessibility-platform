/**
 * Reports Pinia Store
 *
 * Manages state for accessibility conformance reports including:
 * - List of reports for an evaluation
 * - Latest report details
 * - Report generation status
 * - Download URLs
 */

import { defineStore } from 'pinia'
import { computed, ref } from 'vue'
import api from '../lib/api'

export const useReportsStore = defineStore('reports', () => {
  // State
  const reports = ref([])
  const latest = ref(null)
  const loading = ref(false)
  const generating = ref(false)
  const error = ref(null)

  // Computed
  const hasReports = computed(() => reports.value.length > 0)
  const latestFullReport = computed(() => {
    return reports.value.find((r) => r.report_type === 'full') || null
  })
  const latestEarlReport = computed(() => {
    return reports.value.find((r) => r.report_type === 'earl') || null
  })
  const latestCsvReport = computed(() => {
    return reports.value.find((r) => r.report_type === 'csv') || null
  })

  /**
   * Fetch all reports for an evaluation.
   * @param {string} evaluationId - Evaluation UUID
   */
  async function fetchReports(evaluationId) {
    loading.value = true
    error.value = null

    try {
      const response = await api.get(`/evaluations/${evaluationId}/reports`)
      reports.value = response.data.items || []
      return response.data
    } catch (err) {
      error.value = err.message || 'Failed to fetch reports'
      throw err
    } finally {
      loading.value = false
    }
  }

  /**
   * Fetch the latest full report for an evaluation.
   * @param {string} evaluationId - Evaluation UUID
   */
  async function fetchLatest(evaluationId) {
    loading.value = true
    error.value = null

    try {
      const response = await api.get(
        `/evaluations/${evaluationId}/reports/latest`,
      )
      latest.value = response.data
      return response.data
    } catch (err) {
      // 404 is expected if no reports exist yet
      if (err.status === 404) {
        latest.value = null
        return null
      }
      error.value = err.message || 'Failed to fetch latest report'
      throw err
    } finally {
      loading.value = false
    }
  }

  /**
   * Generate a new report for an evaluation.
   * @param {string} evaluationId - Evaluation UUID
   * @param {Object} options - Generation options
   * @param {string[]} [options.report_types] - Report types to generate
   * @param {boolean} [options.include_dismissed] - Include dismissed findings
   * @returns {Promise<{task_id: string}>}
   */
  async function generateReport(evaluationId, options = {}) {
    generating.value = true
    error.value = null

    try {
      const body = {
        report_types: options.report_types || ['full', 'earl', 'csv'],
        include_dismissed: options.include_dismissed || false,
      }

      const response = await api.post(
        `/evaluations/${evaluationId}/report`,
        body,
      )

      return response.data
    } catch (err) {
      error.value = err.message || 'Failed to generate report'
      throw err
    } finally {
      // Don't set generating to false here — let the polling handle that
    }
  }

  /**
   * Set generating state (called from polling callbacks)
   * @param {boolean} value
   */
  function setGenerating(value) {
    generating.value = value
  }

  function clearReports() {
    reports.value = []
    latest.value = null
    error.value = null
    loading.value = false
    generating.value = false
  }

  return {
    // State
    reports,
    latest,
    loading,
    generating,
    error,
    // Computed
    hasReports,
    latestFullReport,
    latestEarlReport,
    latestCsvReport,
    // Actions
    fetchReports,
    fetchLatest,
    generateReport,
    setGenerating,
    clearReports,
  }
})
