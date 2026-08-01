import { useState, useEffect, type ReactNode } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
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
  const [fullscreenOpen, setFullscreenOpen] = useState(false)

  useEffect(() => {
    if (!fullscreenOpen) return
    const onKeyDown = (e: KeyboardEvent) => {
      if (e.key === 'Escape') setFullscreenOpen(false)
    }
    window.addEventListener('keydown', onKeyDown)
    return () => window.removeEventListener('keydown', onKeyDown)
  }, [fullscreenOpen])

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
          <button
            type="button"
            className="preview-expand-btn"
            title="Open 3D preview full screen"
            onClick={() => setFullscreenOpen(true)}
            aria-label="Zoom 3D model fullscreen"
          >
            <svg
              width="18"
              height="18"
              viewBox="0 0 24 24"
              fill="none"
              stroke="currentColor"
              strokeWidth="2"
              strokeLinecap="round"
              strokeLinejoin="round"
            >
              <circle cx="11" cy="11" r="8" />
              <line x1="21" y1="21" x2="16.65" y2="16.65" />
              <line x1="11" y1="8" x2="11" y2="14" />
              <line x1="8" y1="11" x2="14" y2="11" />
            </svg>
          </button>
          <ModelPreview
            analysis={analysis}
            previewFileUrl={previewFileUrl}
            previewBuffer={previewBuffer}
          />
        </div>
      </aside>

      <AnimatePresence>
        {fullscreenOpen && (
          <motion.div
            className="preview-fullscreen-overlay"
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            onClick={() => setFullscreenOpen(false)}
          >
            <motion.div
              className="preview-fullscreen-card"
              initial={{ scale: 0.95, opacity: 0 }}
              animate={{ scale: 1, opacity: 1 }}
              exit={{ scale: 0.95, opacity: 0 }}
              transition={{ type: 'spring', damping: 26, stiffness: 320 }}
              onClick={(e) => e.stopPropagation()}
            >
              <div className="preview-fullscreen-header">
                <div>
                  <span className="fullscreen-subtitle">{viewerLabel}</span>
                  <h2>{analysis?.filename ?? previewFilename ?? '3D CAD Geometry View'}</h2>
                </div>
                <div style={{ display: 'flex', alignItems: 'center', gap: '16px' }}>
                  {viewerMeta}
                  <button
                    type="button"
                    className="workspace-modal-close"
                    style={{ width: '38px', height: '38px', fontSize: '22px' }}
                    onClick={() => setFullscreenOpen(false)}
                    aria-label="Close fullscreen view"
                    title="Close fullscreen view (Esc)"
                  >
                    &times;
                  </button>
                </div>
              </div>
              <div className="preview-fullscreen-canvas">
                <ModelPreview
                  analysis={analysis}
                  previewFileUrl={previewFileUrl}
                  previewBuffer={previewBuffer}
                />
              </div>
            </motion.div>
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  )
}
