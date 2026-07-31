import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { motion, AnimatePresence } from 'framer-motion'
import AppShell from '../components/layout/AppShell'
import StepIndicator from '../components/layout/StepIndicator'
import ModelPreview from '../components/ModelPreview/ModelPreview'
import RadialScore from '../components/conclusion/RadialScore'
import SeverityLegend from '../components/analysis/SeverityLegend'
import Spinner from '../components/common/Spinner'
import { useStore } from '../store'
import { useTaskPolling } from '../lib/useTaskPolling'

interface Issue {
  severity: 'high' | 'medium' | 'low'
  message: string
  recommendation: string
}

const conclusionLegendItems = [
  { label: 'Severe', color: '#ef5350' },
  { label: 'Problematic', color: '#ffb74d' },
  { label: 'Minor', color: '#ffd54f' },
]

export default function ConclusionPage() {
  const navigate = useNavigate()
  const process = useStore((s) => s.process)
  const files = useStore((s) => s.files)
  const projects = useStore((s) => s.projects)
  const updateFile = useStore((s) => s.updateFile)
  const updateProjectFile = useStore((s) => s.updateProjectFile)
  const wizardSource = useStore((s) => s.source)
  const wizardProjectId = useStore((s) => s.projectId)
  const wizardFileId = useStore((s) => s.fileId)
  const analysisResult = useStore((s) => s.analysisResult)
  const setAnalysisResult = useStore((s) => s.setAnalysisResult)
  const [activeTab, setActiveTab] = useState<'reasons' | 'improvements'>('reasons')

  const projectFile =
    wizardSource === 'project' || wizardSource === 'view'
      ? projects.find((p) => p.id === wizardProjectId)?.files.find((f) => f.id === wizardFileId)
      : undefined
  const quickFile =
    wizardSource === 'quick'
      ? (files.find((f) => f.id === wizardFileId) ?? files[files.length - 1])
      : undefined

  const activeFile = projectFile ?? quickFile
  const alreadyDone = activeFile?.status === 'completed' && activeFile.analysisResult != null
  const taskId = alreadyDone ? null : (activeFile?.taskId ?? null)

  const displayResult = projectFile
    ? (projectFile.analysisResult ?? analysisResult)
    : (quickFile?.analysisResult ?? analysisResult)

  useTaskPolling(taskId, activeFile?.analysisId, (data) => {
    const status = typeof data?.status === 'string' ? data.status : null
    const result = data?.result as Record<string, unknown> | undefined
    if (result) {
      setAnalysisResult(result)
    }
    if (status === 'SUCCESS' && activeFile) {
      if (projectFile && wizardProjectId) {
        updateProjectFile(wizardProjectId, projectFile.id, {
          status: 'completed',
          analysisResult: result ?? projectFile.analysisResult,
        })
      } else {
        updateFile(activeFile.id, {
          status: 'completed',
          analysisResult: result ?? activeFile.analysisResult,
        })
      }
    }
    if ((status === 'FAILED' || status === 'FAILURE') && activeFile) {
      if (projectFile && wizardProjectId) {
        updateProjectFile(wizardProjectId, projectFile.id, { status: 'failed' })
      } else {
        updateFile(activeFile.id, { status: 'failed' })
      }
    }
  })

  const backToStart =
    wizardSource === 'project' && wizardProjectId ? `/projects/${wizardProjectId}` : '/home'
  const backLabel = wizardSource === 'project' ? 'Back to Project' : 'Back to Upload'

  const issues = (displayResult?.issues as Issue[]) ?? []
  const score =
    typeof displayResult?.manufacturability_score === 'number'
      ? displayResult.manufacturability_score
      : null

  const showBoth = process === null
  const moldingScore = score
  const printingScore = score

  const loading = taskId !== null && !displayResult
  const error = activeFile?.status === 'failed' ? 'Analysis failed. Please try again.' : null

  return (
    <AppShell>
      <StepIndicator currentStep={3} />

      <motion.h1 initial={{ opacity: 0, x: -10 }} animate={{ opacity: 1, x: 0 }}>
        Conclusion
      </motion.h1>

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

      {!loading && !error && !displayResult && (
        <motion.div
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          style={{ marginTop: 24, display: 'flex', flexDirection: 'column', gap: 16 }}
        >
          <p className="list-empty">No analysis result available.</p>
          <div>
            <button type="button" onClick={() => navigate(backToStart)}>
              {backLabel}
            </button>
          </div>
        </motion.div>
      )}

      {!loading && !error && displayResult && (
        <motion.div
          className="analysis-layout"
          initial={{ opacity: 0, y: 10 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.4 }}
        >
          <ModelPreview />

          <div className="analysis-right-panel">
            <SeverityLegend items={conclusionLegendItems} />

            {score !== null && (
              <motion.div
                className={`conclusion-scores${showBoth ? '' : ' single'}`}
                initial={{ opacity: 0, scale: 0.9 }}
                animate={{ opacity: 1, scale: 1 }}
                transition={{ type: 'spring', stiffness: 200, damping: 20 }}
              >
                {(showBoth || process === 'molding') && (
                  <RadialScore
                    percentage={moldingScore!}
                    label="Molding"
                    recommended={showBoth && moldingScore! > (printingScore ?? 0)}
                  />
                )}
                {(showBoth || process === 'printing') && (
                  <RadialScore
                    percentage={printingScore!}
                    label="Printing"
                    recommended={showBoth && (printingScore ?? 0) > moldingScore!}
                  />
                )}
              </motion.div>
            )}

            <div className="conclusion-tabs">
              <button
                type="button"
                className={`analysis-tab${activeTab === 'reasons' ? ' active' : ''}`}
                onClick={() => setActiveTab('reasons')}
              >
                Reasons
              </button>
              <button
                type="button"
                className={`analysis-tab${activeTab === 'improvements' ? ' active' : ''}`}
                onClick={() => setActiveTab('improvements')}
              >
                Improvements
              </button>
            </div>

            <div className="conclusion-items">
              <AnimatePresence mode="wait">
                {activeTab === 'reasons' ? (
                  <motion.div
                    key="reasons"
                    initial={{ opacity: 0, x: -10 }}
                    animate={{ opacity: 1, x: 0 }}
                    exit={{ opacity: 0, x: 10 }}
                    transition={{ duration: 0.2 }}
                  >
                    {issues.map((issue, i) => (
                      <motion.div
                        key={i}
                        className="conclusion-item"
                        style={{
                          borderLeftColor:
                            issue.severity === 'high'
                              ? '#ef5350'
                              : issue.severity === 'medium'
                                ? '#ffb74d'
                                : '#ffd54f',
                        }}
                        initial={{ opacity: 0, y: 8 }}
                        animate={{ opacity: 1, y: 0 }}
                        transition={{ delay: i * 0.05 }}
                      >
                        <p>{issue.message}</p>
                      </motion.div>
                    ))}
                  </motion.div>
                ) : (
                  <motion.div
                    key="improvements"
                    initial={{ opacity: 0, x: -10 }}
                    animate={{ opacity: 1, x: 0 }}
                    exit={{ opacity: 0, x: 10 }}
                    transition={{ duration: 0.2 }}
                  >
                    {issues.map((issue, i) => (
                      <motion.div
                        key={i}
                        className="conclusion-item"
                        style={{
                          borderLeftColor:
                            issue.severity === 'high'
                              ? '#ef5350'
                              : issue.severity === 'medium'
                                ? '#ffb74d'
                                : '#ffd54f',
                        }}
                        initial={{ opacity: 0, y: 8 }}
                        animate={{ opacity: 1, y: 0 }}
                        transition={{ delay: i * 0.05 }}
                      >
                        <p>{issue.recommendation}</p>
                      </motion.div>
                    ))}
                  </motion.div>
                )}
              </AnimatePresence>
            </div>

            <div className="wizard-nav">
              <button
                type="button"
                className="wizard-nav-back"
                onClick={() => navigate('/extra-info')}
              >
                Go Back
              </button>
              <button type="button" onClick={() => navigate('/download')}>
                Next
              </button>
            </div>
          </div>
        </motion.div>
      )}
    </AppShell>
  )
}
