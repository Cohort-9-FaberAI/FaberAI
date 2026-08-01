import type { AnalysisResult } from '../../types/analysis'
import { API_BASE } from '../../lib/api'

export async function fetchAnalysis() {
  const res = await fetch(`${API_BASE}/analyze-mock`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({}),
  })
  const result = (await res.json()) as AnalysisResult
  return result
}
