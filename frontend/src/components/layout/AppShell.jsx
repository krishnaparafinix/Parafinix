import { Outlet, useLocation } from 'react-router-dom'
import Sidebar from './Sidebar'
import { useAuth } from '../../context/AuthContext'
import { pageBg, font } from '../../lib/theme'

function activeFromPath(pathname) {
  if (pathname.startsWith('/clients')) return 'clients'
  if (pathname.startsWith('/reports')) return 'reports'
  return 'dashboard'
}

export default function AppShell() {
  const { user } = useAuth()
  const location = useLocation()

  return (
    <div style={{ minHeight: '100vh', background: pageBg, fontFamily: font.body, display: 'flex' }}>
      <Sidebar active={activeFromPath(location.pathname)} user={user} />
      <div style={{ flex: 1, minWidth: 0, display: 'flex', flexDirection: 'column' }}>
        <Outlet />
      </div>
    </div>
  )
}
