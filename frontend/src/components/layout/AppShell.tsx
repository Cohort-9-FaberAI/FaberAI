import type { ReactNode } from 'react'
import Sidebar from './Sidebar'
import UsageIndicator from './UsageIndicator'
import AskFaberAIButton from './AskFaberAIButton'

export default function AppShell({ children }: { children: ReactNode }) {
  return (
    <div className="app-shell">
      <Sidebar />
      <div className="app-main">
        <div className="app-content">{children}</div>
        <div className="app-footer">
          <UsageIndicator />
          <AskFaberAIButton />
        </div>
      </div>
    </div>
  )
}
