import { useContext } from 'react'
import { Canvas } from '@react-three/fiber'
import { OrbitControls, GizmoHelper, GizmoViewport } from '@react-three/drei'
import { PCFShadowMap, type BufferGeometry } from 'three'
import { ModelContext, type ModelTransform } from './ModelContext'
import { GhostModel } from './GhostModel'
import IssueMarker from './IssueMarker'
import type { ManufacturabilityIssue, Vector3 } from '../../types/analysis'
import { severityColor } from '../../lib/analysisView'

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

/**
 * Transforms a raw API centroid into geometry-local space.
 * preparePreviewGeometry does: translate(-center) then optionally scale(unitScale).
 * This function replicates that transform for point coordinates.
 */
function toGeometryLocalSpace(
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

/**
 * Projects a point (already in geometry-local space) onto the nearest
 * vertex of the BufferGeometry. The geometry vertices are also in
 * geometry-local space (output of preparePreviewGeometry).
 */
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

/** The mesh renders at scale={0.5}, so world-space = geometry-local * MESH_SCALE */
const MESH_SCALE = 0.5

function markerColor(issue: ManufacturabilityIssue) {
  return severityColor(issue.severity)
}

export default function XRayCanvas() {
  const context = useContext(ModelContext)
  const modelTransform = context?.modelTransform
  const sharedGeometry = context?.sharedGeometry

  // Pipeline: raw centroid → geometry-local space → snap to nearest vertex → scale to world space
  const issueMarkers =
    context?.analysis?.issues
      .map((issue) => ({ issue, position: markerPoint(issue) }))
      .filter(
        (marker): marker is { issue: ManufacturabilityIssue; position: [number, number, number] } =>
          marker.position !== null,
      )
      .map(({ issue, position }) => {
        // Step 1: Transform raw API centroid into geometry-local space
        const localPos = toGeometryLocalSpace(position, modelTransform)
        // Step 2: Project onto nearest actual mesh vertex
        const surfacePos = getClosestSurfacePoint(localPos, sharedGeometry)
        // Step 3: Scale to match GhostModel's scale={0.5}
        const worldPos: [number, number, number] = [
          surfacePos[0] * MESH_SCALE,
          surfacePos[1] * MESH_SCALE,
          surfacePos[2] * MESH_SCALE,
        ]
        return { issue, worldPos }
      }) ?? []

  return (
    <Canvas shadows={{ type: PCFShadowMap }} camera={{ position: [3, 3, 3], fov: 45 }}>
      <ambientLight intensity={1.8} />
      <directionalLight position={[4, 6, 3]} intensity={4} />
      <directionalLight position={[-3, 1, -4]} intensity={0.5} />

      <GhostModel />

      {issueMarkers.map(({ issue, worldPos }) => (
        <IssueMarker
          key={`xray_${issue.issue_id}:${worldPos.join(':')}`}
          position={worldPos}
          color={markerColor(issue)}
          radius={0.5}
          renderAsSphere={true}
          issue={issue}
          type="POINT"
        />
      ))}

      <OrbitControls autoRotate={false} />
      <GizmoHelper alignment="top-left" margin={[80, 80]}>
        <GizmoViewport />
      </GizmoHelper>
    </Canvas>
  )
}
