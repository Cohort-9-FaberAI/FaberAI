import { useFrame } from '@react-three/fiber'
import { useContext, useEffect, useRef, useState } from 'react'
import { Box3, Mesh, Vector3 } from 'three'
import type { ManufacturabilityIssue } from '../../types/analysis'
import { ModelContext } from './ModelContext'
type IssueMarkerProps = {
  position?: [number, number, number]
  boundingBox?: Box3
  type: 'BOUNDING BOX' | 'POINT'
  color: string
  issue: ManufacturabilityIssue
}

export default function IssueMarker({
  position,
  color,
  issue,
  type,
  boundingBox,
}: IssueMarkerProps) {
  const meshRef = useRef<Mesh>(null)
  const [hovered, setHovered] = useState(false)
  const context = useContext(ModelContext)

  useFrame(({ camera }) => {
    if (type == 'POINT') meshRef.current?.lookAt(camera.position)
  })

  //set this as the selected issue when hovered
  useEffect(() => {
    if (context) {
      context.selectedIssueSetter(hovered ? issue : null)
    }
  }, [hovered])

  return (
    <mesh
      ref={meshRef}
      position={type == 'POINT' ? position : boundingBox?.getCenter(new Vector3())}
      onPointerOver={(e) => {
        e.stopPropagation()
        setHovered(true)
      }}
      onPointerOut={() => setHovered(false)}
    >
      {type == 'POINT' ? (
        <circleGeometry args={[1, 32]} />
      ) : (
        <boxGeometry args={boundingBox?.getSize(new Vector3()).toArray()} />
      )}

      <meshBasicMaterial color={hovered ? 'yellow' : color} />
    </mesh>
  )
}
