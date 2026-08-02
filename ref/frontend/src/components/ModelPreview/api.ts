import type { AnalysisResult } from '../../types/analysis'

export async function fetchAnalysis() {
  const res = await fetch('http://localhost:8000/analyze-mock', {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({}),
  })
  const result = (await res.json()) as AnalysisResult
  return result
}
