export type AnalysisStatus = 'pending' | 'processing' | 'completed' | 'failed'

export type IssueSeverity = 'blocker' | 'major' | 'minor'

export type SourceFormat = 'stl' | 'step'

export interface Vector3 {
  x: number
  y: number
  z: number
}

export interface BoundingBox {
  min: Vector3
  max: Vector3
}

export interface PartMetadata {
  units: string
  volume: number
  surface_area: number
  bounding_box: BoundingBox
}

export interface GeometryData {
  source_format: SourceFormat
  bounding_box: BoundingBox
  volume_mm3: number
  surface_area_mm2: number
  measurements_reliable: boolean
  center_mass: Vector3
}

export interface ManufacturabilityIssue {
  issue_id: string
  severity: IssueSeverity
  title: string
  description: string
  face_id?: number
  edge_id?: number
  centroid: [number, number, number]
}

export interface AnalysisResult {
  analysis_id: string
  filename: string
  status: AnalysisStatus
  manufacturability_score: number
  summary: string
  file_url: string
  part_metadata: PartMetadata
  geometry_data: GeometryData
  issues: ManufacturabilityIssue[]
}

export type AIAnswerMode = 'llm' | 'deterministic'

export interface AIAskRequest {
  question: string
  analysis_id?: string | null
  report?: Record<string, unknown> | null
  geometry?: Record<string, unknown> | null
}

export interface AIAnswer {
  question: string
  answer: string
  mode: AIAnswerMode
  model?: string | null
  referenced_rules: string[]
  analysis_id?: string | null
  degraded_reason?: string | null
}
