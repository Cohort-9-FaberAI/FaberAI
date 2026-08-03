import { useContext, useState, useEffect, useRef } from 'react'
import { STLLoader } from 'three/examples/jsm/Addons.js'
import { Box3, DoubleSide, Object3D, Vector3, type BufferGeometry } from 'three'
import { ModelContext, type ModelTransform } from './ModelContext'
import { useThree } from '@react-three/fiber'

function preparePreviewGeometry(source: BufferGeometry): {
  geometry: BufferGeometry
  transform: ModelTransform
} {
  const prepared = source.clone()
  prepared.computeBoundingBox()
  const center = new Vector3()
  const size = new Vector3()
  prepared.boundingBox?.getCenter(center)
  prepared.boundingBox?.getSize(size)
  const maxDimension = Math.max(size.x, size.y, size.z)
  const unitScale = Number.isFinite(maxDimension) && maxDimension > 10000 ? 0.001 : 1
  prepared.translate(-center.x, -center.y, -center.z)
  if (unitScale !== 1) {
    prepared.scale(unitScale, unitScale, unitScale)
  }
  prepared.computeBoundingBox()
  prepared.computeBoundingSphere()
  prepared.computeVertexNormals()
  return {
    geometry: prepared,
    transform: {
      center: [center.x, center.y, center.z],
      unitScale,
    },
  }
}

export function Model() {
  const context = useContext(ModelContext)
  const modelUrl = context?.modelUrl
  const fileBuffer = context?.fileBuffer
  const onModelError = context?.onModelError
  const onModelLoaded = context?.onModelLoaded
  const onGeometryLoaded = context?.onGeometryLoaded
  const onModelTransform = context?.onModelTransform
  const [geometry, setGeometry] = useState<BufferGeometry | undefined>(undefined)
  const { camera } = useThree()
  const objectRef = useRef<Object3D>(null)

  //loads the geometry from the URL on-load
  useEffect(() => {
    let cancelled = false

    async function loadModelFromURL() {
      setGeometry(undefined)
      if (modelUrl) {
        try {
          const { geometry: geom, transform } = preparePreviewGeometry(
            await new STLLoader().loadAsync(modelUrl),
          )
          if (cancelled) return
          onModelTransform?.(transform)
          setGeometry(geom)
          onGeometryLoaded?.(geom)
          onModelLoaded?.()
        } catch {
          if (cancelled) return
          onModelError?.('The generated STL preview could not be loaded.')
        }
        return
      }

      if (fileBuffer) {
        try {
          const { geometry: geom, transform } = preparePreviewGeometry(
            new STLLoader().parse(fileBuffer),
          )
          if (cancelled) return
          onModelTransform?.(transform)
          setGeometry(geom)
          onGeometryLoaded?.(geom)
          onModelLoaded?.()
        } catch {
          if (cancelled) return
          onModelError?.('The local STL preview could not be parsed.')
        }
      }
    }
    loadModelFromURL()

    return () => {
      cancelled = true
    }
  }, [modelUrl, fileBuffer, onModelError, onModelLoaded, onGeometryLoaded, onModelTransform])

  //Gives the camera an initial position along the bounding box of the mesh
  useEffect(() => {
    if (objectRef.current != null) {
      const box = new Box3().setFromObject(objectRef.current)
      const center = box.getCenter(new Vector3())
      const size = box.getSize(new Vector3())
      const distance = Math.max(size.x, size.y, size.z)
      camera.position.set(center.x + distance, center.y + distance, center.z + distance)
      camera.lookAt(center)
    }
  }, [geometry, camera])

  return (
    <mesh ref={objectRef} geometry={geometry} scale={0.5}>
      <meshPhysicalMaterial
        color="#0858F4"
        roughness={0.45}
        metalness={0.05}
        clearcoat={0.1}
        side={DoubleSide}
      />
    </mesh>
  )
}
