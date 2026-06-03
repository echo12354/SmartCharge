import { NavLink, Outlet, useNavigate } from 'react-router-dom'
import { useAuth } from '../contexts/AuthContext'

interface LayoutProps {
  variant: 'user' | 'admin'
}

export default function Layout({ variant }: LayoutProps) {
  const { user, logout } = useAuth()
  const navigate = useNavigate()

  const links = variant === 'admin'
    ? [
        { to: '/admin', label: '概览', end: true },
        { to: '/admin/piles', label: '充电桩管理' },
        { to: '/admin/queue', label: '等候队列' },
        { to: '/admin/reports', label: '统计报表' },
      ]
    : [
        { to: '/user', label: '充电服务', end: true },
        { to: '/user/bills', label: '充电详单' },
      ]

  return (
    <div className="app-shell">
      <header className="topbar">
        <div className="brand">
          <span className="brand-icon">⚡</span>
          <div>
            <strong>SmartCharge</strong>
            <span>{variant === 'admin' ? '管理员控制台' : '用户客户端'}</span>
          </div>
        </div>
        <nav className="nav">
          {links.map((link) => (
            <NavLink key={link.to} to={link.to} end={link.end} className={({ isActive }) => (isActive ? 'active' : '')}>
              {link.label}
            </NavLink>
          ))}
        </nav>
        <div className="user-bar">
          <span>{user?.username}</span>
          <button
            type="button"
            className="btn btn-ghost"
            onClick={() => {
              logout()
              navigate('/login')
            }}
          >
            退出
          </button>
        </div>
      </header>
      <main className="page-content">
        <Outlet />
      </main>
    </div>
  )
}
