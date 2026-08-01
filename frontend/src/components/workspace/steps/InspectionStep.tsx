import { useState } from 'react'
import { motion } from 'framer-motion'
import WorkflowLayout from '../../layout/WorkflowLayout'
import Spinner from '../../common/Spinner'
import IssueAccordion from '../../analysis/IssueAccordion'
import SeverityLegend from '../../analysis/SeverityLegend'
import { useStore } from '../../../store'
import {
  asAnalysisResult,
  getAnalysisScore,
  getDisplayIssues,
  hasCompletedReport,
} from '../../../lib/analysisView'
import type { UploadedFile } from '../../../store'

interface InspectionStepProps {
  activeFile: UploadedFile | null
}

export default function InspectionStep({ activeFile }: InspectionStepProps) {
  const analysisResult = useStore((s) => s.analysisResult)
  const [activeTab, setActiveTab] = useState<'molding' | 'printing'>('molding')

  const analysis = asAnalysisResult(analysisResult)
  const taskId = activeFile?.taskId ?? null
  const isDevManual = taskId === 'dev-manual'
  const activeFileIsStl =
    activeFile?.sourceFormat === 'stl' ||
    (!activeFile?.sourceFormat && activeFile?.name.toLowerCase().endsWith('.stl'))
  const livePreviewUrl = activeFileIsStl ? (activeFile?.fileUrl ?? null) : null
  const livePreviewFilename = activeFile?.name ?? null

  const issues = getDisplayIssues(analysis)
  const score = getAnalysisScore(analysis)
  const loading =
    !isDevManual && activeFile?.status === 'processing' && taskId !== null && !analysis
  const error =
    activeFile?.status === 'failed' && !isDevManual
      ? 'Analysis failed. Please try uploading or processing the file again.'
      : null
  const noAnalysisStarted = !activeFile && !analysis
  const canContinue = hasCompletedReport(analysis)

  const cons = issues.filter((i) => i.severity === 'high' || i.severity === 'blocker')
  const neutral = issues.filter((i) => i.severity === 'medium' || i.severity === 'major')
  const minor = issues.filter((i) => i.severity === 'low' || i.severity === 'minor')

  return (
    <div>
      {loading && (
        <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }} style={{ padding: '40px 0' }}>
          <Spinner label="Analyzing your CAD geometry..." />
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

      {noAnalysisStarted && (
        <motion.div className="analysis-status" initial={{ opacity: 0 }} animate={{ opacity: 1 }}>
          Select or upload a CAD file to view its DFM inspection report.
        </motion.div>
      )}

      {!loading && !error && (
        <WorkflowLayout
          eyebrow="Step 02 &bull; Inspection"
          title="DFM geometry analysis"
          description={
            canContinue
              ? 'Review automated rule checks and geometry issues directly on the 3D model.'
              : isDevManual
                ? 'The DEV loader is only a local model preview. Use the drop zone to run DFM analysis.'
                : 'The backend report will appear here as soon as processing completes.'
          }
          analysis={analysis}
          previewFileUrl={livePreviewUrl}
          previewFilename={livePreviewFilename}
          viewerMeta={
            canContinue && score !== null ? (
              <span className="viewer-score">{Math.round(score)}/100</span>
            ) : null
          }
        >
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

          <motion.div
            className="analysis-right-panel"
            initial={{ opacity: 0, y: 8 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.25 }}
          >
            <SeverityLegend />
            {canContinue && (
              <div className="analysis-report-summary">
                <div>
                  <span>Score</span>
                  <strong>{score !== null ? `${Math.round(score)}/100` : 'Ready'}</strong>
                </div>
                <p>{analysis?.summary ?? 'DFM report completed successfully.'}</p>
              </div>
            )}
            <div className="analysis-findings-scroll" aria-label="Analysis findings">
              <IssueAccordion
                title="Pros"
                count={minor.length}
                color="var(--severity-pro)"
                items={minor}
                emptyLabel={
                  analysis
                    ? 'No minor positive notes are available for this report yet.'
                    : 'Findings will appear once analysis is complete.'
                }
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
        </WorkflowLayout>
      )}
    </div>
  )
}
