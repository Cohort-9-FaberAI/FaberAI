import { useNavigate } from 'react-router-dom'
import AppShell from '../components/layout/AppShell'
import StepIndicator from '../components/layout/StepIndicator'
import UploadDropzone from '../components/home/UploadDropzone'
import FileCard from '../components/home/FileCard'
import { useStore } from '../store'

export default function UploadPage() {
  const navigate = useNavigate()
  const files = useStore((s) => s.files)
  const clearFiles = useStore((s) => s.clearFiles)
  const setWizard = useStore((s) => s.setWizard)

  const readyFile = files.find((f) => f.status === 'stored' && f.file)

  function startAnalysis() {
    if (!readyFile?.file) return
    setWizard({ source: 'quick', projectId: null, fileId: readyFile.id, file: readyFile.file })
    navigate('/extra-info')
  }

  return (
    <AppShell>
      <StepIndicator currentStep={1} />

      <section className="home-header">
        <h1>Quick Upload</h1>
        <p>Upload a CAD file for a one-off manufacturability analysis.</p>
      </section>

      <UploadDropzone />

      {files.length > 0 && (
        <div className="file-list">
          {files.map((f) => (
            <FileCard
              key={f.id}
              name={f.name}
              status={f.status}
              taskId={f.taskId}
              onRemove={() => clearFiles()}
            />
          ))}
        </div>
      )}

      <button className="next-btn" type="button" disabled={!readyFile} onClick={startAnalysis}>
        Next
      </button>
    </AppShell>
  )
}
