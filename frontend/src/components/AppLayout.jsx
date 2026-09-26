import { useCallback, useEffect, useState } from 'react'
import { NavLink, Outlet } from 'react-router-dom'
import { getInstallation, getUsage, USE_MOCKS } from '../api/bomwatcher'
import { useAuth } from '../context/useAuth'
import Icon from './Icon'
import Logo from './Logo'
import { Avatar, PageLoader } from './ui'

const NAV = [
  { to: '/app', label: 'Dashboard', icon: 'dashboard', end: true },
  { to: '/app/repos', label: 'Repositories', icon: 'repo' },
  { to: '/app/github', label: 'GitHub', icon: 'github' },
  { to: '/app/settings', label: 'Settings', icon: 'settings' },
]

export default function AppLayout() {
  const { email, logout } = useAuth()
  const [menuOpen, setMenuOpen] = useState(false)
  const [installation, setInstallation] = useState(undefined)
  const [usage, setUsage] = useState(null)

  const refresh = useCallback(async () => {
    const [inst, use] = await Promise.all([getInstallation().catch(() => null), getUsage().catch(() => null)])
    setInstallation(inst)
    setUsage(use)
  }, [])

  useEffect(() => {
    refresh()
  }, [refresh])

  const pct = usage ? Math.min(100, (usage.repos_enabled / usage.repo_limit) * 100) : 0

  return (
    <div className="app-shell">
      <header className="topbar">
        <Logo to="/app" />
        <button className="icon-btn" onClick={() => setMenuOpen((o) => !o)} aria-label="Toggle menu" aria-expanded={menuOpen}>
          <Icon name={menuOpen ? 'x' : 'menu'} size={20} />
        </button>
      </header>

      <aside className={`sidebar ${menuOpen ? 'open' : ''}`}>
        <div className="sidebar-brand">
          <Logo to="/app" />
        </div>
        <nav className="sidebar-nav">
          {NAV.map((n) => (
            <NavLink key={n.to} to={n.to} end={n.end} className="nav-link" onClick={() => setMenuOpen(false)}>
              <Icon name={n.icon} />
              {n.label}
              {n.to === '/app/github' && installation === null && <span className="nav-dot" title="Not connected" />}
            </NavLink>
          ))}
        </nav>

        <div className="sidebar-foot">
          {usage && (
            <div className="usage-card">
              <div className="usage-head">
                <span>Free trial</span>
                <span className="mono">
                  {usage.repos_enabled}/{usage.repo_limit} repos
                </span>
              </div>
              <div className="meter">
                <div className="meter-fill" style={{ width: `${pct}%` }} />
              </div>
            </div>
          )}
          <div className="user-row">
            <Avatar name={email ?? '?'} size={30} />
            <span className="user-email" title={email}>
              {email}
            </span>
            <button className="icon-btn" onClick={() => logout()} aria-label="Log out" title="Log out">
              <Icon name="logout" size={16} />
            </button>
          </div>
        </div>
      </aside>

      <main className="app-main">
        {USE_MOCKS && (
          <div className="demo-banner">
            <Icon name="zap" size={14} />
            Demo mode: GitHub, repos and scans are simulated in your browser until the backend endpoints exist.
          </div>
        )}
        <div className="app-content">
          {installation === undefined ? <PageLoader /> : <Outlet context={{ installation, usage, refresh }} />}
        </div>
      </main>
    </div>
  )
}
