import { useStore } from '../../store'
import type { ProcessChoice } from '../../store'

interface ProcessToggleProps {
  disabled?: boolean
  fileId?: string | null
}

export default function ProcessToggle({ disabled = false, fileId }: ProcessToggleProps) {
  const setFileProcess = useStore((s) => s.setFileProcess)
  const process = useStore((s) => (fileId ? (s.processByFile[fileId] ?? null) : s.process))
  const setProcess = useStore((s) => (fileId ? undefined : s.setProcess))

  const options: { value: ProcessChoice; label: string }[] = [
    { value: null, label: 'Not sure' },
    { value: 'molding', label: 'Molding' },
    { value: 'printing', label: 'Printing' },
  ]

  const handleSelect = (value: ProcessChoice) => {
    if (disabled) return
    if (fileId) {
      setFileProcess(fileId, value)
    } else if (setProcess) {
      setProcess(value)
    }
  }

  return (
    <div className={`process-toggle${disabled ? ' is-disabled' : ''}`}>
      {options.map((opt) => (
        <button
          key={opt.label}
          type="button"
          className={`process-toggle-btn${process === opt.value ? ' active' : ''}`}
          disabled={disabled}
          onClick={() => handleSelect(opt.value)}
        >
          {opt.label}
        </button>
      ))}
    </div>
  )
}
