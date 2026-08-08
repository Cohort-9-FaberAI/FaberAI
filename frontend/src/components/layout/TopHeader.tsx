import AskFaberAIButton from './AskFaberAIButton'
import UsageIndicator from './UsageIndicator'

export default function TopHeader() {
  return (
    <header className="top-header">
      <div className="top-header-title">
        <span>Workspace</span>
        <strong>DFM review</strong>
      </div>
      <div className="top-header-actions">
        <UsageIndicator />
        <AskFaberAIButton />
      </div>
    </header>
  )
}
