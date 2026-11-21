import { useState } from 'react'
import WorkflowLayout from '../../layout/WorkflowLayout'
import { hasCompletedReport } from '../../../lib/analysisView'
import { useFileWorkspace } from '../../../hooks/useFileWorkspace'
import { downloadAnalysisReportPdf } from '../../../lib/api'
import ReportPdfPreview from '../../export/ReportPdfPreview'
import type { UploadedFile } from '../../../store'

interface ExportStepProps {
  activeFile: UploadedFile | null
}

export default function ExportStep({ activeFile }: ExportStepProps) {
  const { analysis, analysisResult, settings, previewProps } = useFileWorkspace(activeFile)
  const { process, printingProcess, material, tolerance, surfaceFinish } = settings

  const [comparison, setComparison] = useState(false)
  const [downloading, setDownloading] = useState(false)
  const [downloadError, setDownloadError] = useState<string | null>(null)

  const showComparison = process === null
  const canDownload = hasCompletedReport(analysis)

  const cleanAnalysis = analysis ? { ...analysis, issues: [] } : null

  async function handleDownload() {
    if (!analysisResult || !canDownload) {
      setDownloadError('A completed DFM report is required before downloading.')
      return
    }

    setDownloading(true)
    setDownloadError(null)

    try {
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
      {...previewProps}
      viewerOverride={
        <ReportPdfPreview
          analysis={analysisResult}
          comparison={comparison}
          process={process}
          printingProcess={printingProcess}
          material={material}
          tolerance={tolerance}
          surfaceFinish={surfaceFinish}
        />
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
