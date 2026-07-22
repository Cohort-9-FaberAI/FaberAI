import React, { useContext, useState, useEffect } from 'react'
import { STLLoader } from 'three/examples/jsm/Addons.js'
import type { BufferGeometry } from 'three/webgpu'
import { ModelContext } from './ModelContext'

export function Model() {
  const context = useContext(ModelContext)

  const [geometry, setGeometry] = useState<BufferGeometry | undefined>(undefined)
  useEffect(() => {
    async function loadModelFromURL() {
      //SEEMS THAT THE FILE DOESNT EXIST, REPLACING WITH THIS FOR NOW
      // const url = context?.file_url
      const url =
        'https://files.printables.com/media/prints/77297936-f276-44d4-afa7-8cbef288a952/stls/13210738_5b9df843-1e7a-49c6-87fe-7a33da8a6106_6388b5b0-c80b-4e77-b18e-26046b8b89d1/hinge.stl'

      if (context && url) {
        const geom = await new STLLoader().loadAsync(url)
        setGeometry(geom)
      }
    }
    loadModelFromURL()
  }, [])
  return (
    <mesh geometry={geometry} castShadow receiveShadow>
      <meshStandardMaterial color="pink" roughness={0.65} metalness={0.65}></meshStandardMaterial>
    </mesh>
  )
}
