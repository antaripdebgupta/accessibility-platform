/**
 * SSE (Server-Sent Events) Client
 *
 * Wrapper around the browser EventSource API for real-time task progress streaming.
 * Handles Firebase auth token injection, connection management, and event dispatching.
 *
 * Features:
 * - Automatic token refresh on reconnection
 * - Exponential backoff for retries
 * - Proper cleanup on connection failures
 *
 * Note: EventSource does not support custom headers, so auth token is passed via
 * query parameter (?token=xxx).
 */

import { auth } from './firebase'

// Module-level storage for active EventSource connections
const activeStreams = new Map()

// Track retry attempts for exponential backoff
const retryAttempts = new Map()
const MAX_RETRIES = 3
const BASE_RETRY_DELAY = 2000 // 2 seconds

/**
 * Check if SSE/EventSource is supported in this browser.
 * Used to fall back to polling if not available.
 *
 * @returns {boolean} True if EventSource is available
 */
export function isSSESupported() {
  return typeof EventSource !== 'undefined'
}

/**
 * Create a new SSE stream for a task.
 *
 * Connects to the SSE endpoint and dispatches events to the provided handlers.
 * Automatically handles Firebase token injection and connection cleanup.
 *
 * @param {string} taskId - The Celery task ID to stream
 * @param {Object} handlers - Event handler callbacks
 * @param {Function} [handlers.onConnected] - Called when SSE connection is established
 * @param {Function} [handlers.onProgress] - Called on every progress event
 * @param {Function} [handlers.onComplete] - Called when task succeeds
 * @param {Function} [handlers.onError] - Called when task fails or connection error
 * @param {Function} [handlers.onPageFound] - Called on each page_found event (crawl tasks)
 * @param {Function} [handlers.onPageScanned] - Called on each page_complete event (scan tasks)
 * @returns {Promise<Function>} Cleanup function to close the stream
 */
export async function createTaskStream(taskId, handlers = {}) {
  // Close any existing stream for this task
  if (activeStreams.has(taskId)) {
    closeTaskStream(taskId)
  }

  try {
    // Get Firebase auth token
    const currentUser = auth.currentUser
    if (!currentUser) {
      console.error('SSE: No authenticated user')
      handlers.onError?.({ data: { message: 'Authentication required' } })
      return () => {}
    }

    const firebaseToken = await currentUser.getIdToken()
    if (!firebaseToken) {
      console.error('SSE: Failed to get Firebase token')
      handlers.onError?.({
        data: { message: 'Failed to get authentication token' },
      })
      return () => {}
    }

    // Construct SSE URL with token in query param
    const apiBase = import.meta.env.VITE_API_URL || ''
    const url = `${apiBase}/api/v1/tasks/${taskId}/stream?token=${encodeURIComponent(firebaseToken)}`

    // Create EventSource
    const eventSource = new EventSource(url)

    // Store in active streams map
    activeStreams.set(taskId, eventSource)

    // Event dispatcher
    function dispatch(event) {
      switch (event.type) {
        case 'connected':
          handlers.onConnected?.()
          break

        case 'progress':
          handlers.onProgress?.(event)
          // Dispatch specific progress events
          if (event.data?.step === 'page_found') {
            handlers.onPageFound?.(event)
          }
          if (event.data?.step === 'page_complete') {
            handlers.onPageScanned?.(event)
          }
          break

        case 'complete':
          handlers.onComplete?.(event)
          closeTaskStream(taskId)
          break

        case 'error':
          handlers.onError?.(event)
          closeTaskStream(taskId)
          break

        case 'stream_end':
          closeTaskStream(taskId)
          break

        case 'heartbeat':
          // Silently ignore heartbeats - they just keep the connection alive
          break

        case 'timeout':
          handlers.onError?.({ data: { message: 'Connection timed out' } })
          closeTaskStream(taskId)
          break

        default:
          // Unknown event type, log for debugging
          console.debug('SSE: Unknown event type', event.type, event)
      }
    }

    // Handle incoming messages
    eventSource.onmessage = (e) => {
      try {
        const event = JSON.parse(e.data)
        dispatch(event)
      } catch (parseError) {
        console.error('SSE: Failed to parse message', parseError, e.data)
      }
    }

    // Handle connection errors
    eventSource.onerror = async (e) => {
      console.error('SSE: Connection error', e)

      // Get current retry count
      const retries = retryAttempts.get(taskId) || 0

      // Check if the connection was closed
      if (eventSource.readyState === EventSource.CLOSED) {
        // Connection was closed - check if we should retry
        if (retries < MAX_RETRIES) {
          retryAttempts.set(taskId, retries + 1)
          const delay = BASE_RETRY_DELAY * Math.pow(2, retries)
          console.debug(
            `SSE: Will retry in ${delay}ms (attempt ${retries + 1}/${MAX_RETRIES})`,
          )

          // Clean up current stream
          closeTaskStream(taskId)

          // Retry with fresh token after delay
          setTimeout(async () => {
            try {
              await createTaskStream(taskId, handlers)
            } catch (retryError) {
              console.error('SSE: Retry failed', retryError)
              handlers.onError?.({
                data: { message: 'Connection failed after retries' },
              })
            }
          }, delay)
        } else {
          // Max retries exceeded
          retryAttempts.delete(taskId)
          handlers.onError?.({
            data: { message: 'Connection closed - max retries exceeded' },
          })
          closeTaskStream(taskId)
        }
      } else if (eventSource.readyState === EventSource.CONNECTING) {
        // Browser is automatically reconnecting - this is normal for SSE
        // But we may need a fresh token
        console.debug('SSE: Reconnecting...')
      } else {
        retryAttempts.delete(taskId)
        handlers.onError?.({ data: { message: 'Connection lost' } })
        closeTaskStream(taskId)
      }
    }

    // Handle connection open - reset retry counter on success
    eventSource.onopen = () => {
      console.debug('SSE: Connection opened for task', taskId)
      retryAttempts.delete(taskId) // Reset retries on successful connection
    }

    // Return cleanup function
    return () => closeTaskStream(taskId)
  } catch (error) {
    console.error('SSE: Failed to create stream', error)
    handlers.onError?.({
      data: { message: error.message || 'Failed to connect' },
    })
    return () => {}
  }
}

/**
 * Close and clean up an SSE stream for a specific task.
 *
 * This function is idempotent - calling it multiple times for the same
 * taskId is safe and has no side effects.
 *
 * @param {string} taskId - The task ID to close the stream for
 */
export function closeTaskStream(taskId) {
  const eventSource = activeStreams.get(taskId)
  if (eventSource) {
    try {
      eventSource.close()
      console.debug('SSE: Closed stream for task', taskId)
    } catch (error) {
      console.warn('SSE: Error closing stream', taskId, error)
    }
    activeStreams.delete(taskId)
  }
  // Also clean up retry tracking
  retryAttempts.delete(taskId)
}

/**
 * Close all active SSE streams.
 *
 * Call this on page unmount or when navigating away to clean up resources.
 */
export function closeAllStreams() {
  for (const [taskId, eventSource] of activeStreams.entries()) {
    try {
      eventSource.close()
      console.debug('SSE: Closed stream for task', taskId)
    } catch (error) {
      console.warn('SSE: Error closing stream', taskId, error)
    }
  }
  activeStreams.clear()
  retryAttempts.clear()
}

/**
 * Get the number of active SSE streams.
 *
 * Useful for debugging and monitoring.
 *
 * @returns {number} Number of active streams
 */
export function getActiveStreamCount() {
  return activeStreams.size
}
