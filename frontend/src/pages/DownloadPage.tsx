import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import AppShell from '../components/layout/AppShell'
import StepIndicator from '../components/layout/StepIndicator'
import { useStore } from '../store'

const PROJECT_STEPS = ['Upload', 'Extra Info', 'Conclusion']

export default function DownloadPage() {
  const navigate = useNavigate()
  const process = useStore((s) => s.process)
  const wizardSource = useStore((s) => s.source)
  const wizardProjectId = useStore((s) => s.projectId)
  const [comparison, setComparison] = useState(false)
  const showComparison = process === null

  const isProject = wizardSource === 'project' || wizardSource === 'view'
  const backToStart = isProject && wizardProjectId ? `/projects/${wizardProjectId}` : '/home'
  const backLabel = isProject ? 'Back to Project' : 'Back To Upload'

  return (
    <AppShell>
      <StepIndicator
        currentStep={isProject ? 3 : 4}
        steps={isProject ? PROJECT_STEPS : undefined}
      />

      <h1>Download</h1>

      {showComparison && (
        <div className="download-toggle">
          <span>Include Molding vs Printing comparison in PDF?</span>
          <button
            type="button"
            className={`process-toggle-btn${comparison ? ' active' : ''}`}
            onClick={() => setComparison(true)}
          >
            Yes
          </button>
          <button
            type="button"
            className={`process-toggle-btn${!comparison ? ' active' : ''}`}
            onClick={() => setComparison(false)}
          >
            No
          </button>
        </div>
      )}

      <button
        type="button"
        className="download-pdf-btn"
        onClick={() => {
          alert('PDF download will be available once the backend endpoint is ready.')
        }}
      >
        Download PDF
      </button>

      <div className="wizard-nav">
        <button type="button" className="wizard-nav-back" onClick={() => navigate('/conclusion')}>
          Go Back
        </button>
        <button type="button" onClick={() => navigate(backToStart)}>
          {backLabel}
        </button>
      </div>
    </AppShell>
  )
}
