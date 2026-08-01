import styles from './ModelPreview.module.css'
import { useState, useEffect, useContext, useCallback, useMemo } from 'react'
import { Canvas } from '@react-three/fiber'
import { OrbitControls } from '@react-three/drei'

import {
  type AnalysisResult,
  type ManufacturabilityIssue,
  type Vector3,
} from '../../types/analysis'
import { ModelContext, type ModelTransform } from './ModelContext'
import { Model } from './Model'
import IssueMarker from './IssueMarker'
import { PCFShadowMap } from 'three'
import { useStore } from '../../store'
import { isVisibleIssueSeverity } from '../../lib/analysisView'
type ModelPreviewProps = {
  analysis?: AnalysisResult | null
  previewFileUrl?: string | null
  previewBuffer?: ArrayBuffer | null
  onIssueSelected?: (issue: ManufacturabilityIssue | null) => void
  height?: number | string
}

function toPoint(value?: [number, number, number] | Vector3): [number, number, number] | null {
  if (Array.isArray(value) && value.length === 3) {
    return value.every((n) => typeof n === 'number') ? value : null
  }

  if (
    value &&
    !Array.isArray(value) &&
    typeof value.x === 'number' &&
    typeof value.y === 'number' &&
    typeof value.z === 'number'
  ) {
    return [value.x, value.y, value.z]
  }

  return null
}

function markerPoint(issue: ManufacturabilityIssue): [number, number, number] | null {
  return toPoint(issue.centroid) ?? toPoint(issue.three_js_highlight?.center)
}

function transformPoint(
  point: [number, number, number],
  transform?: ModelTransform | null,
): [number, number, number] {
  if (!transform) return point
  return [
    (point[0] - transform.center[0]) * transform.unitScale,
    (point[1] - transform.center[1]) * transform.unitScale,
    (point[2] - transform.center[2]) * transform.unitScale,
  ]
}

function markerColor(issue: ManufacturabilityIssue) {
  if (issue.three_js_highlight?.color) return issue.three_js_highlight.color
  if (issue.severity === 'blocker' || issue.severity === 'high') return 'red'
  if (issue.severity === 'major' || issue.severity === 'medium') return 'orange'
  return 'yellow'
}

function shouldShowMarker(issue: ManufacturabilityIssue) {
  return isVisibleIssueSeverity(issue.severity)
}

function isStepUrl(value?: string | null) {
  return Boolean(
    value
      ?.toLowerCase()
      .split('?')[0]
      .match(/\.(stp|step)$/),
  )
}

function getPreviewUrl(analysis: AnalysisResult | null, previewFileUrl: string | null) {
  const generatedPreviewUrl = analysis?.geometry_data?.preview_url ?? null
  const fileUrl = analysis?.file_url ?? null

  if (generatedPreviewUrl) return generatedPreviewUrl
  if (fileUrl && !isStepUrl(fileUrl)) return fileUrl
  if (previewFileUrl && !isStepUrl(previewFileUrl)) return previewFileUrl
  return null
}

function ModelCanvas() {
  const context = useContext(ModelContext)
  const modelTransform = context?.modelTransform
  const issueMarkers =
    context?.analysis?.issues
      .filter(shouldShowMarker)
      .map((issue) => ({ issue, position: markerPoint(issue) }))
      .filter(
        (marker): marker is { issue: ManufacturabilityIssue; position: [number, number, number] } =>
          marker.position !== null,
      ) ?? []

  return (
    <Canvas shadows={{ type: PCFShadowMap }} camera={{ position: [3, 3, 3], fov: 45 }}>
      <ambientLight intensity={2.4} />
      <directionalLight position={[4, 6, 3]} intensity={5} castShadow />
      <directionalLight position={[-3, 1, -4]} intensity={0.5} castShadow />
      <Model />

      {issueMarkers.map(({ issue, position }) => (
        <IssueMarker
          key={`${issue.issue_id}:${position.join(':')}`}
          position={transformPoint(position, modelTransform)}
          color={markerColor(issue)}
          issue={issue}
          type="POINT"
        />
      ))}

      <OrbitControls />
    </Canvas>
  )
}

export default function ModelPreview({
  analysis = null,
  previewFileUrl = null,
  previewBuffer,
  onIssueSelected,
  height,
}: ModelPreviewProps) {
  const [selectedIssue, setSelectedIssue] = useState<ManufacturabilityIssue | null>(null)
  const [loadError, setLoadError] = useState<{ source: string; message: string } | null>(null)
  const [loadedSource, setLoadedSource] = useState<string | null>(null)
  const [loadedTransform, setLoadedTransform] = useState<{
    source: string
    transform: ModelTransform
  } | null>(null)
  const devFileBuffer = useStore((s) => s.currentFileBuffer)
  const fileBuffer = previewBuffer !== undefined ? previewBuffer : devFileBuffer
  const modelUrl = useMemo(
    () => getPreviewUrl(analysis, previewFileUrl),
    [analysis, previewFileUrl],
  )
  const modelSource = modelUrl ?? (fileBuffer ? 'local-stl-buffer' : null)
  const hasRawStepOnly = Boolean(
    analysis?.geometry_data?.source_format === 'step' &&
    !analysis?.geometry_data?.preview_url &&
    isStepUrl(analysis?.file_url),
  )
  const canRenderModel = Boolean(modelUrl || fileBuffer)
  const handleModelLoaded = useCallback(() => {
    if (modelSource) {
      setLoadedSource(modelSource)
    }
  }, [modelSource])
  const handleModelError = useCallback(
    (message: string) => {
      if (modelSource) {
        setLoadError({ source: modelSource, message })
      }
    },
    [modelSource],
  )
  const handleModelTransform = useCallback(
    (transform: ModelTransform) => {
      if (modelSource) {
        setLoadedTransform({ source: modelSource, transform })
      }
    },
    [modelSource],
  )
  const activeLoadError = loadError?.source === modelSource ? loadError.message : null
  const activeTransform = loadedTransform?.source === modelSource ? loadedTransform.transform : null
  const isLoadingModel = Boolean(modelSource && loadedSource !== modelSource && !activeLoadError)

  //triggers onIssueSelected callback when the selected issue changes
  useEffect(() => {
    if (onIssueSelected) onIssueSelected(selectedIssue)
  }, [onIssueSelected, selectedIssue])

  if (!canRenderModel) {
    return (
      <div className={styles.placeholder}>
        {hasRawStepOnly
          ? 'This STEP report completed, but no converted STL preview was attached.'
          : 'Upload an STL file or wait for a completed analysis preview.'}
      </div>
    )
  }

  return (
    <div className={styles.wrapper} style={{ height }}>
      <div className={styles.canvasContainer}>
        {isLoadingModel && <div className={styles.overlay}>Loading 3D preview...</div>}
        {activeLoadError && <div className={styles.overlay}>{activeLoadError}</div>}
        <ModelContext.Provider
          value={{
            analysis,
            fileBuffer,
            modelUrl,
            modelTransform: activeTransform,
            previewFileUrl,
            onModelError: handleModelError,
            onModelLoaded: handleModelLoaded,
            onModelTransform: handleModelTransform,
            selectedIssueSetter: setSelectedIssue,
          }}
        >
          <ModelCanvas />
        </ModelContext.Provider>
      </div>
    </div>
  )
}
