export type WorkspaceStep = 'setup' | 'inspection' | 'verdict' | 'export'

interface FileSubNavProps {
  currentStep: WorkspaceStep
  onSelectStep: (step: WorkspaceStep) => void
}

const STEPS: { key: WorkspaceStep; label: string }[] = [
  { key: 'setup', label: 'Setup & Inputs' },
  { key: 'inspection', label: 'DFM Analysis' },
  { key: 'verdict', label: 'Conclusion' },
  { key: 'export', label: 'Download Report' },
]

export default function FileSubNav({ currentStep, onSelectStep }: FileSubNavProps) {
  const currentStepIdx = STEPS.findIndex((s) => s.key === currentStep) + 1

  return (
    <div
      className="step-indicator workspace-step-timeline"
      role="tablist"
      aria-label="File analysis workflow steps"
    >
      {STEPS.map((s, i) => {
        const num = i + 1
        const state =
          num < currentStepIdx ? 'completed' : num === currentStepIdx ? 'active' : 'upcoming'
        return (
          <div
            key={s.key}
            className="step-segment"
            style={i === STEPS.length - 1 ? { flex: '0 0 auto' } : undefined}
          >
            <button
              type="button"
              role="tab"
              aria-selected={state === 'active'}
              className={`step-item step-${state}`}
              style={{
                background: 'transparent',
                border: 'none',
                cursor: 'pointer',
                padding: 0,
                font: 'inherit',
                display: 'flex',
                alignItems: 'center',
              }}
              onClick={() => onSelectStep(s.key)}
            >
              <span className="step-num">{num}</span>
              <span className="step-label">{s.label}</span>
            </button>
            {i < STEPS.length - 1 ? (
              <span className={`step-line${num < currentStepIdx ? ' filled' : ''}`} />
            ) : null}
          </div>
        )
      })}
    </div>
  )
}
