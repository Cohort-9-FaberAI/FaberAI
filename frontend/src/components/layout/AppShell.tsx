import type { ReactNode } from 'react'
import Sidebar from './Sidebar'
import TopHeader from './TopHeader'
import ChatPanel from './ChatPanel'

export default function AppShell({ children }: { children: ReactNode }) {
  return (
    <div className="app-shell">
      <Sidebar />
      <div className="app-main">
        <TopHeader />
        <div className="app-content">{children}</div>
      </div>
      <ChatPanel />
    </div>
  )
}
