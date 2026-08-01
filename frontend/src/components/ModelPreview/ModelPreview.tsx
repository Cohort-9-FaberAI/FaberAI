import styles from './ModelPreview.module.css'
import { useState, useEffect, useContext, useRef } from 'react'
import { Canvas } from '@react-three/fiber'
import { GizmoHelper, GizmoViewport, OrbitControls } from '@react-three/drei'

import {
  type AnalysisResult,
  type Centroid,
  type ManufacturabilityIssue,
} from '../../types/analysis'
import { ModelContext } from './ModelContext'
import { fetchAnalysis } from './api'
import { Model } from './Model'
import IssueMarker from './IssueMarker'
import { PCFShadowMap } from 'three'
import Toolbar from './Toolbar'
type ModelPreviewProps = {
  onIssueSelected?: (issue: ManufacturabilityIssue | null) => void
  height?: number | string
}

function toCentroid(centroid: Centroid): [number, number, number] {
  return Array.isArray(centroid) ? centroid : [centroid.x, centroid.y, centroid.z]
}

function ModelCanvas() {
  const context = useContext(ModelContext)

  return (
    <Canvas shadows={{ type: PCFShadowMap }} camera={{ position: [3, 3, 3], fov: 45 }}>
      <color
        attach="background"
        args={[window.matchMedia('(prefers-color-scheme: dark)').matches ? '#22252f' : '#adc5de']}
      />
      <ambientLight intensity={2.4} />
      <directionalLight position={[4, 6, 3]} intensity={5} castShadow />
      <directionalLight position={[-3, 1, -4]} intensity={0.5} castShadow />
      <Model />

      {context?.analysis.issues.map((issue) => {
        const centroid = toCentroid(issue.centroid)
        return (
          <IssueMarker
            key={centroid.join(':')}
            position={centroid}
            color="red"
            issue={issue}
            type="POINT"
          />
        )
      })}

      <OrbitControls />
      <GizmoHelper alignment="top-left" margin={[80, 80]}>
        <GizmoViewport />
      </GizmoHelper>
    </Canvas>
  )
}

export default function ModelPreview({ onIssueSelected, height = 400 }: ModelPreviewProps) {
  const [AnalysisResult, setAnalysisResult] = useState<AnalysisResult | null>(null)
  const [selectedIssue, setSelectedIssue] = useState<ManufacturabilityIssue | null>(null)
  useEffect(() => {
    fetchAnalysis().then((a) => setAnalysisResult(a))
  }, [])

  const containerRef = useRef<HTMLDivElement>(null)
  const [isFullScreen, setFullScreen] = useState<boolean>(false)
  //triggers onIssueSelected callback when the selected issue changes
  useEffect(() => {
    if (onIssueSelected) onIssueSelected(selectedIssue)
  }, [selectedIssue])

  if (!AnalysisResult) return null

  return (
    <div className={styles.wrapper} style={{ height }}>
      <div ref={containerRef} className={styles.canvasContainer}>
        <Toolbar
          onFullScreenPressed={() => {
            if (isFullScreen) document.exitFullscreen()
            else containerRef.current?.requestFullscreen()
            setFullScreen(!isFullScreen)
          }}
          isFullScreen={isFullScreen}
        />
        <ModelContext.Provider
          value={{ analysis: AnalysisResult, selectedIssueSetter: setSelectedIssue }}
        >
          <ModelCanvas />
        </ModelContext.Provider>
      </div>
    </div>
  )
}
