import { useFrame } from '@react-three/fiber'
import { useRef, useState } from 'react'
import { Box3, Mesh, Vector3 } from 'three'
import type { ManufacturabilityIssue } from '../../types/analysis'
import { Color } from 'three'
import { useStore } from '../../store/responsiveStore'
import { useCursor } from '@react-three/drei'

const POINT_MARKER_RADIUS = 1

type IssueMarkerProps = {
  position?: [number, number, number]
  boundingBox?: Box3
  type: 'BOUNDING BOX' | 'POINT'
  color: string
  overrideColor?: string
  radius?: number
  renderAsSphere?: boolean
  issue: ManufacturabilityIssue
}

export default function IssueMarker({
  position,
  color,
  overrideColor,
  radius,
  renderAsSphere,
  type,
  issue,
  boundingBox,
}: IssueMarkerProps) {
  const meshRef = useRef<Mesh>(null)
  const [hovered, setHovered] = useState(false)
  const setHighlightedIssue = useStore((s) => s.setHighlightedIssue)
  const highlightedIssue = useStore((s) => s.highlightedIssue)
  const setFocusedIssue = useStore((s) => s.setFocusedIssue)

  useCursor(hovered)
  useFrame(({ camera }) => {
    if (type == 'POINT' && !renderAsSphere) meshRef.current?.lookAt(camera.position)
  })

  return (
    <mesh
      ref={meshRef}
      position={type == 'POINT' ? position : boundingBox?.getCenter(new Vector3())}
      onPointerOver={(e) => {
        e.stopPropagation()
        setHighlightedIssue(issue.issue_id)
        setHovered(true)
      }}
      onPointerOut={() => {
        setHighlightedIssue(null)
        setHovered(false)
      }}
      onClick={(e) => {
        e.stopPropagation()
        setFocusedIssue(issue.issue_id)
      }}
      scale={hovered || issue.issue_id === highlightedIssue ? 1.2 : 1}
    >
      {renderAsSphere ? (
        <sphereGeometry args={[radius ?? 0.22, 24, 24]} />
      ) : type == 'POINT' ? (
        <circleGeometry args={[radius ?? POINT_MARKER_RADIUS, 32]} />
      ) : (
        <boxGeometry args={boundingBox?.getSize(new Vector3()).toArray()} />
      )}

      <meshBasicMaterial
        color={
          issue.issue_id === highlightedIssue
            ? new Color(overrideColor ?? color).offsetHSL(0, 0.1, 0.05)
            : (overrideColor ?? color)
        }
      />
    </mesh>
  )
}
