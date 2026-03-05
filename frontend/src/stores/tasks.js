/**
 * Tasks Pinia Store
 *
 * Manages state for async background tasks (Celery tasks).
 * Provides polling functionality for task status checks.
 */

import { defineStore } from 'pinia'
import { ref } from 'vue'

import api from '../lib/api'

export const useTasksStore = defineStore('tasks', () => {
  // State
  /**
   * Object storing active task statuses, keyed by task_id
   * @type {Record<string, { status: string, result?: any, error?: string }>}
   */
  const activeTasks = ref({})

  /**
   * Object storing polling interval IDs, keyed by task_id
   * @type {Record<string, number>}
   */
  const pollingIntervals = ref({})

  /**
   * Start polling for a task's status.
   *
   * Polls GET /tasks/{task_id} every 3 seconds.
   * On SUCCESS status: calls onSuccess(result), stops polling.
   * On FAILURE status: calls onError(message), stops polling.
   *
   * @param {string} taskId - The Celery task ID to poll
   * @param {function} onSuccess - Callback when task succeeds, receives result
   * @param {function} onError - Callback when task fails, receives error message
   */
  function startPolling(taskId, onSuccess, onError) {
    // If already polling this task, stop the existing interval
    if (pollingIntervals.value[taskId]) {
      stopPolling(taskId)
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
          stopPolling(taskId)
          if (onSuccess) {
            onSuccess(taskData.result)
          }
        } else if (taskData.status === 'FAILURE') {
          stopPolling(taskId)
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
   * Stop polling for a specific task.
   *
   * @param {string} taskId - The task ID to stop polling
   */
  function stopPolling(taskId) {
    const intervalId = pollingIntervals.value[taskId]
    if (intervalId) {
      clearInterval(intervalId)
      delete pollingIntervals.value[taskId]
    }
  }

  /**
   * Stop all active polling intervals.
   * Call this on page unmount to clean up.
   */
  function stopAll() {
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
   * Clear a task from the active tasks list.
   *
   * @param {string} taskId - The task ID to clear
   */
  function clearTask(taskId) {
    stopPolling(taskId)
    delete activeTasks.value[taskId]
  }

  /**
   * Clear all tasks and stop all polling.
   */
  function clearAll() {
    stopAll()
    activeTasks.value = {}
  }

  return {
    // State
    activeTasks,
    pollingIntervals,
    // Actions
    startPolling,
    stopPolling,
    stopAll,
    getTaskStatus,
    clearTask,
    clearAll,
  }
})
