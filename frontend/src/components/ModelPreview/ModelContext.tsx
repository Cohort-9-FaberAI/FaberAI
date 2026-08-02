import { createContext } from 'react'
import { type AnalysisResult, type ManufacturabilityIssue } from '../../types/analysis'

export type ModelTransform = {
  center: [number, number, number]
  unitScale: number
}

export type ModelContextType = {
  analysis: AnalysisResult | null
  fileBuffer: ArrayBuffer | null
  modelUrl?: string | null
  modelTransform?: ModelTransform | null
  previewFileUrl?: string | null
  onModelError?: (message: string) => void
  onModelLoaded?: () => void
  onModelTransform?: (transform: ModelTransform) => void
  selectedIssueSetter: (issue: ManufacturabilityIssue | null) => void
}

export const ModelContext = createContext<ModelContextType | null>(null)
