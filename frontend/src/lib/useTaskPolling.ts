import { useEffect, useRef } from 'react'
import { getTaskStatus } from './api'

const TERMINAL_STATUSES = new Set(['SUCCESS', 'FAILED', 'FAILURE'])
const DEFAULT_INTERVAL_MS = 3000
const DEFAULT_MAX_RETRIES = 10

export function useTaskPolling(
  taskId: string | null,
  analysisId: string | null | undefined,
  onResult?: (data: Record<string, unknown>) => void,
  onError?: (error: Error) => void,
  intervalMs = DEFAULT_INTERVAL_MS,
  maxRetries = DEFAULT_MAX_RETRIES,
) {
  const cancelledRef = useRef(false)
  const onResultRef = useRef(onResult)
  const onErrorRef = useRef(onError)
  const retryCountRef = useRef(0)

  useEffect(() => {
    onResultRef.current = onResult
  }, [onResult])

  useEffect(() => {
    onErrorRef.current = onError
  }, [onError])

  useEffect(() => {
    cancelledRef.current = false
    retryCountRef.current = 0

    if (!taskId) return

    async function poll() {
      try {
        const result = await getTaskStatus(taskId as string, analysisId)
        if (cancelledRef.current) return

        retryCountRef.current = 0

        const status = typeof result?.status === 'string' ? result.status : null
        const isTerminal = status !== null && TERMINAL_STATUSES.has(status)

        if (isTerminal) {
          onResultRef.current?.(result)
          return
        }

        setTimeout(poll, intervalMs)
      } catch (err) {
        if (cancelledRef.current) return
        retryCountRef.current++
        if (retryCountRef.current >= maxRetries) {
          onErrorRef.current?.(err instanceof Error ? err : new Error('Task polling failed.'))
          return
        }
        setTimeout(poll, intervalMs)
      }
    }

    poll()

    return () => {
      cancelledRef.current = true
    }
  }, [taskId, analysisId, intervalMs, maxRetries])
}
