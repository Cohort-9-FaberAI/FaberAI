import { useContext, useState, useEffect, useRef } from 'react'
import { Box3, Object3D, Vector3, type BufferGeometry } from 'three/webgpu'
import { ModelContext } from './ModelContext'
import { useThree } from '@react-three/fiber'
import { getGeometry } from './api'

export function Model() {
  const context = useContext(ModelContext)
  // const [geometry, setGeometry] = useState<BufferGeometry | undefined>(undefined)
  const [geometries, setGeometries] = useState<BufferGeometry[]>([])
  const { camera } = useThree()
  const objectRef = useRef<Object3D>(null)

  //loads the geometry from the URL on-load
  useEffect(() => {
    async function loadModelFromURL() {
      if (context && context?.analysis.file_url) {
        // const geom = await getGeometry(context.analysis.file_url, "STL")
        const geom = await getGeometry(context.analysis.file_url, 'STEP')
        if (geom) setGeometries(geom)
      }
    }
    loadModelFromURL()
  }, [])

  useEffect(() => {
    return () => {
      geometries.forEach((geometry) => geometry.dispose())
    }
  }, [geometries]) //cleaning when reloading

  // Gives the camera an initial position along the bounding box of the mesh
  useEffect(() => {
    if (objectRef.current != null) {
      objectRef.current.updateWorldMatrix(true, true)
      const box = new Box3().setFromObject(objectRef.current)
      const center = box.getCenter(new Vector3())
      const size = box.getSize(new Vector3())
      const distance = Math.max(size.x, size.y, size.z)
      camera.position.set(center.x + distance, center.y + distance, center.z + distance)
      camera.lookAt(center)
    }
  }, [geometries])

  return (
    <group ref={objectRef}>
      {geometries.map((geometry, i) => (
        <mesh key={`geometry_${i}`} geometry={geometry} castShadow receiveShadow scale={0.5}>
          <meshStandardMaterial
            color="pink"
            roughness={0.65}
            metalness={0.65}
          ></meshStandardMaterial>
        </mesh>
      ))}
    </group>
  )
}
