import { useEffect, useRef, useState } from 'react'
import { getTaskStatus } from './api'

const TERMINAL_STATUSES = new Set(['SUCCESS', 'FAILED', 'FAILURE'])
const DEFAULT_INTERVAL_MS = 3000

interface TaskPollingState {
  data: Record<string, unknown> | null
  status: string | null
  error: Error | null
  isPolling: boolean
}

export function useTaskPolling(taskId: string | null, intervalMs = DEFAULT_INTERVAL_MS) {
  const [state, setState] = useState<TaskPollingState>({
    data: null,
    status: null,
    error: null,
    isPolling: false,
  })

  const timeoutRef = useRef<ReturnType<typeof setTimeout> | null>(null)
  const cancelledRef = useRef(false)

  useEffect(() => {
    cancelledRef.current = false

    if (!taskId) {
      setState({ data: null, status: null, error: null, isPolling: false })
      return
    }

    setState((s) => ({ ...s, isPolling: true, error: null }))

    async function poll() {
      try {
        const result = await getTaskStatus(taskId as string)
        if (cancelledRef.current) return

        const status = typeof result?.status === 'string' ? result.status : null
        const isTerminal = status !== null && TERMINAL_STATUSES.has(status)

        setState({
          data: result,
          status,
          error: null,
          isPolling: !isTerminal,
        })

        if (!isTerminal) {
          timeoutRef.current = setTimeout(poll, intervalMs)
        }
      } catch (err) {
        if (cancelledRef.current) return
        setState((s) => ({
          ...s,
          error: err instanceof Error ? err : new Error('Task status lookup failed'),
          isPolling: false,
        }))
      }
    }

    poll()

    return () => {
      cancelledRef.current = true
      if (timeoutRef.current) clearTimeout(timeoutRef.current)
    }
  }, [taskId, intervalMs])

  return state
}
