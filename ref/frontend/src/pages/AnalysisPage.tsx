import { useState } from 'react'
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

export default function AnalysisPage() {
  const navigate = useNavigate()
  const files = useStore((s) => s.files)
  const updateFile = useStore((s) => s.updateFile)
  const analysisResult = useStore((s) => s.analysisResult)
  const setAnalysisResult = useStore((s) => s.setAnalysisResult)
  const [activeTab, setActiveTab] = useState<'molding' | 'printing'>('molding')

  const latestFile = files[files.length - 1]
  const taskId = latestFile?.taskId ?? null
  const isDevManual = taskId === 'dev-manual'

  useTaskPolling(isDevManual ? null : taskId, latestFile?.analysisId, (data) => {
    const status = typeof data?.status === 'string' ? data.status : null
    if (status === 'SUCCESS' && latestFile) {
      updateFile(latestFile.id, { status: 'completed' })
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
