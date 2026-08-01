import { useState } from 'react'
import { useNavigate, useParams } from 'react-router-dom'
import { motion, AnimatePresence } from 'framer-motion'
import AppShell from '../components/layout/AppShell'
import FileDropzone from '../components/common/FileDropzone'
import { useStore, type ProjectFile } from '../store'

const STATUS_LABELS: Record<string, string> = {
  stored: 'Ready',
  processing: 'Processing',
  completed: 'Completed',
  failed: 'Failed',
}

export default function ProjectDetailPage() {
  const { id } = useParams()
  const navigate = useNavigate()
  const project = useStore((s) => s.projects.find((p) => p.id === id))
  const addProjectFiles = useStore((s) => s.addProjectFiles)
  const removeProjectFile = useStore((s) => s.removeProjectFile)
  const setWizard = useStore((s) => s.setWizard)
  const [pendingFiles, setPendingFiles] = useState<File[]>([])

  if (!project) {
    return (
      <AppShell>
        <p className="list-empty">Project not found.</p>
        <button type="button" onClick={() => navigate('/projects')}>
          Back to Projects
        </button>
      </AppShell>
    )
  }

  const addFiles = () => {
    if (pendingFiles.length === 0) return
    addProjectFiles(
      project.id,
      pendingFiles.map((f) => ({
        id: crypto.randomUUID(),
        name: f.name,
        file: f,
        taskId: null,
        analysisId: null,
        status: 'stored' as const,
        analysisResult: null,
      })),
    )
    setPendingFiles([])
  }

  const analyze = (pf: ProjectFile) => {
    setWizard({ source: 'project', projectId: project.id, fileId: pf.id, file: pf.file })
    navigate('/extra-info')
  }

  const viewResults = (pf: ProjectFile) => {
    setWizard({ source: 'view', projectId: project.id, fileId: pf.id, file: null })
    navigate('/conclusion')
  }

  const renderActions = (pf: ProjectFile) => {
    if (pf.status === 'completed' && pf.analysisResult) {
      return (
        <>
          <button type="button" className="project-file-analyze" onClick={() => viewResults(pf)}>
            View Results
          </button>
          <button type="button" className="project-file-analyze" onClick={() => analyze(pf)}>
            Re-analyze
          </button>
        </>
      )
    }
    if (pf.status === 'stored' || pf.status === 'failed') {
      return (
        <button type="button" className="project-file-analyze" onClick={() => analyze(pf)}>
          {pf.status === 'failed' ? 'Retry' : 'Analyze'}
        </button>
      )
    }
    return null
  }

  return (
    <AppShell>
      <div className="project-detail-header">
        <div>
          <button type="button" className="wizard-nav-back" onClick={() => navigate('/projects')}>
            &larr; Projects
          </button>
          <h1 style={{ marginTop: 12 }}>{project.name}</h1>
          <p className="project-detail-desc">{project.description || 'No description'}</p>
        </div>
        <span className="project-file-count">
          {project.files.length} file{project.files.length === 1 ? '' : 's'}
        </span>
      </div>

      <section className="project-add-files">
        <h2>Add Files</h2>
        <FileDropzone files={pendingFiles} onChange={setPendingFiles} />
        <button
          className="next-btn"
          type="button"
          disabled={pendingFiles.length === 0}
          onClick={addFiles}
        >
          Add to Project
        </button>
      </section>

      <section className="project-files">
        <h2>Files</h2>
        {project.files.length === 0 ? (
          <p className="list-empty">No files yet. Add CAD files above to get started.</p>
        ) : (
          <div className="project-file-list">
            <AnimatePresence>
              {project.files.map((pf) => (
                <motion.div
                  key={pf.id}
                  className="project-file-row"
                  layout
                  initial={{ opacity: 0, y: 8 }}
                  animate={{ opacity: 1, y: 0 }}
                  exit={{ opacity: 0, y: -8 }}
                  transition={{ duration: 0.2 }}
                >
                  <div className="project-file-info">
                    <span className="file-card-name">{pf.name}</span>
                    <span className={`file-card-status status-${pf.status}`}>
                      {STATUS_LABELS[pf.status] ?? pf.status}
                    </span>
                  </div>
                  <div className="project-file-actions">
                    {renderActions(pf)}
                    <button
                      type="button"
                      className="project-file-remove"
                      onClick={() => removeProjectFile(project.id, pf.id)}
                    >
                      Remove
                    </button>
                  </div>
                </motion.div>
              ))}
            </AnimatePresence>
          </div>
        )}
      </section>
    </AppShell>
  )
}
