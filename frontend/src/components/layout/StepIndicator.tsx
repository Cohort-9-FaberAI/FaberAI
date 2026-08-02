import { Link } from 'react-router-dom'

const DEFAULT_STEPS = ['Upload', 'Extra Info', 'Analysis', 'Conclusion', 'Download']
const DEFAULT_ROUTES = ['/home', '/extra-info', '/analysis', '/conclusion', '/download']

interface StepIndicatorProps {
  currentStep: number
  steps?: string[]
  stepRoutes?: string[]
}

export default function StepIndicator({
  currentStep,
  steps = DEFAULT_STEPS,
  stepRoutes = DEFAULT_ROUTES,
}: StepIndicatorProps) {
  return (
    <div className="step-indicator">
      {steps.map((label, i) => {
        const num = i + 1
        const state = num < currentStep ? 'completed' : num === currentStep ? 'active' : 'upcoming'
        return (
          <div key={label} className="step-segment">
            <Link
              to={stepRoutes[i] ?? '#'}
              className={`step-item step-${state}`}
              aria-current={state === 'active' ? 'step' : undefined}
            >
              <span className="step-num">{num}</span>
              <span className="step-label">{label}</span>
            </Link>
            {num < steps.length ? (
              <span className={`step-line${num < currentStep ? ' filled' : ''}`} />
            ) : null}
          </div>
        )
      })}
    </div>
  )
}
