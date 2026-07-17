import { useNavigate } from 'react-router-dom'
import AppShell from '../components/layout/AppShell'
import StepIndicator from '../components/layout/StepIndicator'
import ModelPreviewPlaceholder from '../components/common/ModelPreviewPlaceholder'
import ProcessToggle from '../components/extra-info/ProcessToggle'
import { useStore } from '../store'

export default function ExtraInfoPage() {
  const navigate = useNavigate()
  const quantity = useStore((s) => s.quantity)
  const material = useStore((s) => s.material)
  const tolerance = useStore((s) => s.tolerance)
  const notes = useStore((s) => s.notes)
  const setQuantity = useStore((s) => s.setQuantity)
  const setMaterial = useStore((s) => s.setMaterial)
  const setTolerance = useStore((s) => s.setTolerance)
  const setNotes = useStore((s) => s.setNotes)

  function handleSubmit(e: React.FormEvent) {
    e.preventDefault()
    navigate('/analysis')
  }

  return (
    <AppShell>
      <StepIndicator currentStep={2} />

      <ModelPreviewPlaceholder />

      <form className="extra-info-form" onSubmit={handleSubmit}>
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
            <option value="aluminum">Aluminum</option>
            <option value="steel">Steel</option>
          </select>
        </div>

        <div className="form-group">
          <label htmlFor="tolerance">Tolerance</label>
          <select id="tolerance" value={tolerance} onChange={(e) => setTolerance(e.target.value)}>
            <option value="">Select tolerance</option>
            <option value="standard">Standard (±0.5mm)</option>
            <option value="tight">Tight (±0.2mm)</option>
            <option value="precision">Precision (±0.1mm)</option>
          </select>
        </div>

        <div className="form-group">
          <label htmlFor="notes">Notes</label>
          <textarea
            id="notes"
            rows={3}
            placeholder="Anything else that should be asked"
            value={notes}
            onChange={(e) => setNotes(e.target.value)}
          />
        </div>

        <div className="token-estimate">Estimated token cost: ~2,400 tokens</div>

        <button className="next-btn" type="submit">
          Submit
        </button>
      </form>
    </AppShell>
  )
}
