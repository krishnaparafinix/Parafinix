import { Navigate, Outlet } from 'react-router-dom'
import { useAuth } from '../context/AuthContext'

export default function ProtectedRoute() {
  const { user, loading } = useAuth()

  if (loading) {
    return (
      <div style={{ display: 'flex', height: '100vh', alignItems: 'center', justifyContent: 'center', background: '#0f1113' }}>
        <div style={{ height: 24, width: 24, borderRadius: '50%', border: '2px solid #5fd0c4', borderTopColor: 'transparent', animation: 'pfx-spin 0.7s linear infinite' }} />
      </div>
    )
  }

  if (!user) return <Navigate to="/login" replace />
  return <Outlet />
}
