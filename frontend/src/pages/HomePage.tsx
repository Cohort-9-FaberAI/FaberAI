import { useState } from 'react'
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
  const [modalOpen, setModalOpen] = useState(true)

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
            <FileCard key={f.id} name={f.name} status={f.status} />
          ))}
        </div>
      )}

      <button
        className="next-btn"
        type="button"
        disabled={files.length === 0}
        onClick={() => navigate('/extra-info')}
      >
        Next
      </button>
    </AppShell>
  )
}
