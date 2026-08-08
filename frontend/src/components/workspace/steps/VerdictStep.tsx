import { useState } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import WorkflowLayout from '../../layout/WorkflowLayout'
import RadialScore from '../../conclusion/RadialScore'
import SeverityLegend from '../../analysis/SeverityLegend'
import { useStore } from '../../../store'
import {
  asAnalysisResult,
  getAnalysisScore,
  getDisplayIssues,
  getMoldingScore,
  getPrintingScore,
  getScoreColor,
  hasCompletedReport,
} from '../../../lib/analysisView'
import type { UploadedFile } from '../../../store'

interface VerdictStepProps {
  activeFile: UploadedFile | null
}

const conclusionLegendItems = [
  { label: 'Severe', color: '#ef5350' },
  { label: 'Problematic', color: '#ffb74d' },
  { label: 'Minor', color: '#ffd54f' },
]

export default function VerdictStep({ activeFile }: VerdictStepProps) {
  const process = useStore((s) => s.process)
  const activeId = activeFile?.id ?? ''
  const analysisResult = useStore((s) => s.analysisResults[activeId] ?? null)
  const fileBuffer = useStore((s) => s.fileBuffers[activeId] ?? null)
  const [activeTab, setActiveTab] = useState<'reasons' | 'improvements'>('reasons')
  const analysis = asAnalysisResult(analysisResult)

  const activeFileIsStl =
    activeFile?.sourceFormat === 'stl' ||
    (!activeFile?.sourceFormat && activeFile?.name.toLowerCase().endsWith('.stl'))
  const livePreviewUrl = activeFileIsStl ? (activeFile?.fileUrl ?? null) : null
  const livePreviewFilename = activeFile?.name ?? null

  const issues = getDisplayIssues(analysis)
  const score = getAnalysisScore(analysis)
  const cleanAnalysis = analysis ? { ...analysis, issues: [] } : null

  const reasonItems =
    issues.length > 0
      ? issues.map((issue) => issue.message)
      : [
          analysis?.summary ??
            'The completed DFM report did not flag severe manufacturability blockers for the selected process.',
          score !== null
            ? `The headline manufacturability score is ${Math.round(score)}/100.`
            : 'The report completed successfully and is ready for review.',
        ]
  const improvementItems =
    issues.length > 0
      ? issues.map((issue) => issue.recommendation)
      : [
          'Keep nominal wall thickness, draft, and unsupported overhangs within the process thresholds before release.',
          'Use Ask Faber AI for a report-grounded explanation of specific rule thresholds or process tradeoffs.',
        ]

  const showBoth = process === null
  const moldingScore = getMoldingScore(analysis) ?? score
  const printingScore = getPrintingScore(analysis) ?? score

  if (!hasCompletedReport(analysis)) {
    return (
      <div className="analysis-status">
        A completed DFM report is required before the verdict and score breakdown can be displayed.
        Please check back when inspection finishes.
      </div>
    )
  }

  return (
    <WorkflowLayout
      eyebrow="Step 03 &bull; Verdict"
      title="Manufacturability Conclusion"
      description="Compare process favorability and review prioritized design improvements."
      analysis={cleanAnalysis}
      previewFileUrl={livePreviewUrl}
      previewBuffer={fileBuffer}
      previewFilename={livePreviewFilename}
      viewerMeta={
        score !== null ? (
          <span className="viewer-score">
            <span style={{ color: getScoreColor(score) }}>{Math.round(score)}</span>/100
          </span>
        ) : null
      }
    >
      <section className="conclusion-score-panel" aria-label="Manufacturability verdict">
        <div className="conclusion-score-header">
          <div>
            <h2>Manufacturability verdict</h2>
          </div>
          {score !== null && (
            <div className="conclusion-score-summary">
              <strong style={{ color: getScoreColor(score) }}>{Math.round(score)}</strong>
              <span>/100 overall</span>
            </div>
          )}
        </div>

        <div className="conclusion-score-legend">
          <SeverityLegend items={conclusionLegendItems} />
        </div>

        {score !== null && (
          <motion.div
            className={`conclusion-scores${showBoth ? '' : ' single'}`}
            initial={{ opacity: 0, y: 6 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.18 }}
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
      </section>

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
          <motion.div
            key={activeTab}
            initial={{ opacity: 0, x: -6 }}
            animate={{ opacity: 1, x: 0 }}
            exit={{ opacity: 0, x: 6 }}
            transition={{ duration: 0.15 }}
          >
            {(activeTab === 'reasons' ? reasonItems : improvementItems).map((item, i) => (
              <motion.div
                key={`${activeTab}-${i}`}
                className="conclusion-item"
                initial={{ opacity: 0, y: 4 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ delay: i * 0.03 }}
              >
                <span className="conclusion-item-index">{String(i + 1).padStart(2, '0')}</span>
                <p>{item}</p>
              </motion.div>
            ))}
          </motion.div>
        </AnimatePresence>
      </div>
    </WorkflowLayout>
  )
}
