const API_BASE = import.meta.env.VITE_API_BASE_URL || 'http://127.0.0.1:8000'

export async function uploadFile(file: File) {
  const formData = new FormData()
  formData.append('file', file)

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

export async function getTaskStatus(taskId: string) {
  const res = await fetch(`${API_BASE}/tasks/${encodeURIComponent(taskId)}`)

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
