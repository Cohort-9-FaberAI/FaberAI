import React, { useState } from 'react'
import { Canvas } from '@react-three/fiber'
import styles from './ModelPreview.module.css'
import { OrbitControls } from '@react-three/drei'
import { STLLoader } from 'three/addons/loaders/STLLoader.js'

type PlaceholderProps = {
  buffer: ArrayBuffer
}

function Model({ buffer }: PlaceholderProps) {
  const loader = new STLLoader()
  return (
    buffer.byteLength > 0 && (
      <mesh geometry={loader.parse(buffer)} castShadow receiveShadow>
        <meshStandardMaterial color="pink" roughness={0.65} metalness={0.65}></meshStandardMaterial>
      </mesh>
    )
  )
}

function ModelCanvas({ buffer }: PlaceholderProps) {
  return (
    <Canvas shadows camera={{ position: [3, 3, 3], fov: 45 }}>
      <ambientLight intensity={2.4} />
      <directionalLight position={[4, 6, 3]} intensity={5} castShadow />

      <directionalLight position={[-3, 1, -4]} intensity={0.5} castShadow />

      <Model buffer={buffer} />
      <OrbitControls />
    </Canvas>
  )
}

export default function ModelPreview() {
  const [buffer, setBuffer] = useState(new ArrayBuffer(0))

  return (
    <div>
      {/* TEMPORARY STL UPLOAD FIELD WITH PROP DRILLING; this is until I get some more info on how to get the buffer from the Store
                It seems that as is, the file buffer is not actually being stored in the Store. Will ask lead on that.
            */}
      <input
        type="file"
        accept=".stl"
        onChange={async (event: React.ChangeEvent<HTMLInputElement>) => {
          const selectedFile = event.target.files?.[0]
          if (!selectedFile) {
            return
          }
          const buffer = await selectedFile.arrayBuffer()
          setBuffer(buffer)
        }}
      />
      <div className={styles.CanvasContainer}>
        <ModelCanvas buffer={buffer} />
      </div>
    </div>
  )
}
