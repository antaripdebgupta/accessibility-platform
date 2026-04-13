/**
 * Tasks Pinia Store
 *
 * Manages state for async background tasks (Celery tasks).
 * Uses SSE (Server-Sent Events) for real-time progress streaming,
 * with automatic fallback to polling if SSE is not available.
 */

import { defineStore } from 'pinia'
import { ref } from 'vue'

import api from '../lib/api'
import {
  closeAllStreams,
  closeTaskStream,
  createTaskStream,
  isSSESupported,
} from '../lib/sse'

export const useTasksStore = defineStore('tasks', () => {
  // State

  /**
   * Object storing active task statuses, keyed by task_id
   * @type {Record<string, { status: string, result?: any, error?: string, lastEvent?: object }>}
   */
  const activeTasks = ref({})

  /**
   * Object storing polling interval IDs (for legacy fallback), keyed by task_id
   * @type {Record<string, number>}
   */
  const pollingIntervals = ref({})

  /**
   * Object storing granular task progress, keyed by task_id
   * @type {Record<string, { percent?: number, message?: string, step?: string, pagesFound?: number, pagesScanned?: number, pagesTotal?: number, findings?: number }>}
   */
  const taskProgress = ref({})

  /**
   * Map storing cleanup functions for SSE streams
   * @type {Map<string, Function>}
   */
  const _cleanups = new Map()

  /**
   * Start streaming/polling for a task's status.
   *
   * Uses SSE if available, falls back to polling otherwise.
   * On SUCCESS status: calls onSuccess(result), stops streaming.
   * On FAILURE status: calls onError(message), stops streaming.
   *
   * @param {string} taskId - The Celery task ID to stream
   * @param {function} onSuccess - Callback when task succeeds, receives result
   * @param {function} onError - Callback when task fails, receives error message
   */
  async function startPolling(taskId, onSuccess, onError) {
    // Check for SSE support
    if (!isSSESupported()) {
      _startLegacyPolling(taskId, onSuccess, onError)
      return
    }

    // Stop any existing stream/polling for this task
    stopPolling(taskId)

    // Initialize task status
    activeTasks.value[taskId] = { status: 'PENDING' }
    taskProgress.value[taskId] = {
      percent: null,
      message: null,
      step: null,
      pagesFound: null,
      pagesScanned: null,
      pagesTotal: null,
      findings: null,
    }

    try {
      const cleanup = await createTaskStream(taskId, {
        onConnected: () => {
          if (activeTasks.value[taskId]) {
            activeTasks.value[taskId].status = 'STARTED'
          }
        },

        onProgress: (event) => {
          const data = event.data || {}

          // Update progress state with all available fields
          taskProgress.value[taskId] = {
            percent:
              data.percent ?? taskProgress.value[taskId]?.percent ?? null,
            message: data.message ?? null,
            step: data.step ?? null,
            // Crawl progress
            pagesFound:
              data.pages_found ??
              taskProgress.value[taskId]?.pagesFound ??
              null,
            lastUrl: data.url ?? taskProgress.value[taskId]?.lastUrl ?? null,
            // Scan progress
            pagesScanned:
              data.pages_scanned ??
              taskProgress.value[taskId]?.pagesScanned ??
              null,
            pagesTotal:
              data.pages_total ??
              taskProgress.value[taskId]?.pagesTotal ??
              null,
            currentPage:
              data.current_page ??
              data.url ??
              taskProgress.value[taskId]?.currentPage ??
              null,
            lastPage:
              data.last_page ?? taskProgress.value[taskId]?.lastPage ?? null,
            findingsOnPage:
              data.findings_on_page ??
              taskProgress.value[taskId]?.findingsOnPage ??
              null,
            // Report progress
            findings:
              data.findings_found ??
              data.total_findings ??
              taskProgress.value[taskId]?.findings ??
              null,
          }

          // Update task status
          if (activeTasks.value[taskId]) {
            activeTasks.value[taskId].status = 'STARTED'
            activeTasks.value[taskId].lastEvent = event
          }
        },

        onComplete: (event) => {
          const data = event.data || {}

          if (activeTasks.value[taskId]) {
            activeTasks.value[taskId].status = 'SUCCESS'
            activeTasks.value[taskId].result = data
          }

          // Clear progress after completion
          delete taskProgress.value[taskId]

          onSuccess?.(data)
        },

        onError: (event) => {
          const data = event.data || {}
          const errorMessage = data.message || 'Task failed'

          if (activeTasks.value[taskId]) {
            activeTasks.value[taskId].status = 'FAILURE'
            activeTasks.value[taskId].error = errorMessage
          }

          // Clear progress after failure
          delete taskProgress.value[taskId]

          onError?.(errorMessage)
        },

        onPageFound: (event) => {
          // Page found events are already handled in onProgress
          // This callback is available for additional page-specific handling
        },

        onPageScanned: (event) => {
          // Page scanned events are already handled in onProgress
          // This callback is available for additional page-specific handling
        },
      })

      // Store cleanup function
      _cleanups.set(taskId, cleanup)
    } catch (error) {
      console.error(
        'Failed to start SSE stream, falling back to polling:',
        error,
      )
      // Fall back to legacy polling on SSE failure
      _startLegacyPolling(taskId, onSuccess, onError)
    }
  }

  /**
   * Legacy polling implementation (fallback for browsers without SSE support).
   *
   * Polls GET /tasks/{task_id} every 3 seconds.
   * Kept as internal method - use startPolling() instead.
   *
   * @param {string} taskId - The Celery task ID to poll
   * @param {function} onSuccess - Callback when task succeeds
   * @param {function} onError - Callback when task fails
   * @private
   */
  function _startLegacyPolling(taskId, onSuccess, onError) {
    // If already polling this task, stop the existing interval
    if (pollingIntervals.value[taskId]) {
      clearInterval(pollingIntervals.value[taskId])
      delete pollingIntervals.value[taskId]
    }

    // Initialize task status
    activeTasks.value[taskId] = { status: 'PENDING' }

    // Poll function
    async function pollTask() {
      try {
        const response = await api.get(`/tasks/${taskId}`)
        const taskData = response.data

        // Update task state
        activeTasks.value[taskId] = {
          status: taskData.status,
          result: taskData.result,
          error: taskData.error,
        }

        // Check for terminal states
        if (taskData.status === 'SUCCESS') {
          clearInterval(pollingIntervals.value[taskId])
          delete pollingIntervals.value[taskId]
          if (onSuccess) {
            onSuccess(taskData.result)
          }
        } else if (taskData.status === 'FAILURE') {
          clearInterval(pollingIntervals.value[taskId])
          delete pollingIntervals.value[taskId]
          if (onError) {
            onError(taskData.error || 'Task failed')
          }
        }
        // PENDING and STARTED continue polling
      } catch (err) {
        console.error(`Failed to poll task ${taskId}:`, err)
        // Don't stop polling on network errors, let it retry
        activeTasks.value[taskId] = {
          status: 'ERROR',
          error: err.message || 'Failed to check task status',
        }
      }
    }

    // Start polling immediately and then every 3 seconds
    pollTask()
    const intervalId = setInterval(pollTask, 3000)
    pollingIntervals.value[taskId] = intervalId
  }

  /**
   * Stop streaming/polling for a specific task.
   *
   * @param {string} taskId - The task ID to stop
   */
  function stopPolling(taskId) {
    // Stop SSE stream if active
    const cleanup = _cleanups.get(taskId)
    if (cleanup) {
      cleanup()
      _cleanups.delete(taskId)
    }
    closeTaskStream(taskId)

    // Stop legacy polling if active
    const intervalId = pollingIntervals.value[taskId]
    if (intervalId) {
      clearInterval(intervalId)
      delete pollingIntervals.value[taskId]
    }
  }

  /**
   * Stop all active streaming/polling.
   * Call this on page unmount to clean up.
   */
  function stopAll() {
    // Stop all SSE streams
    for (const cleanup of _cleanups.values()) {
      cleanup()
    }
    _cleanups.clear()
    closeAllStreams()

    // Stop all legacy polling
    Object.keys(pollingIntervals.value).forEach((taskId) => {
      clearInterval(pollingIntervals.value[taskId])
    })
    pollingIntervals.value = {}
  }

  /**
   * Get the latest known status for a task.
   *
   * @param {string} taskId - The task ID to check
   * @returns {{ status: string, result?: any, error?: string } | null}
   */
  function getTaskStatus(taskId) {
    return activeTasks.value[taskId] || null
  }

  /**
   * Get the granular progress for a task.
   *
   * Returns progress details like percent complete, current message,
   * pages found/scanned, etc.
   *
   * @param {string} taskId - The task ID to check
   * @returns {{ percent?: number, message?: string, step?: string, pagesFound?: number, pagesScanned?: number, pagesTotal?: number, findings?: number } | null}
   */
  function getProgress(taskId) {
    return taskProgress.value[taskId] || null
  }

  /**
   * Clear a task from the active tasks list.
   *
   * @param {string} taskId - The task ID to clear
   */
  function clearTask(taskId) {
    stopPolling(taskId)
    delete activeTasks.value[taskId]
    delete taskProgress.value[taskId]
  }

  /**
   * Clear all tasks and stop all streaming/polling.
   */
  function clearAll() {
    stopAll()
    activeTasks.value = {}
    taskProgress.value = {}
  }

  return {
    // State
    activeTasks,
    pollingIntervals,
    taskProgress,
    // Actions
    startPolling,
    stopPolling,
    stopAll,
    getTaskStatus,
    getProgress,
    clearTask,
    clearAll,
  }
})
