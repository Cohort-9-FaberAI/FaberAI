const DEFAULT_STEPS = ['Upload', 'Extra Info', 'Conclusion', 'Download']

interface StepIndicatorProps {
  currentStep: number
  steps?: string[]
}

export default function StepIndicator({ currentStep, steps = DEFAULT_STEPS }: StepIndicatorProps) {
  return (
    <div className="step-indicator">
      {steps.map((label, i) => {
        const num = i + 1
        const state = num < currentStep ? 'completed' : num === currentStep ? 'active' : 'upcoming'
        return (
          <div key={label} className={`step-item step-${state}`}>
            <span className="step-num">{num}</span>
            <span className="step-label">{label}</span>
          </div>
        )
      })}
    </div>
  )
}
