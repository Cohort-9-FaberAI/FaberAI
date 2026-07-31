import type { ReactNode } from 'react'
import Sidebar from './Sidebar'
import AskFaberAIButton from './AskFaberAIButton'
import ChatPanel from './ChatPanel'

export default function AppShell({ children }: { children: ReactNode }) {
  return (
    <div className="app-shell">
      <Sidebar />
      <div className="app-main">
        <div className="app-content">{children}</div>
        <div className="app-footer">
          <AskFaberAIButton />
        </div>
      </div>
      <ChatPanel />
    </div>
  )
}
