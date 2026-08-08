import type { ReactNode } from 'react'

interface WizardNavProps {
  previous?: {
    label?: string
    onClick: () => void
    disabled?: boolean
    title?: string
  }
  next?: {
    label?: string
    onClick: () => void
    disabled?: boolean
    title?: string
  }
  extra?: ReactNode
  hint?: string | null
}

export default function WizardNav({ previous, next, extra, hint }: WizardNavProps) {
  if (!previous && !next && !extra && !hint) return null

  return (
    <div className="wizard-nav-shell">
      {hint ? <p className="wizard-nav-hint">{hint}</p> : null}
      <div className="wizard-nav">
        {previous ? (
          <button
            type="button"
            className="wizard-nav-btn wizard-nav-prev"
            onClick={previous.onClick}
            disabled={previous.disabled}
            title={previous.title}
          >
            {previous.label ?? 'Previous'}
          </button>
        ) : null}
        {extra ? extra : null}
        {next ? (
          <button
            type="button"
            className="wizard-nav-btn wizard-nav-next"
            onClick={next.onClick}
            disabled={next.disabled}
            title={next.title}
          >
            {next.label ?? 'Next'}
          </button>
        ) : null}
      </div>
    </div>
  )
}
