import { useState } from 'react'
import { Link, useLocation, useNavigate } from 'react-router-dom'
import AuthLogo from '../components/AuthLogo'
import { useAuth } from '../context/AuthContext'
import { apiErrorMessage } from '../api/client'
import { color, font, pageBg } from '../lib/theme'

const inputStyle = {
  width: '100%', boxSizing: 'border-box', background: color.bg, border: `1px solid ${color.borderRaised}`,
  borderRadius: 8, padding: '10px 13px', color: color.textPrimary, fontSize: 13.5, outline: 'none', fontFamily: font.body,
}
const labelStyle = { display: 'block', marginBottom: 6, fontSize: 12.5, fontWeight: 500, color: color.textSecondary2 }

export default function Login() {
  const { login } = useAuth()
  const navigate = useNavigate()
  const location = useLocation()
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [error, setError] = useState('')
  const [loading, setLoading] = useState(false)

  const handleSubmit = async (e) => {
    e.preventDefault()
    setError('')
    setLoading(true)
    try {
      await login(email, password)
      navigate(location.state?.from || '/', { replace: true })
    } catch (err) {
      setError(apiErrorMessage(err, 'Could not sign in. Check your details and try again.'))
    } finally {
      setLoading(false)
    }
  }

  return (
    <div style={{ minHeight: '100vh', display: 'flex', alignItems: 'center', justifyContent: 'center', background: pageBg, fontFamily: font.body, padding: 16 }}>
      <div style={{ width: '100%', maxWidth: 380 }}>
        <div style={{ marginBottom: 32 }}><AuthLogo /></div>

        <div style={{ background: color.card, border: `1px solid ${color.border}`, borderRadius: 14, padding: 28 }}>
          <h1 style={{ fontFamily: font.display, fontSize: 18, fontWeight: 600, color: color.textPrimary, margin: 0 }}>Sign in</h1>
          <p style={{ marginTop: 4, fontSize: 13, color: color.textFaint }}>Your report wingman is waiting.</p>

          <form onSubmit={handleSubmit} style={{ marginTop: 22, display: 'flex', flexDirection: 'column', gap: 16 }}>
            <div>
              <label style={labelStyle} htmlFor="email">Email</label>
              <input id="email" type="email" required autoComplete="email" value={email} onChange={(e) => setEmail(e.target.value)} style={inputStyle} />
            </div>
            <div>
              <label style={labelStyle} htmlFor="password">Password</label>
              <input id="password" type="password" required autoComplete="current-password" value={password} onChange={(e) => setPassword(e.target.value)} style={inputStyle} />
            </div>

            {error && <p style={{ fontSize: 13, color: '#e08787', margin: 0 }}>{error}</p>}

            <button
              type="submit"
              disabled={loading}
              className="pfx-btn pfx-btn-amber"
              style={{ width: '100%', fontSize: 13.5, fontWeight: 600, color: color.ink, background: color.amber, border: 'none', borderRadius: 9, padding: '12px 0', cursor: 'pointer', opacity: loading ? 0.7 : 1 }}
            >
              {loading ? 'Signing in…' : 'Sign in'}
            </button>
          </form>
        </div>
        <p style={{ marginTop: 18, textAlign: 'center', fontSize: 13, color: color.textFaint }}>
          No account yet? <Link to="/register" style={{ fontWeight: 500, color: color.teal }}>Register</Link>
        </p>
      </div>
    </div>
  )
}
