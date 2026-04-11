/**
 * Longitudinal Pinia Store
 *
 * Manages state for longitudinal evaluation tracking:
 * - Evaluation series (grouped by target URL)
 * - Series trends and analysis
 * - Snapshot management
 */

import { defineStore } from 'pinia'
import { computed, ref } from 'vue'
import api from '../lib/api'

export const useLongitudinalStore = defineStore('longitudinal', () => {
  // State
  const series = ref([])
  const currentSeries = ref(null)
  const trends = ref(null)
  const loading = ref(false)
  const error = ref(null)

  // Computed
  const allSeries = computed(() => series.value)
  const hasSeries = computed(() => series.value.length > 0)
  const isLoading = computed(() => loading.value)
  const currentError = computed(() => error.value)

  /**
   * Fetch all evaluation series for the current organisation.
   * @returns {Promise<Array>} Array of series items
   */
  async function fetchAllSeries() {
    loading.value = true
    error.value = null

    try {
      const response = await api.get('/series')
      series.value = response.data.items || []
      return series.value
    } catch (err) {
      error.value =
        err.response?.data?.detail || err.message || 'Failed to fetch series'
      throw err
    } finally {
      loading.value = false
    }
  }

  /**
   * Fetch detailed information about a single series.
   * @param {string} seriesId - Series UUID
   * @returns {Promise<Object>} Series detail with snapshots
   */
  async function fetchSeries(seriesId) {
    loading.value = true
    error.value = null

    try {
      const response = await api.get(`/series/${seriesId}`)
      currentSeries.value = response.data
      return response.data
    } catch (err) {
      error.value =
        err.response?.data?.detail || err.message || 'Failed to fetch series'
      currentSeries.value = null
      throw err
    } finally {
      loading.value = false
    }
  }

  /**
   * Fetch trend analysis for a series.
   * @param {string} seriesId - Series UUID
   * @param {Object} options - Query options
   * @param {number} [options.lastN] - Only use last N snapshots
   * @param {string} [options.criterion] - Filter to a single criterion
   * @returns {Promise<Object>} Trend report
   */
  async function fetchTrends(seriesId, options = {}) {
    loading.value = true
    error.value = null

    try {
      const params = new URLSearchParams()
      if (options.lastN) params.append('last_n', options.lastN.toString())
      if (options.criterion) params.append('criterion', options.criterion)

      const queryString = params.toString()
      const url = queryString
        ? `/series/${seriesId}/trends?${queryString}`
        : `/series/${seriesId}/trends`

      const response = await api.get(url)
      trends.value = response.data
      return response.data
    } catch (err) {
      error.value =
        err.response?.data?.detail || err.message || 'Failed to fetch trends'
      trends.value = null
      throw err
    } finally {
      loading.value = false
    }
  }

  /**
   * Fetch the series that an evaluation belongs to.
   * @param {string} evaluationId - Evaluation UUID
   * @returns {Promise<Object|null>} Series info or null if not registered
   */
  async function fetchEvaluationSeries(evaluationId) {
    loading.value = true
    error.value = null

    try {
      const response = await api.get(`/evaluations/${evaluationId}/series`)
      return response.data
    } catch (err) {
      if (err.response?.status === 404) {
        // Evaluation not yet registered in a series
        return null
      }
      error.value =
        err.response?.data?.detail ||
        err.message ||
        'Failed to fetch evaluation series'
      throw err
    } finally {
      loading.value = false
    }
  }

  /**
   * Register an evaluation in the longitudinal tracking series.
   * @param {string} evaluationId - Evaluation UUID
   * @returns {Promise<Object>} Created snapshot
   */
  async function registerEvaluation(evaluationId) {
    loading.value = true
    error.value = null

    try {
      const response = await api.post(
        `/evaluations/${evaluationId}/series/register`,
      )
      return response.data
    } catch (err) {
      error.value =
        err.response?.data?.detail ||
        err.message ||
        'Failed to register evaluation'
      throw err
    } finally {
      loading.value = false
    }
  }

  /**
   * Update a series display name.
   * @param {string} seriesId - Series UUID
   * @param {string} name - New display name
   * @returns {Promise<Object>} Updated series
   */
  async function updateSeriesName(seriesId, name) {
    loading.value = true
    error.value = null

    try {
      const response = await api.patch(`/series/${seriesId}`, {
        display_name: name,
      })

      // Update in local state
      const index = series.value.findIndex((s) => s.id === seriesId)
      if (index !== -1) {
        series.value[index].display_name = name
      }

      if (currentSeries.value?.id === seriesId) {
        currentSeries.value.display_name = name
      }

      return response.data
    } catch (err) {
      error.value =
        err.response?.data?.detail || err.message || 'Failed to update series'
      throw err
    } finally {
      loading.value = false
    }
  }

  /**
   * Clear current series and trends state.
   */
  function clearCurrent() {
    currentSeries.value = null
    trends.value = null
    error.value = null
  }

  /**
   * Reset all state.
   */
  function $reset() {
    series.value = []
    currentSeries.value = null
    trends.value = null
    loading.value = false
    error.value = null
  }

  return {
    // State
    series,
    currentSeries,
    trends,
    loading,
    error,

    // Computed
    allSeries,
    hasSeries,
    isLoading,
    currentError,

    // Actions
    fetchAllSeries,
    fetchSeries,
    fetchTrends,
    fetchEvaluationSeries,
    registerEvaluation,
    updateSeriesName,
    clearCurrent,
    $reset,
  }
})
