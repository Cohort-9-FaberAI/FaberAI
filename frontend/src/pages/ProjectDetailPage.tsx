import { useState } from 'react'
import { useNavigate, useParams } from 'react-router-dom'
import { motion, AnimatePresence } from 'framer-motion'
import AppShell from '../components/layout/AppShell'
import FileDropzone from '../components/common/FileDropzone'
import { useStore, type ProjectFile, type UploadedFile } from '../store'

const STATUS_LABELS: Record<string, string> = {
  stored: 'Ready',
  processing: 'Processing',
  completed: 'Completed',
  failed: 'Failed',
}

function detectSourceFormat(name: string): 'stl' | 'step' | null {
  const lowerName = name.toLowerCase()
  if (lowerName.endsWith('.stl')) return 'stl'
  if (lowerName.endsWith('.step') || lowerName.endsWith('.stp')) return 'step'
  return null
}

export default function ProjectDetailPage() {
  const { id } = useParams()
  const navigate = useNavigate()
  const project = useStore((s) => s.projects.find((p) => p.id === id))
  const addProjectFiles = useStore((s) => s.addProjectFiles)
  const removeProjectFile = useStore((s) => s.removeProjectFile)
  const addFile = useStore((s) => s.addFile)
  const files = useStore((s) => s.files)
  const openTab = useStore((s) => s.openTab)
  const setFileBuffer = useStore((s) => s.setFileBuffer)
  const setCurrentFileBuffer = useStore((s) => s.setCurrentFileBuffer)
  const setAnalysisResult = useStore((s) => s.setAnalysisResult)
  const setRequestedStep = useStore((s) => s.setRequestedStep)
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
    const existing = files.find((f) => f.id === pf.id)
    const fileSourceFormat = detectSourceFormat(pf.name)

    if (existing) {
      openTab(pf.id)
    } else {
      const uploaded: UploadedFile = {
        id: pf.id,
        name: pf.name,
        file: pf.file,
        taskId: null,
        analysisId: null,
        fileUrl: null,
        sourceFormat: fileSourceFormat,
        status: 'pending',
        analysisResult: null,
        projectName: project.name,
      }
      addFile(uploaded)
    }

    if (pf.file) {
      pf.file
        .arrayBuffer()
        .then((buffer) => {
          setFileBuffer(pf.id, buffer)
          if (fileSourceFormat === 'stl') {
            setCurrentFileBuffer(buffer)
          }
        })
        .catch(() => {
          // buffer read failed, preview won't work immediately but upload proceeds
        })
    }

    navigate('/analysis')
  }

  const viewResults = (pf: ProjectFile) => {
    const existing = files.find((f) => f.id === pf.id)

    if (!existing) {
      const uploaded: UploadedFile = {
        id: pf.id,
        name: pf.name,
        file: null,
        taskId: pf.taskId,
        analysisId: pf.analysisId,
        fileUrl: null,
        sourceFormat: detectSourceFormat(pf.name),
        status: pf.analysisResult ? 'completed' : 'stored',
        analysisResult: pf.analysisResult,
        projectName: project.name,
      }
      addFile(uploaded)
    } else {
      openTab(pf.id)
    }
    if (pf.analysisResult) {
      setAnalysisResult(pf.id, pf.analysisResult)
    }
    setRequestedStep({ fileId: pf.id, step: 'inspection' })
    navigate('/analysis')
  }

  const renderActions = (pf: ProjectFile) => {
    if (pf.status === 'completed' && pf.analysisResult) {
      return (
        <>
          <button type="button" className="project-file-analyze" onClick={() => viewResults(pf)}>
            View Analysis
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
