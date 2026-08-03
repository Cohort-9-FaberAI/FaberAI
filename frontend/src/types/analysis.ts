export type AnalysisStatus = 'pending' | 'processing' | 'completed' | 'failed'

export type IssueSeverity = 'blocker' | 'major' | 'minor' | 'high' | 'medium' | 'low'

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
  preview_url?: string
  bounding_box: BoundingBox
  volume_mm3: number
  surface_area_mm2: number
  measurements_reliable: boolean
  center_mass: Vector3
}

export type Centroid = [number, number, number] | { x: number; y: number; z: number }

export interface ManufacturabilityIssue {
  issue_id: string
  severity: IssueSeverity
  title?: string
  description?: string
  type?: string
  message?: string
  recommendation?: string
  face_id?: number
  edge_id?: number
  centroid?: Centroid
  three_js_highlight?: {
    type: string
    color: string
    min: Vector3
    max: Vector3
    center: Vector3
  }
}

export interface AnalysisResult {
  analysis_id: string
  filename: string
  status: AnalysisStatus
  manufacturability_score: number
  printing_score?: number | null
  molding_score?: number | null
  printing_manufacturable?: boolean | null
  molding_manufacturable?: boolean | null
  summary: string
  file_url?: string
  source_file_url?: string
  part_metadata: PartMetadata
  geometry_data: GeometryData
  dfm_report?: Record<string, unknown>
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
