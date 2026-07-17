import { NavLink } from 'react-router-dom'

const navItems = [
  { label: 'Upload', to: '/home' },
  { label: 'Projects', to: null },
  { label: 'Library', to: null },
  { label: 'History', to: null },
]

export default function Sidebar() {
  return (
    <aside className="sidebar">
      <div className="sidebar-logo">FaberAI</div>
      <nav className="sidebar-nav">
        {navItems.map((item) =>
          item.to ? (
            <NavLink
              key={item.label}
              to={item.to}
              className={({ isActive }) => `sidebar-nav-item${isActive ? ' active' : ''}`}
            >
              {item.label}
            </NavLink>
          ) : (
            <span key={item.label} className="sidebar-nav-item disabled">
              {item.label}
            </span>
          ),
        )}
      </nav>
      <NavLink
        to="/debug"
        className={({ isActive }) => `sidebar-nav-item${isActive ? ' active' : ''}`}
      >
        API Debug
      </NavLink>
    </aside>
  )
}
