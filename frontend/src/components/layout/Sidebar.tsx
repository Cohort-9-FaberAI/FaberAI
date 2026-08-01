import { NavLink } from 'react-router-dom'

const navItems = [
  { label: 'Quick Upload', to: '/upload', icon: 'U' },
  { label: 'Projects', to: '/projects', icon: 'P' },
]

interface SidebarProps {
  collapsed: boolean
  onToggle: () => void
}

export default function Sidebar({ collapsed, onToggle }: SidebarProps) {
  return (
    <aside className={`sidebar${collapsed ? ' collapsed' : ''}`}>
      <button
        type="button"
        className="sidebar-toggle"
        onClick={onToggle}
        aria-label={collapsed ? 'Expand sidebar' : 'Collapse sidebar'}
        title={collapsed ? 'Expand sidebar' : 'Collapse sidebar'}
      >
        {collapsed ? '»' : '«'}
      </button>
      <div className="sidebar-logo">Faber AI</div>
      <nav className="sidebar-nav">
        {navItems.map((item) => (
          <NavLink
            key={item.label}
            to={item.to}
            className={({ isActive }) => `sidebar-nav-item${isActive ? ' active' : ''}`}
          >
            <span
              style={{
                display: 'inline-flex',
                alignItems: 'center',
                justifyContent: 'center',
                width: 24,
                height: 24,
                borderRadius: 6,
                background: 'rgba(255,255,255,0.1)',
                fontSize: 12,
                fontWeight: 700,
              }}
            >
              {item.icon}
            </span>
            <span className="sidebar-label">{item.label}</span>
          </NavLink>
        ))}
      </nav>
      <div style={{ marginTop: 'auto' }}>
        <NavLink
          to="/debug"
          className={({ isActive }) => `sidebar-nav-item${isActive ? ' active' : ''}`}
          style={{ fontSize: 12, opacity: 0.5 }}
        >
          <span className="sidebar-label">API Debug</span>
        </NavLink>
      </div>
    </aside>
  )
}
