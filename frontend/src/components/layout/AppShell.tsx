import { useState, type ReactNode } from 'react'
import Sidebar from './Sidebar'
import AskFaberAIButton from './AskFaberAIButton'
import ChatPanel from './ChatPanel'

export default function AppShell({ children }: { children: ReactNode }) {
  const [collapsed, setCollapsed] = useState(false)

  return (
    <div className="app-shell">
      <Sidebar collapsed={collapsed} onToggle={() => setCollapsed((c) => !c)} />
      <div className="app-main">
        <div className="app-content">{children}</div>
      </div>
      <AskFaberAIButton />
      <ChatPanel />
    </div>
  )
}
