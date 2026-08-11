import { useState, type ReactNode } from 'react'
import { Outlet } from 'react-router-dom'
import Sidebar from './Sidebar'
import TopHeader from './TopHeader'
import ChatPanel from './ChatPanel'

export default function AppShell({ children }: { children?: ReactNode }) {
  const [collapsed, setCollapsed] = useState(false)

  return (
    <div className="app-shell">
      <Sidebar collapsed={collapsed} onToggle={() => setCollapsed((c) => !c)} />
      <div className="app-main">
        <TopHeader />
        <div className="app-content">{children ?? <Outlet />}</div>
      </div>
      <ChatPanel />
    </div>
  )
}
