import { NavLink } from 'react-router-dom'

const navItems = [
  { label: 'Quick Upload', to: '/home', icon: 'U' },
  { label: 'Projects', to: '/projects', icon: 'P' },
]

export default function Sidebar() {
  return (
    <aside className="sidebar">
      <div className="sidebar-logo">FaberAI</div>
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
            {item.label}
          </NavLink>
        ))}
      </nav>
      <div style={{ marginTop: 'auto' }}>
        <NavLink
          to="/debug"
          className={({ isActive }) => `sidebar-nav-item${isActive ? ' active' : ''}`}
          style={{ fontSize: 12, opacity: 0.5 }}
        >
          API Debug
        </NavLink>
      </div>
    </aside>
  )
}
