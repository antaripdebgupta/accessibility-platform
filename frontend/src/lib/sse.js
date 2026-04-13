/**
 * SSE (Server-Sent Events) Client
 *
 * Wrapper around the browser EventSource API for real-time task progress streaming.
 * Handles Firebase auth token injection, connection management, and event dispatching.
 *
 * Note: EventSource does not support custom headers, so auth token is passed via
 * query parameter (?token=xxx).
 */

import { auth } from './firebase'

// Module-level storage for active EventSource connections
const activeStreams = new Map()

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
    const url = `/api/v1/tasks/${taskId}/stream?token=${encodeURIComponent(firebaseToken)}`

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
    eventSource.onerror = (e) => {
      console.error('SSE: Connection error', e)

      // Check if the connection was closed
      if (eventSource.readyState === EventSource.CLOSED) {
        handlers.onError?.({ data: { message: 'Connection closed' } })
        closeTaskStream(taskId)
      } else if (eventSource.readyState === EventSource.CONNECTING) {
        // Browser is automatically reconnecting - this is normal for SSE
        console.debug('SSE: Reconnecting...')
      } else {
        handlers.onError?.({ data: { message: 'Connection lost' } })
        closeTaskStream(taskId)
      }
    }

    // Handle connection open
    eventSource.onopen = () => {
      console.debug('SSE: Connection opened for task', taskId)
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
