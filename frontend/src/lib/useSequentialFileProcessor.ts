import { useStore } from '../store'
import { uploadFile } from './api'

const inFlight = new Set<string>()

/**
 * Analyze a single active file by uploading it to the backend. Intended to be
 * triggered by the "Analyze" action in the Setup & Inputs step instead of
 * auto-uploading files the moment they are dropped.
 *
 * Skips files that are already analyzed, still being processed, or that have
 * lost their in-memory File blob (e.g. after a page reload, persist.null).
 */
export async function analyzeFile(fileId: string): Promise<void> {
  const { files, updateFile } = useStore.getState()
  const file = files.find((f) => f.id === fileId)

  if (!file) return
  if (file.taskId === 'dev-manual') return
  if (file.status === 'completed' || file.status === 'processing') return
  if (file.taskId) return
  if (!file.file) return
  if (inFlight.has(fileId)) return

  inFlight.add(fileId)
  updateFile(fileId, { status: 'processing' })

  try {
    const settings = useStore.getState().settingsByFile[fileId]
    const res = await uploadFile(file.file, {
      process: settings?.process,
      material: settings?.material,
      surface_finish: settings?.surfaceFinish,
      printing_process: settings?.printingProcess,
      tolerance: settings?.tolerance,
    })
    updateFile(fileId, {
      taskId: res.task_id,
      analysisId: res.analysis_id ?? null,
      fileUrl: res.file_url ?? null,
      status: 'processing',
    })
  } catch (err) {
    const errMsg = err instanceof Error ? err.message : 'Failed to upload CAD file to server.'
    updateFile(fileId, { status: 'failed', errorMessage: errMsg })
  } finally {
    inFlight.delete(fileId)
  }
}
