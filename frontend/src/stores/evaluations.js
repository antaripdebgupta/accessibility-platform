/**
 * Evaluations Pinia Store
 *
 * Manages state for evaluation projects including:
 * - List of evaluations for the current organisation
 * - Current evaluation being viewed/edited
 * - CRUD operations
 */

import { defineStore } from 'pinia'
import { computed, ref } from 'vue'
import api from '../lib/api'

export const useEvaluationsStore = defineStore('evaluations', () => {
  // State
  const list = ref([])
  const current = ref(null)
  const loading = ref(false)
  const error = ref(null)
  const total = ref(0)

  // Computed
  const hasEvaluations = computed(() => list.value.length > 0)
  const isLoading = computed(() => loading.value)
  const currentError = computed(() => error.value)

  /**
   * Fetch list of evaluations for the user's organisations.
   * @param {Object} options - Query options
   * @param {string} [options.status] - Filter by status
   * @param {number} [options.skip=0] - Pagination offset
   * @param {number} [options.limit=20] - Items per page
   */
  async function fetchList(options = {}) {
    loading.value = true
    error.value = null

    try {
      const params = new URLSearchParams()
      if (options.status) params.append('status', options.status)
      if (options.skip !== undefined)
        params.append('skip', options.skip.toString())
      if (options.limit !== undefined)
        params.append('limit', options.limit.toString())

      const queryString = params.toString()
      const url = queryString ? `/evaluations?${queryString}` : '/evaluations'

      const response = await api.get(url)
      list.value = response.data.items || []
      total.value = response.data.total || 0

      return response.data
    } catch (err) {
      error.value = err.message || 'Failed to fetch evaluations'
      throw err
    } finally {
      loading.value = false
    }
  }

  /**
   * Fetch a single evaluation by ID.
   * @param {string} id - Evaluation UUID
   */
  async function fetchOne(id) {
    loading.value = true
    error.value = null

    try {
      const response = await api.get(`/evaluations/${id}`)
      current.value = response.data
      return response.data
    } catch (err) {
      error.value = err.message || 'Failed to fetch evaluation'
      current.value = null
      throw err
    } finally {
      loading.value = false
    }
  }

  /**
   * Create a new evaluation project.
   * @param {Object} data - Evaluation creation data
   * @param {string} data.title - Project title
   * @param {string} data.target_url - Website URL to evaluate
   * @param {string} [data.wcag_version='2.1'] - WCAG version
   * @param {string} [data.conformance_level='AA'] - Target level
   * @returns {Promise<Object>} Created evaluation
   */
  async function create(data) {
    loading.value = true
    error.value = null

    try {
      const response = await api.post('/evaluations', data)
      const created = response.data

      // Add to the beginning of the list
      list.value.unshift({
        id: created.id,
        title: created.title,
        target_url: created.target_url,
        status: created.status,
        wcag_version: created.wcag_version,
        conformance_level: created.conformance_level,
        created_at: created.created_at,
      })
      total.value += 1

      return created
    } catch (err) {
      error.value = err.message || 'Failed to create evaluation'
      throw err
    } finally {
      loading.value = false
    }
  }

  /**
   * Update an existing evaluation.
   * @param {string} id - Evaluation UUID
   * @param {Object} data - Fields to update
   * @returns {Promise<Object>} Updated evaluation
   */
  async function updateOne(id, data) {
    loading.value = true
    error.value = null

    try {
      const response = await api.patch(`/evaluations/${id}`, data)
      const updated = response.data

      // Update current if it's the same evaluation
      if (current.value && current.value.id === id) {
        current.value = updated
      }

      // Update in list
      const index = list.value.findIndex((e) => e.id === id)
      if (index !== -1) {
        list.value[index] = {
          id: updated.id,
          title: updated.title,
          target_url: updated.target_url,
          status: updated.status,
          wcag_version: updated.wcag_version,
          conformance_level: updated.conformance_level,
          created_at: updated.created_at,
        }
      }

      return updated
    } catch (err) {
      error.value = err.message || 'Failed to update evaluation'
      throw err
    } finally {
      loading.value = false
    }
  }

  /**
   * Delete an evaluation (soft delete).
   * @param {string} id - Evaluation UUID
   */
  async function deleteOne(id) {
    loading.value = true
    error.value = null

    try {
      await api.delete(`/evaluations/${id}`)

      // Remove from list
      list.value = list.value.filter((e) => e.id !== id)
      total.value = Math.max(0, total.value - 1)

      // Clear current if it was deleted
      if (current.value && current.value.id === id) {
        current.value = null
      }
    } catch (err) {
      error.value = err.message || 'Failed to delete evaluation'
      throw err
    } finally {
      loading.value = false
    }
  }

  /**
   * Clear the current evaluation selection.
   */
  function clearCurrent() {
    current.value = null
    error.value = null
  }

  /**
   * Clear all state.
   */
  function clearAll() {
    list.value = []
    current.value = null
    total.value = 0
    loading.value = false
    error.value = null
  }

  return {
    // State
    list,
    current,
    loading,
    error,
    total,
    // Computed
    hasEvaluations,
    isLoading,
    currentError,
    // Actions
    fetchList,
    fetchOne,
    create,
    updateOne,
    deleteOne,
    clearCurrent,
    clearAll,
  }
})
