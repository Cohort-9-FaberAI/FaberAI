import { useContext, useEffect, useRef } from 'react'
import { Box3, DoubleSide, Object3D, Vector3 } from 'three'
import { ModelContext } from './ModelContext'
import { useThree } from '@react-three/fiber'

export function GhostModel({ fitToViewport = false }: { fitToViewport?: boolean }) {
  const context = useContext(ModelContext)
  const geometry = context?.sharedGeometry
  const { camera, size: viewportSize } = useThree()
  const objectRef = useRef<Object3D>(null)

  // Gives the camera an initial position along the bounding box of the mesh
  useEffect(() => {
    if (objectRef.current != null && geometry) {
      const box = new Box3().setFromObject(objectRef.current)
      const center = box.getCenter(new Vector3())
      const size = box.getSize(new Vector3())
      const distance = Math.max(size.x, size.y, size.z)
      const aspect = viewportSize.width / Math.max(viewportSize.height, 1)
      const portraitFit = fitToViewport && aspect < 1 ? Math.min(1 / aspect, 1.85) : 1
      const fittedDistance = distance * portraitFit
      camera.position.set(
        center.x + fittedDistance,
        center.y + fittedDistance,
        center.z + fittedDistance,
      )
      camera.lookAt(center)
    }
  }, [geometry, camera, fitToViewport, viewportSize.height, viewportSize.width])

  if (!geometry) return null

  return (
    <mesh ref={objectRef} geometry={geometry} scale={0.5}>
      <meshPhysicalMaterial
        color="#0858F4"
        roughness={0.25}
        metalness={0.1}
        clearcoat={0.3}
        transparent={true}
        opacity={0.22}
        side={DoubleSide}
        depthWrite={false}
      />
    </mesh>
  )
}
