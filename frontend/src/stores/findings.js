/**
 * Findings Pinia Store
 *
 * Manages state for accessibility findings including:
 * - List of findings for an evaluation
 * - Finding summary statistics
 * - Current finding being viewed
 * - CRUD operations and filtering
 */

import { defineStore } from 'pinia'
import { computed, ref } from 'vue'
import api from '../lib/api'

export const useFindingsStore = defineStore('findings', () => {
  // State
  const findings = ref([])
  const summary = ref({
    critical: 0,
    serious: 0,
    moderate: 0,
    minor: 0,
    info: 0,
    total: 0,
  })
  const current = ref(null)
  const loadingFindings = ref(false)
  const loadingSummary = ref(false)
  const error = ref(null)
  const total = ref(0)
  const filters = ref({
    severity: null,
    status: null,
    source: null,
  })
  const pagination = ref({
    skip: 0,
    limit: 50,
  })

  // Current evaluation ID being viewed
  const currentEvaluationId = ref(null)

  // Computed
  const hasFindings = computed(() => findings.value.length > 0)
  const isLoading = computed(
    () => loadingFindings.value || loadingSummary.value,
  )
  const activeFilters = computed(() => {
    const active = {}
    if (filters.value.severity) active.severity = filters.value.severity
    if (filters.value.status) active.status = filters.value.status
    if (filters.value.source) active.source = filters.value.source
    return active
  })
  const hasActiveFilters = computed(
    () => Object.keys(activeFilters.value).length > 0,
  )

  // Profile-related state
  const profileSummary = ref(null)
  const excludeNa = ref(false)
  const profilePriorityFilter = ref(null)

  /**
   * Fetch findings for an evaluation with optional filters.
   * Supports profile-based filtering and enrichment.
   * @param {string} evaluationId - Evaluation UUID
   * @param {Object} filterOverrides - Optional filter overrides
   * @param {Object} profileOptions - Profile options { profileId, excludeNa, profilePriority }
   */
  async function fetchFindings(
    evaluationId,
    filterOverrides = {},
    profileOptions = {},
  ) {
    loadingFindings.value = true
    error.value = null
    currentEvaluationId.value = evaluationId

    try {
      const params = new URLSearchParams()

      // Apply pagination
      params.append('skip', pagination.value.skip.toString())
      params.append('limit', pagination.value.limit.toString())

      // Apply current filters
      const appliedFilters = { ...filters.value, ...filterOverrides }

      if (appliedFilters.severity)
        params.append('severity', appliedFilters.severity)
      if (appliedFilters.status) params.append('status', appliedFilters.status)
      if (appliedFilters.source) params.append('source', appliedFilters.source)

      // Apply profile options
      const { profileId, excludeNaOption, profilePriority } = profileOptions

      if (profileId) {
        params.append('profile', profileId)
      }

      if (excludeNaOption || excludeNa.value) {
        params.append('exclude_na', 'true')
      }

      if (profilePriority || profilePriorityFilter.value) {
        params.append(
          'profile_priority',
          profilePriority || profilePriorityFilter.value,
        )
      }

      const url = `/evaluations/${evaluationId}/findings?${params.toString()}`

      const response = await api.get(url)
      findings.value = response.data.items || []
      total.value = response.data.total || 0

      // Store profile summary if returned
      if (response.data.profile_summary) {
        profileSummary.value = response.data.profile_summary
      } else {
        profileSummary.value = null
      }

      return response.data
    } catch (err) {
      error.value = err.message || 'Failed to fetch findings'
      throw err
    } finally {
      loadingFindings.value = false
    }
  }

  /**
   * Fetch findings summary for an evaluation.
   * @param {string} evaluationId - Evaluation UUID
   */
  async function fetchSummary(evaluationId) {
    loadingSummary.value = true
    try {
      const response = await api.get(
        `/evaluations/${evaluationId}/findings/summary`,
      )
      summary.value = response.data
      return response.data
    } catch (err) {
      console.error('Failed to fetch findings summary:', err)
      // Don't throw - summary is non-critical
    } finally {
      loadingSummary.value = false
    }
  }

  /**
   * Fetch a single finding by ID.
   * @param {string} findingId - Finding UUID
   */
  async function fetchOne(findingId) {
    loadingFindings.value = true
    error.value = null

    try {
      const response = await api.get(`/findings/${findingId}`)
      current.value = response.data
      return response.data
    } catch (err) {
      error.value = err.message || 'Failed to fetch finding'
      current.value = null
      throw err
    } finally {
      loadingFindings.value = false
    }
  }

  /**
   * Update a finding (optimistic update).
   * @param {string} findingId - Finding UUID
   * @param {Object} data - Fields to update (status, reviewer_note, remediation)
   */
  async function updateFinding(findingId, data) {
    // Find the finding in the list
    const index = findings.value.findIndex((f) => f.id === findingId)
    const originalFinding = index !== -1 ? { ...findings.value[index] } : null

    // Optimistic update
    if (index !== -1) {
      findings.value[index] = { ...findings.value[index], ...data }
    }

    try {
      const response = await api.patch(`/findings/${findingId}`, data)

      // Update with server response
      if (index !== -1) {
        findings.value[index] = response.data
      }

      // Update current if viewing this finding
      if (current.value && current.value.id === findingId) {
        current.value = response.data
      }

      return response.data
    } catch (err) {
      // Revert on error
      if (index !== -1 && originalFinding) {
        findings.value[index] = originalFinding
      }
      error.value = err.message || 'Failed to update finding'
      throw err
    }
  }

  /**
   * Create a manual finding.
   * @param {string} evaluationId - Evaluation UUID
   * @param {Object} data - Finding creation data
   */
  async function createManual(evaluationId, data) {
    loadingFindings.value = true
    error.value = null

    try {
      const response = await api.post(
        `/evaluations/${evaluationId}/findings`,
        data,
      )
      const created = response.data

      // Prepend to findings list
      findings.value.unshift(created)
      total.value += 1

      // Update summary
      if (created.severity && summary.value[created.severity] !== undefined) {
        summary.value[created.severity] += 1
        summary.value.total += 1
      }

      return created
    } catch (err) {
      error.value = err.message || 'Failed to create finding'
      throw err
    } finally {
      loadingFindings.value = false
    }
  }

  /**
   * Set a filter and refetch findings.
   * @param {string} key - Filter key (severity, status, source)
   * @param {string|null} value - Filter value or null to clear
   */
  async function setFilter(key, value) {
    filters.value[key] = value || null

    if (currentEvaluationId.value) {
      await fetchFindings(currentEvaluationId.value)
    }
  }

  /**
   * Clear all filters and refetch findings.
   */
  async function clearFilters() {
    filters.value = {
      severity: null,
      status: null,
      source: null,
    }

    if (currentEvaluationId.value) {
      await fetchFindings(currentEvaluationId.value)
    }
  }

  /**
   * Clear the current finding selection.
   */
  function clearCurrent() {
    current.value = null
  }

  /**
   * Clear all state.
   */
  function clearAll() {
    findings.value = []
    summary.value = {
      critical: 0,
      serious: 0,
      moderate: 0,
      minor: 0,
      info: 0,
      total: 0,
    }
    current.value = null
    total.value = 0
    loadingFindings.value = false
    loadingSummary.value = false
    error.value = null
    filters.value = {
      severity: null,
      status: null,
      source: null,
    }
    pagination.value = {
      skip: 0,
      limit: 50,
    }
    currentEvaluationId.value = null
    // Profile state
    profileSummary.value = null
    excludeNa.value = false
    profilePriorityFilter.value = null
  }

  /**
   * Set the exclude N/A toggle and refetch findings.
   * @param {boolean} value - Whether to exclude N/A findings
   */
  function setExcludeNa(value) {
    excludeNa.value = value
  }

  /**
   * Set the profile priority filter.
   * @param {string|null} value - Profile priority to filter by
   */
  function setProfilePriorityFilter(value) {
    profilePriorityFilter.value = value || null
  }

  return {
    // State
    findings,
    summary,
    current,
    loadingFindings,
    loadingSummary,
    error,
    total,
    filters,
    pagination,
    profileSummary,
    excludeNa,
    profilePriorityFilter,
    // Computed
    hasFindings,
    isLoading,
    activeFilters,
    hasActiveFilters,
    // Actions
    fetchFindings,
    fetchSummary,
    fetchOne,
    updateFinding,
    createManual,
    setFilter,
    clearFilters,
    clearCurrent,
    clearAll,
    setExcludeNa,
    setProfilePriorityFilter,
  }
})
