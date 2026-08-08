const steps = ['Upload', 'Extra Info', 'Analysis', 'Conclusion', 'Download']

interface StepIndicatorProps {
  currentStep: number
}

export default function StepIndicator({ currentStep }: StepIndicatorProps) {
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
