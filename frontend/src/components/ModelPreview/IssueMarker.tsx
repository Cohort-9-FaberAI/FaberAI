import { useFrame } from '@react-three/fiber'
import { useRef, useState } from 'react'
import { Mesh } from 'three'

type IssueMarkerProps = {
  position: [number, number, number]
  color: string
}

export default function IssueMarker({ position, color }: IssueMarkerProps) {
  const meshRef = useRef<Mesh>(null)
  const [hovered, setHovered] = useState(false)

  useFrame(({ camera }) => {
    if (!meshRef.current) console.log('none')
    meshRef.current?.lookAt(camera.position)
  })
  return (
    <mesh
      ref={meshRef}
      position={position}
      onPointerOver={(e) => {
        e.stopPropagation()
        setHovered(true)
      }}
      onPointerOut={() => setHovered(false)}
    >
      <circleGeometry args={[1, 32]} />
      <meshBasicMaterial color={hovered ? 'yellow' : color} />
    </mesh>
  )
}
