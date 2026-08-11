import { useStore, DEFAULT_SETTINGS } from '../../store'

export default function ProcessToggle({ fileId }: { fileId: string }) {
  const process = useStore((s) => s.settingsByFile[fileId]?.process ?? DEFAULT_SETTINGS.process)
  const setSettings = useStore((s) => s.setSettings)

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
          onClick={() => setSettings(fileId, { process: opt.value })}
        >
          {opt.label}
        </button>
      ))}
    </div>
  )
}
