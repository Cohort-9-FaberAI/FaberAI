import { useContext, useState, useEffect } from 'react'
import { STLLoader } from 'three/examples/jsm/Addons.js'
import type { BufferGeometry } from 'three/webgpu'
import { ModelContext } from './ModelContext'

export function Model() {
  const context = useContext(ModelContext)

  const [geometry, setGeometry] = useState<BufferGeometry | undefined>(undefined)
  useEffect(() => {
    async function loadModelFromURL() {
      if (context && context?.file_url) {
        const geom = await new STLLoader().loadAsync(context.file_url)
        setGeometry(geom)
      }
    }
    loadModelFromURL()
  }, [])
  return (
    <mesh geometry={geometry} castShadow receiveShadow scale={0.5}>
      <meshStandardMaterial color="pink" roughness={0.65} metalness={0.65}></meshStandardMaterial>
    </mesh>
  )
}
