import styles from './ModelPreview.module.css'
import { useState, useContext, useCallback, useMemo, useRef } from 'react'
import { Canvas } from '@react-three/fiber'
import { OrbitControls, Float, GizmoHelper, GizmoViewport } from '@react-three/drei'

import {
  type AnalysisResult,
  type ManufacturabilityIssue,
  type Vector3,
} from '../../types/analysis'
import { ModelContext, type ModelTransform } from './ModelContext'
import { Model } from './Model'
import IssueMarker from './IssueMarker'
import { PCFShadowMap, type BufferGeometry } from 'three'
import { useStore } from '../../store'
import { isVisibleIssueSeverity } from '../../lib/analysisView'
import Toolbar from './Toolbar'
import XRayCanvas from './XRayCanvas'
import { LuBox, LuLayers } from 'react-icons/lu'
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

const MESH_SCALE = 0.5

function getClosestSurfacePoint(
  point: [number, number, number],
  geometry?: BufferGeometry | null,
): [number, number, number] {
  if (!geometry) return point
  const posAttr = geometry.getAttribute('position')
  if (!posAttr || posAttr.count === 0) return point

  const arr = posAttr.array
  const count = posAttr.count * 3
  let minDistanceSq = Infinity
  let closestX = point[0]
  let closestY = point[1]
  let closestZ = point[2]

  for (let i = 0; i < count; i += 3) {
    const vx = arr[i]
    const vy = arr[i + 1]
    const vz = arr[i + 2]

    const dx = vx - point[0]
    const dy = vy - point[1]
    const dz = vz - point[2]
    const distSq = dx * dx + dy * dy + dz * dz

    if (distSq < minDistanceSq) {
      minDistanceSq = distSq
      closestX = vx
      closestY = vy
      closestZ = vz
    }
  }

  return [closestX, closestY, closestZ]
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
  const sharedGeometry = context?.sharedGeometry
  const isLoginLogo = context?.modelUrl === '/logo.stl' || context?.modelUrl?.endsWith('logo.stl')
  const issueMarkers =
    context?.analysis?.issues
      .filter(shouldShowMarker)
      .map((issue) => ({ issue, position: markerPoint(issue) }))
      .filter(
        (marker): marker is { issue: ManufacturabilityIssue; position: [number, number, number] } =>
          marker.position !== null,
      )
      .map(({ issue, position }) => {
        const localPos = transformPoint(position, modelTransform)
        const surfacePos = getClosestSurfacePoint(localPos, sharedGeometry)
        const worldPos: [number, number, number] = [
          surfacePos[0] * MESH_SCALE,
          surfacePos[1] * MESH_SCALE,
          surfacePos[2] * MESH_SCALE,
        ]
        return { issue, worldPos }
      }) ?? []

  return (
    <Canvas shadows={{ type: PCFShadowMap }} camera={{ position: [3, 3, 3], fov: 45 }}>
      <ambientLight intensity={2.4} />
      <directionalLight position={[4, 6, 3]} intensity={5} castShadow />
      <directionalLight position={[-3, 1, -4]} intensity={0.5} castShadow />

      {isLoginLogo ? (
        <Float speed={2.2} rotationIntensity={0.6} floatIntensity={1.8}>
          <Model />
        </Float>
      ) : (
        <Model />
      )}

      {issueMarkers.map(({ issue, worldPos }) => (
        <IssueMarker
          key={`${issue.issue_id}:${worldPos.join(':')}`}
          position={worldPos}
          color={markerColor(issue)}
          radius={0.5}
          renderAsSphere={true}
          issue={issue}
          type="POINT"
        />
      ))}

      <OrbitControls autoRotate={Boolean(isLoginLogo)} autoRotateSpeed={1.5} />
      {!isLoginLogo && (
        <GizmoHelper alignment="top-left" margin={[80, 80]}>
          <GizmoViewport />
        </GizmoHelper>
      )}
    </Canvas>
  )
}

export default function ModelPreview({
  analysis = null,
  previewFileUrl = null,
  previewBuffer,
  height,
}: ModelPreviewProps) {
  const [loadError, setLoadError] = useState<{ source: string; message: string } | null>(null)
  const [loadedSource, setLoadedSource] = useState<string | null>(null)
  const [loadedTransform, setLoadedTransform] = useState<{
    source: string
    transform: ModelTransform
  } | null>(null)
  const [sharedGeometry, setSharedGeometry] = useState<{
    source: string
    geometry: BufferGeometry
  } | null>(null)
  const [showXRay, setShowXRay] = useState<boolean>(false)
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
  const handleGeometryLoaded = useCallback(
    (geometry: BufferGeometry) => {
      if (modelSource) {
        setSharedGeometry({ source: modelSource, geometry })
      }
    },
    [modelSource],
  )
  const activeLoadError = loadError?.source === modelSource ? loadError.message : null
  const activeTransform = loadedTransform?.source === modelSource ? loadedTransform.transform : null
  const activeGeometry = sharedGeometry?.source === modelSource ? sharedGeometry.geometry : null
  const isLoadingModel = Boolean(modelSource && loadedSource !== modelSource && !activeLoadError)

  const isLoginLogo = modelUrl === '/logo.stl' || Boolean(modelUrl?.endsWith('logo.stl'))
  const hasIssues = Boolean(
    analysis?.issues &&
    analysis.issues.filter((issue) => isVisibleIssueSeverity(issue.severity)).length > 0,
  )
  const shouldDisplayXRay = hasIssues && !isLoginLogo && showXRay

  const containerRef = useRef<HTMLDivElement>(null)
  const [isFullScreen, setFullScreen] = useState<boolean>(false)

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
      <div ref={containerRef} className={styles.canvasContainer}>
        {hasIssues && !isLoginLogo && (
          <div className={styles.viewModeSelector}>
            <button
              type="button"
              className={`${styles.viewModeOption} ${!showXRay ? styles.activeOption : ''}`}
              onClick={() => setShowXRay(false)}
            >
              <LuBox size={16} />
              <span>Solid</span>
            </button>
            <button
              type="button"
              className={`${styles.viewModeOption} ${showXRay ? styles.activeOption : ''}`}
              onClick={() => setShowXRay(true)}
            >
              <LuLayers size={16} />
              <span>X-Ray</span>
            </button>
          </div>
        )}
        {!isLoginLogo && (
          <Toolbar
            onFullScreenPressed={() => {
              if (isFullScreen) document.exitFullscreen()
              else containerRef.current?.requestFullscreen()
              setFullScreen(!isFullScreen)
            }}
            isFullScreen={isFullScreen}
          />
        )}
        {isLoadingModel && <div className={styles.overlay}>Loading 3D preview...</div>}
        {activeLoadError && <div className={styles.overlay}>{activeLoadError}</div>}
        <ModelContext.Provider
          value={{
            analysis,
            fileBuffer,
            modelUrl,
            modelTransform: activeTransform,
            previewFileUrl,
            sharedGeometry: activeGeometry,
            onModelError: handleModelError,
            onModelLoaded: handleModelLoaded,
            onGeometryLoaded: handleGeometryLoaded,
            onModelTransform: handleModelTransform,
          }}
        >
          {shouldDisplayXRay ? <XRayCanvas /> : <ModelCanvas />}
        </ModelContext.Provider>
      </div>
    </div>
  )
}
