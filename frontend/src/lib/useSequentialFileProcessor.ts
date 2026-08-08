import { useEffect, useRef } from 'react'
import { useStore } from '../store'
import { uploadFile } from './api'

export function useSequentialFileProcessor() {
  const files = useStore((s) => s.files)
  const updateFile = useStore((s) => s.updateFile)
  const uploadingRef = useRef(false)

  useEffect(() => {
    // 1. Is any file currently processing in the background or being uploaded?
    const isCurrentlyProcessing =
      uploadingRef.current ||
      files.some((f) => f.taskId !== 'dev-manual' && f.status === 'processing')

    if (isCurrentlyProcessing) return

    // 2. Find the very next pending file waiting in line
    const nextPending = files.find(
      (f) => f.taskId !== 'dev-manual' && f.status === 'pending' && f.file !== null && !f.taskId,
    )

    if (!nextPending || !nextPending.file) return

    // 3. Process exactly ONE file at a time
    uploadingRef.current = true
    updateFile(nextPending.id, { status: 'processing' })

    uploadFile(nextPending.file)
      .then((res) => {
        updateFile(nextPending.id, {
          taskId: res.task_id,
          analysisId: res.analysis_id ?? null,
          fileUrl: res.file_url ?? null,
          status: 'processing',
        })
      })
      .catch((err) => {
        const errMsg = err instanceof Error ? err.message : 'Failed to upload CAD file to server.'
        updateFile(nextPending.id, { status: 'failed', errorMessage: errMsg })
      })
      .finally(() => {
        uploadingRef.current = false
      })
  }, [files, updateFile])
}
