import type { AnalysisResult, ManufacturabilityIssue } from '../../types/analysis'

export const bracketIssues: ManufacturabilityIssue[] = [
  {
    issue_id: 'M1-2815',
    severity: 'major',
    title: 'Wall thickness exceeds material maximum',
    description: 'A thick wall section creates sink, void, and cycle-time risk.',
    recommendation: 'Core out the thick section and keep walls between 0.80 and 5.00 mm.',
    centroid: [18, 8, 24],
  },
  {
    issue_id: 'M1-1134',
    severity: 'major',
    title: 'Abrupt thin-to-thick transition',
    description: 'The neighboring wall transition is outside the material limit.',
    recommendation: 'Blend the transition and hold wall variation within 25%.',
    centroid: [43, 4, 48],
  },
  {
    issue_id: 'M3-14',
    severity: 'major',
    title: 'Insufficient draft',
    description: 'This vertical face has less than 1 degree of draft.',
    recommendation: 'Add at least 1 degree of draft per side.',
    centroid: [74, 12, 31],
  },
  {
    issue_id: 'M5-3',
    severity: 'major',
    title: 'Rib thickness ratio',
    description: 'The rib is thicker than 50% of the adjoining wall.',
    recommendation: 'Keep rib thickness between 50% and 60% of the nominal wall.',
    centroid: [47, 36, 17],
  },
  {
    issue_id: 'M6-8',
    severity: 'minor',
    title: 'Boss design',
    description: 'This boss creates a localized thick mass.',
    recommendation: 'Hollow the boss wall to 40% to 60% of the nominal wall.',
    centroid: [82, 49, 15],
  },
  {
    issue_id: 'P1-322',
    severity: 'major',
    title: 'Overhang angle',
    description: 'The down-facing surface extends beyond the 45 degree limit.',
    recommendation: 'Reorient the part or redesign the unsupported face.',
    centroid: [8, 51, 34],
  },
  {
    issue_id: 'P2-21',
    severity: 'minor',
    title: 'Minimum feature size',
    description: 'A local feature is below the 1.00 mm FDM minimum.',
    recommendation: 'Increase the feature to at least 1.50 mm.',
    centroid: [58, 58, 48],
  },
]

export const bracketAnalysis: AnalysisResult = {
  analysis_id: 'fa87e9a9-1bee-4d88-aee3-b0ab7de959a9',
  filename: 'faberai-sample-part.stl',
  status: 'completed',
  manufacturability_score: 35,
  molding_score: 35,
  printing_score: 25,
  molding_manufacturable: false,
  printing_manufacturable: false,
  summary: 'Injection molding is recommended, but the part needs review before production.',
  file_url: '/faberai-sample-part.stl',
  part_metadata: {
    units: 'mm',
    volume: 69456.81,
    surface_area: 21187.03,
    bounding_box: {
      min: { x: 0, y: 0, z: 0 },
      max: { x: 90, y: 60, z: 51.5 },
    },
  },
  geometry_data: {
    source_format: 'stl',
    bounding_box: {
      min: { x: 0, y: 0, z: 0 },
      max: { x: 90, y: 60, z: 51.5 },
    },
    volume_mm3: 69456.81,
    surface_area_mm2: 21187.03,
    measurements_reliable: true,
    center_mass: { x: 45, y: 30, z: 25.75 },
  },
  issues: bracketIssues,
}

const logoIssues: ManufacturabilityIssue[] = [
  {
    issue_id: 'L-M1',
    severity: 'major',
    title: 'Thin edge transition',
    description: 'A narrow transition may not fill consistently during molding.',
    recommendation: 'Increase the local edge thickness and blend the transition.',
    centroid: [-1.7, 1.35, 0.3],
  },
  {
    issue_id: 'L-M3',
    severity: 'minor',
    title: 'Draft review',
    description: 'A vertical face needs additional release angle.',
    recommendation: 'Add 1 degree of draft along the selected pull direction.',
    centroid: [1.55, 1.2, 0.28],
  },
  {
    issue_id: 'L-P1',
    severity: 'major',
    title: 'Unsupported lower edge',
    description: 'The lower feature creates a localized support requirement.',
    recommendation: 'Reorient the part or soften the unsupported edge.',
    centroid: [-0.85, -1.72, 0.22],
  },
  {
    issue_id: 'L-P2',
    severity: 'minor',
    title: 'Small feature',
    description: 'A small logo feature is close to the printing limit.',
    recommendation: 'Increase the feature width by 0.2 mm.',
    centroid: [0.95, -1.48, 0.3],
  },
  {
    issue_id: 'L-M5',
    severity: 'minor',
    title: 'Local thickness variation',
    description: 'The center transition changes thickness abruptly.',
    recommendation: 'Use a smoother transition through the center feature.',
    centroid: [0, -0.1, 0.38],
  },
]

export const logoAnalysis: AnalysisResult = {
  analysis_id: 'landing-logo-analysis',
  filename: 'logo.stl',
  status: 'completed',
  manufacturability_score: 87,
  molding_score: 87,
  printing_score: 92,
  molding_manufacturable: true,
  printing_manufacturable: true,
  summary: 'The FaberAI mark is manufacturable with minor local refinements.',
  file_url: '/logo.stl',
  part_metadata: {
    units: 'mm',
    volume: 0,
    surface_area: 0,
    bounding_box: {
      min: { x: -1.9536, y: -2.1497, z: -0.3906 },
      max: { x: 1.9536, y: 1.8517, z: 0.3837 },
    },
  },
  geometry_data: {
    source_format: 'stl',
    bounding_box: {
      min: { x: -1.9536, y: -2.1497, z: -0.3906 },
      max: { x: 1.9536, y: 1.8517, z: 0.3837 },
    },
    volume_mm3: 0,
    surface_area_mm2: 0,
    measurements_reliable: true,
    center_mass: { x: 0, y: -0.149, z: -0.0034 },
  },
  issues: logoIssues,
}

export type LoginPreviewSample = {
  id: string
  name: string
  process: string
  score: number
  markerRadius: number
  analysis: AnalysisResult
  readouts: Array<{
    label: string
    value: string
    detail: string
    tone: 'blue' | 'warning' | 'success' | 'danger'
  }>
}

export const loginPreviewSamples: LoginPreviewSample[] = [
  {
    id: 'bracket',
    name: 'Production bracket',
    process: 'Molding + printing review',
    score: 35,
    markerRadius: 0.5,
    analysis: bracketAnalysis,
    readouts: [
      { label: 'Wall thickness', value: '100.83 mm', detail: 'Above material max', tone: 'danger' },
      { label: 'Draft angle', value: '0.0 deg', detail: 'Add at least 1.0 deg', tone: 'warning' },
      { label: 'Mapped findings', value: '7 markers', detail: 'Pinned to geometry', tone: 'blue' },
    ],
  },
  {
    id: 'faber-mark',
    name: 'FaberAI mark',
    process: 'Feature and edge review',
    score: 87,
    markerRadius: 0.075,
    analysis: logoAnalysis,
    readouts: [
      { label: 'Molding score', value: '87 / 100', detail: 'Manufacturable', tone: 'success' },
      { label: 'Printing score', value: '92 / 100', detail: 'Ready to print', tone: 'success' },
      { label: 'Mapped findings', value: '5 markers', detail: 'Minor refinements', tone: 'blue' },
    ],
  },
]
