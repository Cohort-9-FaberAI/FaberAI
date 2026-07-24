import { Canvas } from '@react-three/fiber'
import { OrbitControls } from '@react-three/drei'
import { STLLoader } from 'three/addons/loaders/STLLoader.js'
import { useStore } from '../../store'
import styles from './ModelPreview.module.css'

function Model({ buffer }: { buffer: ArrayBuffer }) {
  const loader = new STLLoader()
  return (
    <mesh geometry={loader.parse(buffer)} castShadow receiveShadow>
      <meshStandardMaterial color="#64b5f6" roughness={0.4} metalness={0.6} />
    </mesh>
  )
}

function ModelCanvas({ buffer }: { buffer: ArrayBuffer }) {
  return (
    <Canvas shadows camera={{ position: [3, 3, 3], fov: 45 }}>
      <ambientLight intensity={1.5} />
      <directionalLight position={[4, 6, 3]} intensity={3} castShadow />
      <directionalLight position={[-3, 1, -4]} intensity={0.3} castShadow />
      {buffer.byteLength > 0 && <Model buffer={buffer} />}
      <OrbitControls />
    </Canvas>
  )
}

export default function ModelPreview() {
  const buffer = useStore((s) => s.currentFileBuffer)

  return (
    <div className={styles.wrapper}>
      {buffer && buffer.byteLength > 0 ? (
        <div className={styles.canvasContainer}>
          <ModelCanvas buffer={buffer} />
        </div>
      ) : (
        <div className={styles.placeholder}>
          <span>Upload a CAD file to preview</span>
        </div>
      )}
    </div>
  )
}
