import { defineStore } from 'pinia'
import { computed, ref } from 'vue'
import api from '../lib/api'

export const useSamplingStore = defineStore('sampling', () => {
  // State
  const sampleSummary = ref(null)
  const sampledPages = ref([])
  const loading = ref(false)
  const applying = ref(false)
  const error = ref(null)

  // Getters
  const hasSample = computed(() => {
    return sampleSummary.value?.sampled_pages > 0
  })

  const sampleSize = computed(() => {
    return sampleSummary.value?.sampled_pages || 0
  })

  const totalEligible = computed(() => {
    return sampleSummary.value?.total_pages || 0
  })

  const structuredCount = computed(() => {
    // Coverage is a map of page_type -> count
    const coverage = sampleSummary.value?.coverage || {}
    return Object.values(coverage).reduce((acc, count) => acc + count, 0)
  })

  const randomCount = computed(() => {
    // This is sampled_pages - structured_count
    return (sampleSummary.value?.sampled_pages || 0) - structuredCount.value
  })

  // Actions
  async function fetchSampleSummary(evaluationId) {
    loading.value = true
    error.value = null

    try {
      const response = await api.get(`/evaluations/${evaluationId}/sample`)
      // API returns { summary: {...}, pages: [...] }
      sampleSummary.value = response.data.summary
      sampledPages.value = response.data.pages
      return response.data
    } catch (err) {
      error.value = err.message || 'Failed to fetch sample summary'
      throw err
    } finally {
      loading.value = false
    }
  }

  async function fetchSampledPages(evaluationId, options = {}) {
    // The GET /sample endpoint already returns all pages, so we just filter in memory
    // If we need pagination, we can add a separate endpoint later
    loading.value = true
    error.value = null

    try {
      const response = await api.get(`/evaluations/${evaluationId}/sample`)
      sampledPages.value = response.data.pages
      sampleSummary.value = response.data.summary

      // Return in a paginated format for compatibility
      return {
        items: response.data.pages,
        total: response.data.pages.length,
      }
    } catch (err) {
      error.value = err.message || 'Failed to fetch sampled pages'
      throw err
    } finally {
      loading.value = false
    }
  }

  async function applySample(evaluationId, config = null) {
    applying.value = true
    error.value = null

    try {
      const response = await api.post(
        `/evaluations/${evaluationId}/sample`,
        config,
      )
      // POST returns SampleResultResponse: { structured_count, random_count, total_count, coverage, reasoning, sampled_page_ids }
      // We need to refresh to get the full data
      await fetchSampleSummary(evaluationId)
      return response.data
    } catch (err) {
      error.value = err.message || 'Failed to apply sample'
      throw err
    } finally {
      applying.value = false
    }
  }

  async function togglePageInSample(evaluationId, pageId, inSample) {
    error.value = null

    try {
      const response = await api.patch(
        `/evaluations/${evaluationId}/sample/pages/${pageId}`,
        { in_sample: inSample },
      )

      // Update local state
      const page = sampledPages.value.find((p) => p.id === pageId)
      if (page) {
        page.in_sample = inSample
      }

      // Update summary counts
      if (sampleSummary.value) {
        if (inSample) {
          sampleSummary.value.sampled_pages++
          sampleSummary.value.unsampled_pages--
        } else {
          sampleSummary.value.sampled_pages--
          sampleSummary.value.unsampled_pages++
        }
      }

      return response.data
    } catch (err) {
      error.value = err.message || 'Failed to toggle page sample status'
      throw err
    }
  }

  function clearSample() {
    sampleSummary.value = null
    sampledPages.value = []
    error.value = null
  }

  return {
    // State
    sampleSummary,
    sampledPages,
    loading,
    applying,
    error,
    // Getters
    hasSample,
    sampleSize,
    totalEligible,
    structuredCount,
    randomCount,
    // Actions
    fetchSampleSummary,
    fetchSampledPages,
    applySample,
    togglePageInSample,
    clearSample,
  }
})
