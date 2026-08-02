import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import AppShell from '../components/layout/AppShell'
import StepIndicator from '../components/layout/StepIndicator'
import ModelPreview from '../components/ModelPreview/ModelPreview'
import ProcessToggle from '../components/extra-info/ProcessToggle'
import { uploadFile } from '../lib/api'
import { useStore } from '../store'

export default function ExtraInfoPage() {
  const navigate = useNavigate()
  const quantity = useStore((s) => s.quantity)
  const material = useStore((s) => s.material)
  const tolerance = useStore((s) => s.tolerance)
  const setQuantity = useStore((s) => s.setQuantity)
  const setMaterial = useStore((s) => s.setMaterial)
  const setTolerance = useStore((s) => s.setTolerance)
  const wizardSource = useStore((s) => s.source)
  const wizardProjectId = useStore((s) => s.projectId)
  const wizardFileId = useStore((s) => s.fileId)
  const wizardFile = useStore((s) => s.file)
  const updateFile = useStore((s) => s.updateFile)
  const updateProjectFile = useStore((s) => s.updateProjectFile)
  const [uploading, setUploading] = useState(false)
  const [error, setError] = useState<string | null>(null)

  async function markFile(status: 'processing' | 'failed') {
    if (wizardSource === 'project' && wizardProjectId && wizardFileId) {
      updateProjectFile(wizardProjectId, wizardFileId, { status })
    } else if (wizardFileId) {
      updateFile(wizardFileId, { status })
    }
  }

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault()
    setUploading(true)
    setError(null)
    try {
      if (wizardFile) {
        const res = await uploadFile(wizardFile)
        if (wizardSource === 'project' && wizardProjectId && wizardFileId) {
          updateProjectFile(wizardProjectId, wizardFileId, {
            taskId: res.task_id,
            analysisId: res.analysis_id ?? null,
            status: 'processing',
          })
        } else if (wizardFileId) {
          updateFile(wizardFileId, {
            taskId: res.task_id,
            analysisId: res.analysis_id ?? null,
            status: 'processing',
          })
        }
      }
      navigate('/conclusion')
    } catch (err) {
      markFile('failed')
      setError(err instanceof Error ? err.message : 'Upload failed. Please try again.')
    } finally {
      setUploading(false)
    }
  }

  return (
    <AppShell>
      <StepIndicator currentStep={2} />

      <div className="extra-info-layout">
        <div className="extra-info-viewport">
          <ModelPreview height="100%" />
        </div>

        <form className="extra-info-overlay" onSubmit={handleSubmit}>
          <div className="form-group">
            <label>Process</label>
            <ProcessToggle />
          </div>

          <div className="form-group">
            <label htmlFor="quantity">Quantity</label>
            <input
              id="quantity"
              type="number"
              min={1}
              value={quantity}
              onChange={(e) => setQuantity(Number(e.target.value))}
            />
          </div>

          <div className="form-group">
            <label htmlFor="material">Material</label>
            <select id="material" value={material} onChange={(e) => setMaterial(e.target.value)}>
              <option value="">Select material</option>
              <option value="pla">PLA</option>
              <option value="abs">ABS</option>
              <option value="petg">PETG</option>
              <option value="nylon">Nylon</option>
            </select>
          </div>

          <div className="form-group">
            <label htmlFor="tolerance">Tolerance</label>
            <select id="tolerance" value={tolerance} onChange={(e) => setTolerance(e.target.value)}>
              <option value="">Select tolerance</option>
              <option value="standard">Standard (&plusmn;0.5mm)</option>
              <option value="tight">Tight (&plusmn;0.2mm)</option>
              <option value="precision">Precision (&plusmn;0.1mm)</option>
            </select>
          </div>

          {error && <p className="form-error">{error}</p>}

          <button className="next-btn" type="submit" disabled={uploading}>
            {uploading ? 'Uploading...' : 'Submit'}
          </button>
        </form>
      </div>
    </AppShell>
  )
}
