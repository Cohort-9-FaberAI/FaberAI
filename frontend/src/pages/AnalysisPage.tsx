import { useEffect, useState } from 'react'
import AppShell from '../components/layout/AppShell'
import StepIndicator from '../components/layout/StepIndicator'
import ModelPreviewPlaceholder from '../components/common/ModelPreviewPlaceholder'
import SeverityLegend from '../components/analysis/SeverityLegend'
import IssueAccordion from '../components/analysis/IssueAccordion'
import { getMockAnalysis } from '../lib/api'

interface Issue {
  severity: 'high' | 'medium' | 'low'
  message: string
  recommendation: string
}

interface MockAnalysisResponse {
  issues: Issue[]
  [key: string]: unknown
}

const fallbackData: MockAnalysisResponse = {
  analysis_id: 'mock-analysis-0001',
  filename: 'sample_bracket.stl',
  status: 'completed',
  manufacturability_score: 72,
  issues: [
    {
      severity: 'high',
      message: 'Wall thickness of 0.8mm is below the minimum of 1.5mm for CNC machining.',
      recommendation: 'Increase wall thickness to at least 1.5mm.',
    },
    {
      severity: 'medium',
      message:
        'Pocket depth-to-width ratio of 5:1 exceeds the recommended 4:1 for standard tooling.',
      recommendation: 'Reduce pocket depth or widen the pocket opening.',
    },
  ],
}

export default function AnalysisPage() {
  const [data, setData] = useState<MockAnalysisResponse>(fallbackData)
  const [activeTab, setActiveTab] = useState<'molding' | 'printing'>('molding')

  useEffect(() => {
    getMockAnalysis()
      .then(setData)
      .catch(() => {})
  }, [])

  const cons = (data.issues ?? []).filter((i) => i.severity === 'high')
  const neutral = (data.issues ?? []).filter((i) => i.severity === 'medium')

  return (
    <AppShell>
      <StepIndicator currentStep={3} />

      <div className="analysis-tabs">
        <button
          type="button"
          className={`analysis-tab${activeTab === 'molding' ? ' active' : ''}`}
          onClick={() => setActiveTab('molding')}
        >
          Molding
        </button>
        <button
          type="button"
          className={`analysis-tab${activeTab === 'printing' ? ' active' : ''}`}
          onClick={() => setActiveTab('printing')}
        >
          Printing
        </button>
      </div>

      <div className="analysis-layout">
        {/* Left thumbnail rail */}
        <div className="analysis-thumb-rail">
          {/* TODO: clarify with design what these 4 thumbnails represent */}
          {[1, 2, 3, 4].map((n) => (
            <div key={n} className="analysis-thumb" />
          ))}
        </div>

        <ModelPreviewPlaceholder />

        <div className="analysis-right-panel">
          <SeverityLegend />

          <IssueAccordion title="Pros" count={0} color="#4caf50" items={[]} />

          <IssueAccordion title="Neutral" count={neutral.length} color="#ffb84d" items={neutral} />

          <IssueAccordion title="Cons" count={cons.length} color="#ff4d4d" items={cons} />
        </div>
      </div>

      <button className="next-btn" type="button" disabled>
        Next
        {/* TODO: navigate to /conclusion once that page is built */}
      </button>
    </AppShell>
  )
}
