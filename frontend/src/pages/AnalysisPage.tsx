import { useEffect, useRef, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { motion } from 'framer-motion'
import AppShell from '../components/layout/AppShell'
import StepIndicator from '../components/layout/StepIndicator'
import ModelPreview from '../components/ModelPreview/ModelPreview'
import SeverityLegend from '../components/analysis/SeverityLegend'
import IssueAccordion from '../components/analysis/IssueAccordion'
import Spinner from '../components/common/Spinner'
import { useStore } from '../store'
import { useTaskPolling } from '../lib/useTaskPolling'

interface Issue {
  severity: 'high' | 'medium' | 'low'
  message: string
  recommendation: string
}

const MOCK_FALLBACK: Record<string, unknown> = {
  analysis_id: 'mock-local-fallback',
  filename: 'local_preview.stl',
  status: 'completed',
  manufacturability_score: 72,
  issues: [
    {
      severity: 'high',
      message: 'Wall thickness of 0.8mm is below the minimum of 1.5mm for CNC machining.',
      recommendation: 'Increase wall thickness to at least 1.5mm.',
    },
    {
      severity: 'medium',
      message:
        'Pocket depth-to-width ratio of 5:1 exceeds the recommended 4:1 for standard tooling.',
      recommendation: 'Reduce pocket depth or widen the pocket opening.',
    },
  ],
}

export default function AnalysisPage() {
  const navigate = useNavigate()
  const files = useStore((s) => s.files)
  const analysisResult = useStore((s) => s.analysisResult)
  const setAnalysisResult = useStore((s) => s.setAnalysisResult)
  const [activeTab, setActiveTab] = useState<'molding' | 'printing'>('molding')
  const fallbackTimerRef = useRef<ReturnType<typeof setTimeout> | null>(null)

  const latestFile = files[files.length - 1]
  const taskId = latestFile?.taskId ?? null
  const isDevManual = taskId === 'dev-manual'

  useEffect(() => {
    if (isDevManual) {
      setAnalysisResult(MOCK_FALLBACK)
      return
    }
    fallbackTimerRef.current = setTimeout(() => {
      const current = useStore.getState().analysisResult
      if (!current) {
        useStore.getState().setAnalysisResult(MOCK_FALLBACK)
      }
    }, 8000)
    return () => {
      if (fallbackTimerRef.current) clearTimeout(fallbackTimerRef.current)
    }
  }, []) // eslint-disable-line react-hooks/exhaustive-deps

  useTaskPolling(isDevManual ? null : taskId, (data) => {
    if (fallbackTimerRef.current) {
      clearTimeout(fallbackTimerRef.current)
      fallbackTimerRef.current = null
    }
    const result = data?.result as Record<string, unknown> | undefined
    if (result) {
      setAnalysisResult(result)
    }
  })

  const issues = (analysisResult?.issues as Issue[]) ?? []
  const loading = !isDevManual && taskId !== null && !analysisResult
  const error =
    latestFile?.status === 'failed' && !isDevManual ? 'Analysis failed. Please try again.' : null

  const cons = issues.filter((i) => i.severity === 'high')
  const neutral = issues.filter((i) => i.severity === 'medium')

  return (
    <AppShell>
      <StepIndicator currentStep={3} />

      <div className="analysis-tabs">
        <button
          type="button"
          className={`analysis-tab${activeTab === 'molding' ? ' active' : ''}`}
          onClick={() => setActiveTab('molding')}
        >
          Molding
        </button>
        <button
          type="button"
          className={`analysis-tab${activeTab === 'printing' ? ' active' : ''}`}
          onClick={() => setActiveTab('printing')}
        >
          Printing
        </button>
      </div>

      {loading && (
        <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }}>
          <Spinner label="Analyzing your CAD file..." />
        </motion.div>
      )}

      {error && (
        <motion.p
          className="analysis-status error"
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
        >
          {error}
        </motion.p>
      )}

      {!loading && !error && (
        <motion.div
          className="analysis-layout"
          initial={{ opacity: 0, y: 10 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.4 }}
        >
          <ModelPreview />
          <div className="analysis-right-panel">
            <SeverityLegend />
            <IssueAccordion
              title="Pros"
              count={0}
              color="var(--severity-pro)"
              items={[]}
              emptyLabel="Positive findings will appear once analysis is complete."
            />
            <IssueAccordion
              title="Neutral"
              count={neutral.length}
              color="var(--severity-medium)"
              items={neutral}
            />
            <IssueAccordion
              title="Cons"
              count={cons.length}
              color="var(--severity-high)"
              items={cons}
            />
          </div>
        </motion.div>
      )}

      {analysisResult && (
        <motion.button
          className="next-btn"
          type="button"
          onClick={() => navigate('/conclusion')}
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          transition={{ delay: 0.2 }}
        >
          Next
        </motion.button>
      )}
    </AppShell>
  )
}
