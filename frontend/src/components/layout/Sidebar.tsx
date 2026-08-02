import { NavLink } from 'react-router-dom'
import BrandMark from './BrandMark'
import { useStore } from '../../store'

const navItems = [
  { label: 'Upload', to: '/home', icon: 'M10 4l8 4.5v9L10 22l-8-4.5v-9L10 4z' },
  { label: 'Analysis', to: '/analysis', icon: 'M4 18h12 M6 14v4 M10 10v8 M14 6v12' },
  { label: 'Projects', to: '/projects', icon: 'M3 6.5h14M3 12h14M3 17.5h9' },
  { label: 'Library', to: '/library', icon: 'M5 4h10a2 2 0 0 1 2 2v14H7a2 2 0 0 0-2 2V4z' },
  { label: 'History', to: '/history', icon: 'M10 4a8 8 0 1 1-7.1 4.3M10 8v4l3 2' },
]

interface SidebarProps {
  collapsed: boolean
  onToggle: () => void
}

export default function Sidebar({ collapsed, onToggle }: SidebarProps) {
  const theme = useStore((s) => s.theme)
  const toggleTheme = useStore((s) => s.toggleTheme)

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
      <div
        className="sidebar-logo"
        style={{
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'space-between',
          width: '100%',
        }}
      >
        <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
          {collapsed ? (
            <BrandMark size={20} variant="default" className="sidebar-mark-icon" />
          ) : (
            <BrandMark size={24} variant="full" className="sidebar-mark-full" />
          )}
        </div>
        {!collapsed && (
          <button
            type="button"
            onClick={toggleTheme}
            className="theme-toggle-btn"
            title={theme === 'dark' ? 'Switch to Light Mode' : 'Switch to Dark Mode'}
            aria-label="Toggle theme"
            style={{
              background: 'transparent',
              border: 'none',
              color: 'var(--mist)',
              cursor: 'pointer',
              padding: '6px',
              display: 'inline-flex',
              alignItems: 'center',
              justifyContent: 'center',
              borderRadius: '8px',
              transition: 'color 0.2s ease, background 0.2s ease',
            }}
          >
            {theme === 'dark' ? (
              <svg
                width="20"
                height="20"
                viewBox="0 0 24 24"
                fill="none"
                stroke="currentColor"
                strokeWidth="1.8"
                strokeLinecap="round"
                strokeLinejoin="round"
              >
                <circle cx="12" cy="12" r="5" />
                <line x1="12" y1="1" x2="12" y2="3" />
                <line x1="12" y1="21" x2="12" y2="23" />
                <line x1="4.22" y1="4.22" x2="5.64" y2="5.64" />
                <line x1="18.36" y1="18.36" x2="19.78" y2="19.78" />
                <line x1="1" y1="12" x2="3" y2="12" />
                <line x1="21" y1="12" x2="23" y2="12" />
                <line x1="4.22" y1="19.78" x2="5.64" y2="18.36" />
                <line x1="18.36" y1="5.64" x2="19.78" y2="4.22" />
              </svg>
            ) : (
              <svg
                width="20"
                height="20"
                viewBox="0 0 24 24"
                fill="none"
                stroke="currentColor"
                strokeWidth="1.8"
                strokeLinecap="round"
                strokeLinejoin="round"
              >
                <path d="M21 12.79A9 9 0 1 1 11.21 3 7 7 0 0 0 21 12.79z" />
              </svg>
            )}
          </button>
        )}
      </div>
      <nav className="sidebar-nav">
        {navItems.map((item) => (
          <NavLink
            key={item.label}
            to={item.to}
            className={({ isActive }) => `sidebar-nav-item${isActive ? ' active' : ''}`}
          >
            <span className="sidebar-nav-icon" aria-hidden="true">
              <svg viewBox="0 0 20 24" fill="none">
                <path
                  d={item.icon}
                  stroke="currentColor"
                  strokeWidth="1.5"
                  strokeLinecap="round"
                  strokeLinejoin="round"
                />
              </svg>
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
