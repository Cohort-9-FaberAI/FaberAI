import { useStore } from '../../store'

export default function ProcessToggle() {
  const process = useStore((s) => s.process)
  const setProcess = useStore((s) => s.setProcess)

  const options = [
    { value: null, label: 'Not sure' },
    { value: 'molding' as const, label: 'Molding' },
    { value: 'printing' as const, label: 'Printing' },
  ]

  return (
    <div className="process-toggle">
      {options.map((opt) => (
        <button
          key={opt.label}
          type="button"
          className={`process-toggle-btn${process === opt.value ? ' active' : ''}`}
          onClick={() => setProcess(opt.value)}
        >
          {opt.label}
        </button>
      ))}
    </div>
  )
}
