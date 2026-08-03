import { type ReactNode } from 'react'
import ModelPreview from '../ModelPreview/ModelPreview'
import type { AnalysisResult } from '../../types/analysis'

interface WorkflowLayoutProps {
  eyebrow?: string
  title: string
  description?: string
  analysis?: AnalysisResult | null
  previewFileUrl?: string | null
  previewBuffer?: ArrayBuffer | null
  previewFilename?: string | null
  viewerLabel?: string
  viewerMeta?: ReactNode
  children: ReactNode
}

export default function WorkflowLayout({
  eyebrow,
  title,
  description,
  analysis = null,
  previewFileUrl = null,
  previewBuffer,
  previewFilename = null,
  viewerLabel = 'Live inspection',
  viewerMeta,
  children,
}: WorkflowLayoutProps) {
  return (
    <div className="workflow-layout">
      <section className="workflow-panel">
        {eyebrow ? <p className="workflow-eyebrow">{eyebrow}</p> : null}
        <h1 className="page-title">{title}</h1>
        {description ? <p className="page-sub">{description}</p> : null}
        {children}
      </section>

      <aside className="viewer-panel" aria-label={viewerLabel}>
        <div className="viewer-panel-header">
          <div>
            <span>{viewerLabel}</span>
            <strong>{analysis?.filename ?? previewFilename ?? 'No completed report'}</strong>
          </div>
          {viewerMeta}
        </div>
        <div style={{ position: 'relative' }}>
          <ModelPreview
            analysis={analysis}
            previewFileUrl={previewFileUrl}
            previewBuffer={previewBuffer}
          />
        </div>
      </aside>
    </div>
  )
}
