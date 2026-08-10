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
  getMarkerIssuesForProcess,
  getMoldingScore,
  getPrintingScore,
  getProcessIssues,
  getScoreColor,
  hasCompletedReport,
} from '../../../lib/analysisView'
import type { UploadedFile } from '../../../store'

interface InspectionStepProps {
  activeFile: UploadedFile | null
}

export default function InspectionStep({ activeFile }: InspectionStepProps) {
  const activeId = activeFile?.id ?? ''
  const analysisResult = useStore((s) => s.analysisResults[activeId] ?? null)
  const fileBuffer = useStore((s) => s.fileBuffers[activeId] ?? null)
  const fileProcess = useStore((s) => (activeId ? (s.processByFile[activeId] ?? null) : null))
  const [activeTab, setActiveTab] = useState<'molding' | 'printing'>('molding')

  const analysis = asAnalysisResult(analysisResult)
  const taskId = activeFile?.taskId ?? null
  const isDevManual = taskId === 'dev-manual'
  const activeFileIsStl =
    activeFile?.sourceFormat === 'stl' ||
    (!activeFile?.sourceFormat && activeFile?.name.toLowerCase().endsWith('.stl'))
  const livePreviewUrl = activeFileIsStl ? (activeFile?.fileUrl ?? null) : null
  const livePreviewFilename = activeFile?.name ?? null

  // When a specific process was chosen in Setup, that process is the only
  // one being analyzed, so the Molding/Printing toggle is not applicable.
  const lockedProcess = fileProcess === 'molding' || fileProcess === 'printing' ? fileProcess : null
  const effectiveTab = lockedProcess ?? activeTab

  const overallScore = getAnalysisScore(analysis)
  const score =
    effectiveTab === 'molding'
      ? (getMoldingScore(analysis) ?? overallScore)
      : (getPrintingScore(analysis) ?? overallScore)
  const issues =
    effectiveTab === 'molding'
      ? getProcessIssues(analysis, 'injection_molding')
      : getProcessIssues(analysis, 'printing')

  // The 3D viewer renders markers from analysis.issues, so scope those to the
  // tab currently being inspected so markers match the listed findings.
  const viewerAnalysis = analysis
    ? {
        ...analysis,
        issues: getMarkerIssuesForProcess(
          analysis,
          effectiveTab === 'molding' ? 'injection_molding' : 'printing',
        ),
      }
    : null

  const loading = !isDevManual && activeFile?.status === 'processing' && !analysis
  const error =
    activeFile?.status === 'failed' && !isDevManual
      ? activeFile.errorMessage ||
        'Analysis failed. Please try uploading or processing the file again.'
      : null
  const noAnalysisStarted = !activeFile && !analysis
  const canContinue = hasCompletedReport(analysis)

  const severe = issues.filter((i) => i.severity === 'high' || i.severity === 'blocker')
  const problematic = issues.filter((i) => i.severity === 'medium' || i.severity === 'major')
  const minor = issues.filter((i) => i.severity === 'low' || i.severity === 'minor')

  return (
    <div>
      {loading && (
        <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }} style={{ padding: '40px 0' }}>
          <Spinner label="Analyzing your CAD geometry..." />
        </motion.div>
      )}

      {error && (
        <motion.div
          className="analysis-status error-card"
          initial={{ opacity: 0, y: -6 }}
          animate={{ opacity: 1, y: 0 }}
          style={{
            padding: '16px 20px',
            borderRadius: '12px',
            background: 'rgba(232, 93, 93, 0.15)',
            border: '1px solid rgba(232, 93, 93, 0.45)',
            color: '#ff6b6b',
            fontSize: '14px',
            fontWeight: 600,
            display: 'flex',
            alignItems: 'center',
            gap: '12px',
            marginBottom: '24px',
            boxShadow: '0 4px 16px rgba(232, 93, 93, 0.15)',
          }}
        >
          <span style={{ fontSize: '20px', flexShrink: 0 }}>⚠️</span>
          <div style={{ display: 'flex', flexDirection: 'column', gap: '4px' }}>
            <strong style={{ fontSize: '15px', color: '#fff' }}>DFM Inspection Error</strong>
            <span>{error}</span>
          </div>
        </motion.div>
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
          analysis={viewerAnalysis}
          previewFileUrl={livePreviewUrl}
          previewBuffer={fileBuffer}
          previewSourceFormat={activeFile?.sourceFormat ?? null}
          previewFilename={livePreviewFilename}
          viewerMeta={
            canContinue && score !== null ? (
              <span className="viewer-score">
                <span style={{ color: getScoreColor(score) }}>{Math.round(score)}</span>/100
              </span>
            ) : null
          }
        >
          <div className="analysis-tabs">
            <button
              type="button"
              className={`analysis-tab${effectiveTab === 'molding' ? ' active' : ''}`}
              onClick={() => setActiveTab('molding')}
              style={lockedProcess ? { display: 'none' } : undefined}
            >
              Molding
            </button>
            <button
              type="button"
              className={`analysis-tab${effectiveTab === 'printing' ? ' active' : ''}`}
              onClick={() => setActiveTab('printing')}
              style={lockedProcess ? { display: 'none' } : undefined}
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
                  <strong>
                    {score !== null ? (
                      <>
                        <span style={{ color: getScoreColor(score) }}>{Math.round(score)}</span>/100
                      </>
                    ) : (
                      'Ready'
                    )}
                  </strong>
                </div>
                <p>{analysis?.summary ?? 'DFM report completed successfully.'}</p>
              </div>
            )}
            <div className="analysis-findings-scroll" aria-label="Analysis findings">
              <IssueAccordion
                title="Minor"
                count={minor.length}
                color="var(--severity-low)"
                items={minor}
                emptyLabel={
                  analysis
                    ? 'No minor findings are available for this report yet.'
                    : 'Findings will appear once analysis is complete.'
                }
              />
              <IssueAccordion
                title="Problematic"
                count={problematic.length}
                color="var(--severity-medium)"
                items={problematic}
              />
              <IssueAccordion
                title="Severe"
                count={severe.length}
                color="var(--severity-high)"
                items={severe}
              />
            </div>
          </motion.div>
        </WorkflowLayout>
      )}
    </div>
  )
}
