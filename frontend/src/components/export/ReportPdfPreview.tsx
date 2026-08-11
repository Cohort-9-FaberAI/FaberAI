import { useEffect, useState } from 'react'
import { downloadAnalysisReportPdf } from '../../lib/api'
import styles from './ReportPdfPreview.module.css'

interface ReportPdfPreviewProps {
  analysis: Record<string, unknown> | null
  comparison: boolean
  process?: string | null
  printingProcess?: string | null
  material?: string | null
  tolerance?: string | null
  surfaceFinish?: string | null
  height?: number
}

export default function ReportPdfPreview({
  analysis,
  comparison,
  process,
  printingProcess,
  material,
  tolerance,
  surfaceFinish,
  height = 580,
}: ReportPdfPreviewProps) {
  const [pdfUrl, setPdfUrl] = useState<string | null>(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    let cancelled = false
    let objectUrl: string | null = null

    async function generate() {
      if (!analysis || analysis.status !== 'completed') {
        setPdfUrl(null)
        setError(null)
        setLoading(false)
        return
      }

      setLoading(true)
      setError(null)

      try {
        const { blob } = await downloadAnalysisReportPdf(
          analysis,
          comparison,
          process,
          material,
          tolerance,
          printingProcess,
          surfaceFinish,
          true,
        )
        if (cancelled) return

        objectUrl = URL.createObjectURL(blob)
        setPdfUrl((prev) => {
          if (prev) URL.revokeObjectURL(prev)
          return objectUrl
        })
      } catch (err) {
        if (!cancelled)
          setError(err instanceof Error ? err.message : 'Failed to render PDF preview.')
      } finally {
        if (!cancelled) setLoading(false)
      }
    }

    generate()

    return () => {
      cancelled = true
      if (objectUrl) URL.revokeObjectURL(objectUrl)
    }
  }, [analysis, comparison, process, material, tolerance, printingProcess, surfaceFinish])

  const ready = !!pdfUrl && !error

  return (
    <div className={styles.preview} style={{ height }}>
      {!analysis || analysis.status !== 'completed' ? (
        <div className={styles.placeholder}>
          A completed DFM report is required to preview the PDF.
        </div>
      ) : error ? (
        <div className={styles.error}>{error}</div>
      ) : ready ? (
        <>
          <iframe className={styles.iframe} src={pdfUrl ?? undefined} title="DFM report preview" />
          {loading && <div className={styles.busy}>Updating preview&hellip;</div>}
        </>
      ) : (
        <div className={styles.loading}>Generating PDF preview&hellip;</div>
      )}
    </div>
  )
}
