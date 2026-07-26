import { useRef, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import AppShell from '../components/layout/AppShell'
import StepIndicator from '../components/layout/StepIndicator'
import Modal from '../components/common/Modal'
import UploadDropzone from '../components/home/UploadDropzone'
import FileCard from '../components/home/FileCard'
import { useStore } from '../store'

export default function HomePage() {
  const navigate = useNavigate()
  const files = useStore((s) => s.files)
  const setProject = useStore((s) => s.setProject)
  const addFile = useStore((s) => s.addFile)
  const setCurrentFileBuffer = useStore((s) => s.setCurrentFileBuffer)
  const [modalOpen, setModalOpen] = useState(true)
  const stlInputRef = useRef<HTMLInputElement>(null)

  const completedFiles = files.filter((f) => f.status === 'completed')

  function handleManualStl(file: File) {
    const id = crypto.randomUUID()
    addFile({ id, name: file.name, taskId: 'dev-manual', analysisId: null, status: 'completed' })
    file.arrayBuffer().then((buffer) => setCurrentFileBuffer(buffer))
  }

  return (
    <AppShell>
      <StepIndicator currentStep={1} />

      <Modal open={modalOpen} onClose={() => setModalOpen(false)}>
        <h2>Would you like to start a new Project?</h2>
        <div className="modal-actions">
          <button type="button" onClick={() => setModalOpen(false)}>
            No I want to just upload
          </button>
          <button
            type="button"
            onClick={() => {
              setProject(true)
              setModalOpen(false)
              navigate('/projects')
            }}
          >
            Yes take me to project
          </button>
        </div>
      </Modal>

      <section className="home-header">
        <h1>Manufacturability scoring for molding and 3D printing</h1>
        <p>Upload a CAD file to get started.</p>
      </section>

      <UploadDropzone />

      {files.length > 0 && (
        <div className="file-list">
          {files.map((f) => (
            <FileCard key={f.id} name={f.name} status={f.status} taskId={f.taskId} />
          ))}
        </div>
      )}

      <div className="dev-section">
        <span className="dev-badge">DEV</span>
        <span className="dev-text">Load an STL file directly for 3D preview.</span>
        <input
          ref={stlInputRef}
          type="file"
          accept=".stl"
          className="sr-only"
          onChange={(e) => {
            const file = e.target.files?.[0]
            if (file) handleManualStl(file)
            e.target.value = ''
          }}
        />
        <button
          className="dev-browse-btn"
          type="button"
          onClick={() => stlInputRef.current?.click()}
        >
          Browse STL
        </button>
      </div>

      <button
        className="next-btn"
        type="button"
        disabled={completedFiles.length === 0}
        onClick={() => navigate('/extra-info')}
      >
        Next
      </button>
    </AppShell>
  )
}
