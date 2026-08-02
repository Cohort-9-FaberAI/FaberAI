import styles from './ModelPreview.module.css'
import { useState, useEffect, useContext } from 'react'
import { Canvas } from '@react-three/fiber'
import { OrbitControls } from '@react-three/drei'

import { type AnalysisResult, type ManufacturabilityIssue } from '../../types/analysis'
import { ModelContext } from './ModelContext'
import { fetchAnalysis } from './api'
import { Model } from './Model'
import IssueMarker from './IssueMarker'
import { PCFShadowMap } from 'three'
type ModelPreviewProps = {
  onIssueSelected?: (issue: ManufacturabilityIssue | null) => void
}

function ModelCanvas() {
  const context = useContext(ModelContext)

  return (
    <Canvas shadows={{ type: PCFShadowMap }} camera={{ position: [3, 3, 3], fov: 45 }}>
      <ambientLight intensity={2.4} />
      <directionalLight position={[4, 6, 3]} intensity={5} castShadow />
      <directionalLight position={[-3, 1, -4]} intensity={0.5} castShadow />
      <Model />

      {context?.analysis.issues.map((issue) => {
        const { x, y, z } = issue.centroid
        return (
          <IssueMarker
            key={`${x}:${y}:${z}`}
            position={[x, y, z]}
            color="red"
            issue={issue}
            type="POINT"
          />
        )
      })}

      <OrbitControls />
    </Canvas>
  )
}

export default function ModelPreview({ onIssueSelected }: ModelPreviewProps) {
  const [AnalysisResult, setAnalysisResult] = useState<AnalysisResult | null>(null)
  const [selectedIssue, setSelectedIssue] = useState<ManufacturabilityIssue | null>(null)
  useEffect(() => {
    fetchAnalysis().then((a) => setAnalysisResult(a))
  }, [])

  //triggers onIssueSelected callback when the selected issue changes
  useEffect(() => {
    if (onIssueSelected) onIssueSelected(selectedIssue)
  }, [selectedIssue])

  if (!AnalysisResult) return null

  return (
    <div>
      <div className={styles.CanvasContainer}>
        <ModelContext.Provider
          value={{ analysis: AnalysisResult, selectedIssueSetter: setSelectedIssue }}
        >
          <ModelCanvas />
        </ModelContext.Provider>
      </div>
    </div>
  )
}
