import { createContext } from 'react'
import type { BufferGeometry } from 'three'
import { type AnalysisResult, type ManufacturabilityIssue } from '../../types/analysis'

export type ModelTransform = {
  center: [number, number, number]
  unitScale: number
}

export type ModelContextType = {
  analysis: AnalysisResult | null
  fileBuffer: ArrayBuffer | null
  sourceFormat?: 'stl' | 'step' | null
  modelUrl?: string | null
  modelTransform?: ModelTransform | null
  previewFileUrl?: string | null
  sharedGeometry?: BufferGeometry | null
  onModelError?: (message: string) => void
  onModelLoaded?: () => void
  onGeometryLoaded?: (geometry: BufferGeometry) => void
  onModelTransform?: (transform: ModelTransform) => void
  selectedIssueSetter: (issue: ManufacturabilityIssue | null) => void
}

export const ModelContext = createContext<ModelContextType | null>(null)
