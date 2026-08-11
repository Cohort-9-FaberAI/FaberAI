import { useState } from 'react'
import WorkflowLayout from '../../layout/WorkflowLayout'
import { useStore } from '../../../store'
import {
  asAnalysisResult,
  getAnalysisScore,
  getScoreColor,
  hasCompletedReport,
} from '../../../lib/analysisView'
import { downloadAnalysisReportPdf } from '../../../lib/api'
import type { UploadedFile } from '../../../store'

interface ExportStepProps {
  activeFile: UploadedFile | null
}

export default function ExportStep({ activeFile }: ExportStepProps) {
  const process = useStore((s) => s.process)
  const printingProcess = useStore((s) => s.printingProcess)
  const material = useStore((s) => s.material)
  const tolerance = useStore((s) => s.tolerance)
  const surfaceFinish = useStore((s) => s.surfaceFinish)

  const activeId = activeFile?.id ?? ''
  const analysisResult = useStore((s) => s.analysisResults[activeId] ?? null)
  const fileBuffer = useStore((s) => s.fileBuffers[activeId] ?? null)
  const [comparison, setComparison] = useState(false)
  const [downloading, setDownloading] = useState(false)
  const [downloadError, setDownloadError] = useState<string | null>(null)

  const showComparison = process === null
  const analysis = asAnalysisResult(analysisResult)
  const score = getAnalysisScore(analysis)
  const canDownload = hasCompletedReport(analysis)

  const activeFileIsStl =
    activeFile?.sourceFormat === 'stl' ||
    (!activeFile?.sourceFormat && activeFile?.name.toLowerCase().endsWith('.stl'))
  const livePreviewUrl = activeFileIsStl ? (activeFile?.fileUrl ?? null) : null
  const livePreviewFilename = activeFile?.name ?? null
  const cleanAnalysis = analysis ? { ...analysis, issues: [] } : null

  async function handleDownload() {
    if (!analysisResult || !canDownload) {
      setDownloadError('A completed DFM report is required before downloading.')
      return
    }

    setDownloading(true)
    setDownloadError(null)

    try {
      // Rastreador para provar se as variáveis estão chegando vivas ou mortas aqui
      console.log('Rastreio do ExportStep ->', { process, material, tolerance })

      const { blob, filename } = await downloadAnalysisReportPdf(
        analysisResult,
        comparison,
        process,
        material,
        tolerance,
        printingProcess,
        surfaceFinish,
      )
      const url = URL.createObjectURL(blob)
      const link = document.createElement('a')
      link.href = url
      link.download = filename
      document.body.appendChild(link)
      link.click()
      link.remove()
      URL.revokeObjectURL(url)
    } catch (err) {
      setDownloadError(err instanceof Error ? err.message : 'PDF download failed.')
    } finally {
      setDownloading(false)
    }
  }

  return (
    <WorkflowLayout
      eyebrow="Step 04 &bull; Export"
      title="Download DFM report"
      description="Package the completed inspection results and design recommendations for supplier review."
      analysis={cleanAnalysis}
      previewFileUrl={livePreviewUrl}
      previewBuffer={fileBuffer}
      previewSourceFormat={activeFile?.sourceFormat ?? null}
      previewFilename={livePreviewFilename}
      viewerMeta={
        score !== null ? (
          <span className="viewer-score">
            <span style={{ color: getScoreColor(score) }}>{Math.round(score)}</span>/100
          </span>
        ) : null
      }
    >
      {showComparison && (
        <section className="download-options" aria-label="Report export options">
          <div className="download-options-header">
            <h2>Export options</h2>
            <p>Choose the contents to include in the supplier-ready PDF document.</p>
          </div>

          <div className="download-setting-row">
            <div>
              <span className="download-setting-label">Process comparison</span>
              <p>Include molding versus printing analytical evidence in the exported report.</p>
            </div>
            <div className="download-toggle" role="group" aria-label="Include process comparison">
              <button
                type="button"
                className={`process-toggle-btn${comparison ? ' active' : ''}`}
                onClick={() => setComparison(true)}
              >
                Yes
              </button>
              <button
                type="button"
                className={`process-toggle-btn${!comparison ? ' active' : ''}`}
                onClick={() => setComparison(false)}
              >
                No
              </button>
            </div>
          </div>
        </section>
      )}

      <button
        type="button"
        className="download-pdf-btn"
        disabled={downloading || !canDownload}
        onClick={handleDownload}
        title={!canDownload ? 'Complete an analysis before downloading.' : undefined}
      >
        {downloading ? 'Preparing PDF...' : 'Download PDF'}
      </button>
      {downloadError && <p className="download-error">{downloadError}</p>}
    </WorkflowLayout>
  )
}
