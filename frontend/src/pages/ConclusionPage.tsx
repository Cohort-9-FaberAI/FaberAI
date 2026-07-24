import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { motion, AnimatePresence } from 'framer-motion'
import AppShell from '../components/layout/AppShell'
import StepIndicator from '../components/layout/StepIndicator'
import RadialScore from '../components/conclusion/RadialScore'
import SeverityLegend from '../components/analysis/SeverityLegend'
import Spinner from '../components/common/Spinner'
import { useStore } from '../store'

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
  const analysisResult = useStore((s) => s.analysisResult)
  const [activeTab, setActiveTab] = useState<'reasons' | 'improvements'>('reasons')

  const issues = (analysisResult?.issues as Issue[]) ?? []
  const score =
    typeof analysisResult?.manufacturability_score === 'number'
      ? analysisResult.manufacturability_score
      : null

  const showBoth = process === null
  const moldingScore = score
  const printingScore = score

  if (!analysisResult) {
    return (
      <AppShell>
        <StepIndicator currentStep={4} />
        <Spinner label="Loading analysis results..." />
        <motion.button
          type="button"
          onClick={() => navigate('/home')}
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          style={{ marginTop: 16 }}
        >
          Back to Upload
        </motion.button>
      </AppShell>
    )
  }

  return (
    <AppShell>
      <StepIndicator currentStep={4} />

      <motion.h1 initial={{ opacity: 0, x: -10 }} animate={{ opacity: 1, x: 0 }}>
        Conclusion
      </motion.h1>

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
        <button type="button" className="wizard-nav-back" onClick={() => navigate('/analysis')}>
          Go Back
        </button>
        <button type="button" onClick={() => navigate('/download')}>
          Next
        </button>
      </div>
    </AppShell>
  )
}
