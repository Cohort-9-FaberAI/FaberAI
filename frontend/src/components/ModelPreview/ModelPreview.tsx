import styles from './ModelPreview.module.css'
import { useState, useEffect, useContext } from 'react'
import { Canvas } from '@react-three/fiber'
import { OrbitControls } from '@react-three/drei'

import { type AnalysisResult } from '../../types/analysis'
import { ModelContext } from './ModelContext'
import { fetchAnalysis } from './api'
import { Model } from './Model'
import IssueMarker from './IssueMarker'

function ModelCanvas() {
  const Analysis = useContext(ModelContext)

  return (
    <Canvas shadows camera={{ position: [3, 3, 3], fov: 45 }}>
      <ambientLight intensity={2.4} />
      <directionalLight position={[4, 6, 3]} intensity={5} castShadow />
      <directionalLight position={[-3, 1, -4]} intensity={0.5} castShadow />
      <Model />

      {Analysis?.issues.map((issue) => (
        <IssueMarker key={issue.centroid.join(':')} position={issue.centroid} color="red" />
      ))}

      <OrbitControls />
    </Canvas>
  )
}

export default function ModelPreview() {
  const [AnalysisResult, setAnalysisResult] = useState<AnalysisResult | null>(null)

  useEffect(() => {
    fetchAnalysis().then((a) => setAnalysisResult(a))
  }, [])

  if (!AnalysisResult) return null

  return (
    <div>
      <div className={styles.CanvasContainer}>
        <ModelContext.Provider value={AnalysisResult}>
          <ModelCanvas />
        </ModelContext.Provider>
      </div>
    </div>
  )
}
