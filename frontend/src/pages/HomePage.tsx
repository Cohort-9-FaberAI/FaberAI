import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { motion, AnimatePresence } from 'framer-motion'
import UploadDropzone from '../components/home/UploadDropzone'
import FileCard from '../components/home/FileCard'
import WizardNav from '../components/layout/WizardNav'
import { useStore } from '../store'
import { useTaskPolling } from '../lib/useTaskPolling'

function FilePoller({
  file,
}: {
  file: { id: string; taskId: string | null; analysisId: string | null; status: string }
}) {
  const updateFile = useStore((s) => s.updateFile)
  const setAnalysisResult = useStore((s) => s.setAnalysisResult)
  const syncProjectFile = useStore((s) => s.syncProjectFile)

  useTaskPolling(
    file.status === 'processing' && file.taskId ? file.taskId : null,
    file.analysisId,
    (data) => {
      const status = typeof data?.status === 'string' ? data.status : null
      const result = data?.result as Record<string, unknown> | undefined
      if (status === 'SUCCESS') {
        updateFile(file.id, { status: 'completed', analysisResult: result ?? null })
        if (result) {
          setAnalysisResult(file.id, result)
        }
        syncProjectFile(file.id)
      }
      if (status === 'FAILED' || status === 'FAILURE') {
        const errorMsg =
          typeof data?.error === 'string'
            ? data.error
            : typeof data?.message === 'string'
              ? data.message
              : 'DFM inspection failed during background processing.'
        updateFile(file.id, { status: 'failed', errorMessage: errorMsg })
        syncProjectFile(file.id)
      }
    },
    () => {
      updateFile(file.id, {
        status: 'failed',
        errorMessage: 'Network timeout or server connection error while checking task status.',
      })
      syncProjectFile(file.id)
    },
  )
  return null
}

export default function HomePage() {
  const navigate = useNavigate()
  const files = useStore((s) => s.files)
  const closeTab = useStore((s) => s.closeTab)
  const [projectPromptDismissed, setProjectPromptDismissed] = useState(false)

  const sessionFiles = files.filter((f) => f.taskId !== 'dev-manual' && !f.projectName)
  const hasProcessing = files.some(
    (f) => f.taskId !== 'dev-manual' && (f.status === 'processing' || f.status === 'pending'),
  )
  const canContinue = sessionFiles.length > 0
  const showProjectPrompt = sessionFiles.length === 0 && !projectPromptDismissed
  const nextHint = canContinue
    ? null
    : hasProcessing
      ? 'Please wait for analysis to complete before continuing.'
      : 'Upload a CAD file before continuing. Files are analyzed from the DFM workspace.'

  return (
    <>
      {sessionFiles.map((f) =>
        f.taskId !== 'dev-manual' && (f.status === 'processing' || f.status === 'pending') ? (
          <FilePoller key={f.id} file={f} />
        ) : null,
      )}

      <AnimatePresence>
        {showProjectPrompt && (
          <motion.aside
            className="project-side-prompt"
            aria-label="Start a new project"
            initial={{ opacity: 0, x: '100%' }}
            animate={{ opacity: 1, x: 0 }}
            exit={{ opacity: 0, x: '100%' }}
            transition={{ type: 'spring', stiffness: 320, damping: 30 }}
          >
            <button
              className="project-side-prompt-close"
              type="button"
              aria-label="Dismiss project prompt"
              onClick={() => setProjectPromptDismissed(true)}
            >
              x
            </button>
            <h2>Start this upload as a project?</h2>
            <p>
              Use a project when you want to keep the analysis, notes, and follow-up files grouped.
            </p>
            <div className="project-side-prompt-actions">
              <button
                type="button"
                className="project-prompt-primary"
                onClick={() => navigate('/projects')}
              >
                Start Project
              </button>
              <button
                type="button"
                className="project-prompt-secondary"
                onClick={() => setProjectPromptDismissed(true)}
              >
                Just Upload
              </button>
            </div>
          </motion.aside>
        )}
      </AnimatePresence>

      <div className="workflow-layout">
        <section className="workflow-panel">
          <section className="home-header">
            <h1>Manufacturability scoring for molding and 3D printing</h1>
            <p>Upload CAD files to get started.</p>
          </section>

          {sessionFiles.length > 0 && (
            <div className="file-list-container">
              <div className="file-list-header">
                <h3>Uploaded Files ({sessionFiles.length})</h3>
                <button
                  type="button"
                  className="clear-files-btn"
                  onClick={() => sessionFiles.forEach((file) => closeTab(file.id))}
                >
                  Clear all
                </button>
              </div>
              <div className="file-list">
                {sessionFiles.map((f) => (
                  <FileCard
                    key={f.id}
                    name={f.name}
                    status={f.status}
                    taskId={f.taskId}
                    errorMessage={f.errorMessage}
                    onRemove={() => closeTab(f.id)}
                  />
                ))}
              </div>
            </div>
          )}
        </section>

        <aside className="viewer-panel" aria-label="CAD file upload drop zone">
          <div className="viewer-panel-header">
            <div>
              <span>CAD Upload</span>
              <strong>Drop Zone</strong>
            </div>
          </div>
          <UploadDropzone />
        </aside>
      </div>

      <WizardNav
        hint={nextHint}
        next={{
          onClick: () => navigate('/analysis'),
          disabled: !canContinue,
          title: nextHint ?? undefined,
        }}
      />
    </>
  )
}
