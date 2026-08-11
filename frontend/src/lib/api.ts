import type { AIAnswer, AIAskRequest } from '../types/analysis'

export const API_BASE = import.meta.env.VITE_API_BASE_URL || 'http://127.0.0.1:8000'

export interface AIAskPayload {
  question: string
  analysis_id?: string
  report?: Record<string, unknown>
  geometry?: Record<string, unknown>
}

export interface AIAskResponse {
  question: string
  answer: string
  mode: 'llm' | 'deterministic'
  model?: string | null
  referenced_rules: string[]
  analysis_id?: string | null
  degraded_reason?: string | null
}

export interface UploadResponse {
  message: string
  task_id: string
  analysis_id?: string | null
  filename: string
  storage_path: string
  file_url?: string | null
  source_file_url?: string | null
  status: string
}

export interface UploadInputs {
  process?: string | null
  material?: string | null
  surface_finish?: string | null
  printing_process?: string | null
  tolerance?: string | null
}

export async function uploadFile(file: File, inputs?: UploadInputs): Promise<UploadResponse> {
  const formData = new FormData()
  formData.append('file', file)

  for (const [key, value] of Object.entries(inputs ?? {})) {
    if (value !== undefined && value !== null && value !== '') {
      formData.append(key, String(value))
    }
  }

  const res = await fetch(`${API_BASE}/upload/`, {
    method: 'POST',
    body: formData,
  })

  if (!res.ok) {
    const body = await res.json().catch(() => null)
    throw new Error(body?.error?.message || `Upload failed (${res.status})`)
  }

  return res.json()
}

export async function getTaskStatus(taskId: string, analysisId?: string | null) {
  const url = new URL(`${API_BASE}/tasks/${encodeURIComponent(taskId)}`)
  if (analysisId) {
    url.searchParams.set('analysis_id', analysisId)
  }
  const res = await fetch(url.toString())

  if (!res.ok) {
    const body = await res.json().catch(() => null)
    throw new Error(body?.error?.message || `Task lookup failed (${res.status})`)
  }

  return res.json()
}

export async function getHealthCheck() {
  const res = await fetch(`${API_BASE}/`)

  if (!res.ok) {
    const body = await res.json().catch(() => null)
    throw new Error(body?.error?.message || `Health check failed (${res.status})`)
  }

  return res.json()
}

export async function createAnalysis(data: Record<string, unknown>) {
  const res = await fetch(`${API_BASE}/analysis/`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(data),
  })

  if (!res.ok) {
    const body = await res.json().catch(() => null)
    throw new Error(body?.error?.message || `Create analysis failed (${res.status})`)
  }

  return res.json()
}

export async function getMockAnalysis() {
  const res = await fetch(`${API_BASE}/analyze-mock`, { method: 'POST' })

  if (!res.ok) {
    const body = await res.json().catch(() => null)
    throw new Error(body?.error?.message || `Mock analysis failed (${res.status})`)
  }

  return res.json()
}

export async function askFaberAI(
  payload: AIAskPayload | AIAskRequest,
): Promise<AIAskResponse & AIAnswer> {
  const res = await fetch(`${API_BASE}/ai/ask`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(payload),
  })

  if (!res.ok) {
    const body = await res.json().catch(() => null)
    throw new Error(body?.error?.message || `AI request failed (${res.status})`)
  }

  return res.json()
}

export const askAI = askFaberAI as unknown as (payload: AIAskRequest) => Promise<AIAnswer>

export async function downloadAnalysisReportPdf(
  analysis: Record<string, unknown>,
  includeComparison: boolean,
  process?: string | null,
  material?: string | null,
  tolerance?: string | null,
  printingProcess?: string | null,
  surfaceFinish?: string | null,
  inline?: boolean,
) {
  const res = await fetch(`${API_BASE}/analysis/report.pdf`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      analysis,
      include_comparison: includeComparison,
      process,
      material,
      tolerance,
      printing_process: printingProcess,
      surface_finish: surfaceFinish,
      inline,
    }),
  })

  if (!res.ok) {
    const body = await res.json().catch(() => null)
    throw new Error(body?.error?.message || `PDF download failed (${res.status})`)
  }

  const disposition = res.headers.get('content-disposition')
  const filename =
    disposition?.match(/filename="([^"]+)"/)?.[1] ??
    disposition?.match(/filename=([^;]+)/)?.[1]?.trim() ??
    'faberai-dfm-report.pdf'

  return {
    blob: await res.blob(),
    filename,
  }
}
