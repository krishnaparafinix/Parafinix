import { useState } from 'react'
import { Link, useNavigate } from 'react-router-dom'
import AuthLogo from '../components/AuthLogo'
import { register } from '../api/auth'
import { apiErrorMessage } from '../api/client'
import { color, font, pageBg } from '../lib/theme'

const inputStyle = {
  width: '100%', boxSizing: 'border-box', background: color.bg, border: `1px solid ${color.borderRaised}`,
  borderRadius: 8, padding: '10px 13px', color: color.textPrimary, fontSize: 13.5, outline: 'none', fontFamily: font.body,
}
const labelStyle = { display: 'block', marginBottom: 6, fontSize: 12.5, fontWeight: 500, color: color.textSecondary2 }

export default function Register() {
  const navigate = useNavigate()
  const [form, setForm] = useState({ email: '', password: '', full_name: '', firm_name: '' })
  const [error, setError] = useState('')
  const [success, setSuccess] = useState(false)
  const [loading, setLoading] = useState(false)

  const update = (key) => (e) => setForm((f) => ({ ...f, [key]: e.target.value }))

  const handleSubmit = async (e) => {
    e.preventDefault()
    setError('')
    setLoading(true)
    try {
      await register(form)
      setSuccess(true)
    } catch (err) {
      setError(apiErrorMessage(err, 'Registration failed. Please try again.'))
    } finally {
      setLoading(false)
    }
  }

  return (
    <div style={{ minHeight: '100vh', display: 'flex', alignItems: 'center', justifyContent: 'center', background: pageBg, fontFamily: font.body, padding: 16 }}>
      <div style={{ width: '100%', maxWidth: 380 }}>
        <div style={{ marginBottom: 32 }}><AuthLogo /></div>

        <div style={{ background: color.card, border: `1px solid ${color.border}`, borderRadius: 14, padding: 28 }}>
          {success ? (
            <div style={{ textAlign: 'center' }}>
              <h1 style={{ fontFamily: font.display, fontSize: 18, fontWeight: 600, color: color.textPrimary, margin: 0 }}>Account created</h1>
              <p style={{ marginTop: 8, fontSize: 13, color: color.textFaint }}>You can now sign in.</p>
              <button
                onClick={() => navigate('/login')}
                className="pfx-btn pfx-btn-amber"
                style={{ marginTop: 22, width: '100%', fontSize: 13.5, fontWeight: 600, color: color.ink, background: color.amber, border: 'none', borderRadius: 9, padding: '12px 0', cursor: 'pointer' }}
              >
                Go to sign in
              </button>
            </div>
          ) : (
            <>
              <h1 style={{ fontFamily: font.display, fontSize: 18, fontWeight: 600, color: color.textPrimary, margin: 0 }}>Create an account</h1>
              <p style={{ marginTop: 4, fontSize: 13, color: color.textFaint }}>For advisers and paraplanners.</p>

              <form onSubmit={handleSubmit} style={{ marginTop: 22, display: 'flex', flexDirection: 'column', gap: 16 }}>
                <div>
                  <label style={labelStyle} htmlFor="full_name">Full name</label>
                  <input id="full_name" value={form.full_name} onChange={update('full_name')} style={inputStyle} />
                </div>
                <div>
                  <label style={labelStyle} htmlFor="firm_name">Firm name</label>
                  <input id="firm_name" value={form.firm_name} onChange={update('firm_name')} style={inputStyle} />
                </div>
                <div>
                  <label style={labelStyle} htmlFor="email">Email</label>
                  <input id="email" type="email" required autoComplete="email" value={form.email} onChange={update('email')} style={inputStyle} />
                </div>
                <div>
                  <label style={labelStyle} htmlFor="password">Password</label>
                  <input id="password" type="password" required minLength={6} autoComplete="new-password" value={form.password} onChange={update('password')} style={inputStyle} />
                </div>

                {error && <p style={{ fontSize: 13, color: '#e08787', margin: 0 }}>{error}</p>}

                <button
                  type="submit"
                  disabled={loading}
                  className="pfx-btn pfx-btn-amber"
                  style={{ width: '100%', fontSize: 13.5, fontWeight: 600, color: color.ink, background: color.amber, border: 'none', borderRadius: 9, padding: '12px 0', cursor: 'pointer', opacity: loading ? 0.7 : 1 }}
                >
                  {loading ? 'Creating…' : 'Create account'}
                </button>
              </form>
            </>
          )}
        </div>
        <p style={{ marginTop: 18, textAlign: 'center', fontSize: 13, color: color.textFaint }}>
          Already have an account? <Link to="/login" style={{ fontWeight: 500, color: color.teal }}>Sign in</Link>
        </p>
      </div>
    </div>
  )
}
