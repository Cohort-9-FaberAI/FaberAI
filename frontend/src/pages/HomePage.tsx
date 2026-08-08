import { useNavigate } from 'react-router-dom'
import AppShell from '../components/layout/AppShell'
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

  useTaskPolling(
    file.status === 'processing' && file.taskId ? file.taskId : null,
    file.analysisId,
    (data) => {
      const status = typeof data?.status === 'string' ? data.status : null
      if (status === 'SUCCESS') {
        updateFile(file.id, { status: 'completed' })
      }
      if (status === 'FAILED' || status === 'FAILURE') {
        const errorMsg =
          typeof data?.error === 'string'
            ? data.error
            : typeof data?.message === 'string'
              ? data.message
              : 'DFM inspection failed during background processing.'
        updateFile(file.id, { status: 'failed', errorMessage: errorMsg })
      }
      const result = data?.result as Record<string, unknown> | undefined
      if (result) {
        setAnalysisResult(file.id, result)
      }
    },
    () => {
      updateFile(file.id, {
        status: 'failed',
        errorMessage: 'Network timeout or server connection error while checking task status.',
      })
    },
  )
  return null
}

export default function HomePage() {
  const navigate = useNavigate()
  const files = useStore((s) => s.files)
  const clearFiles = useStore((s) => s.clearFiles)

  const uploadedFiles = files.filter((f) => f.taskId !== 'dev-manual')
  const hasProcessing = files.some(
    (f) => f.taskId !== 'dev-manual' && (f.status === 'processing' || f.status === 'pending'),
  )
  const canContinue = uploadedFiles.length > 0
  const nextHint = canContinue
    ? null
    : hasProcessing
      ? 'Please wait for analysis to complete before continuing.'
      : 'Upload a CAD file before continuing. Files are analyzed from the DFM workspace.'

  return (
    <AppShell>
      {files.map((f) =>
        f.taskId !== 'dev-manual' && (f.status === 'processing' || f.status === 'pending') ? (
          <FilePoller key={f.id} file={f} />
        ) : null,
      )}

      <div className="workflow-layout">
        <section className="workflow-panel">
          <section className="home-header">
            <h1>Manufacturability scoring for molding and 3D printing</h1>
            <p>Upload CAD files to get started.</p>
          </section>

          {files.length > 0 && (
            <div className="file-list-container">
              <div className="file-list-header">
                <h3>Uploaded Files ({files.length})</h3>
                <button type="button" className="clear-files-btn" onClick={() => clearFiles()}>
                  Clear all
                </button>
              </div>
              <div className="file-list">
                {files.map((f) => (
                  <FileCard
                    key={f.id}
                    name={f.name}
                    status={f.status}
                    taskId={f.taskId}
                    errorMessage={f.errorMessage}
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
    </AppShell>
  )
}
