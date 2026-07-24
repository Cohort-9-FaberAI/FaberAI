import { createContext } from 'react'
import { type AnalysisResult, type ManufacturabilityIssue } from '../../types/analysis'

export type ModelContextType = {
  analysis: AnalysisResult
  selectedIssueSetter: (issue: ManufacturabilityIssue | null) => void
}

export const ModelContext = createContext<ModelContextType | null>(null)
