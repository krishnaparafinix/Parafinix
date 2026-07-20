import { useState } from 'react'
import { Link, useLocation, useNavigate } from 'react-router-dom'
import { useAuth } from '../context/AuthContext'
import { forgotPassword } from '../api/auth'
import { apiErrorMessage } from '../api/client'
import { color, font } from '../lib/theme'

const fieldWrap = { border: `1px solid ${color.border}`, borderRadius: 10, background: color.bg, transition: 'border-color .16s ease, box-shadow .16s ease' }
const inputStyle = { width: '100%', boxSizing: 'border-box', border: 'none', outline: 'none', background: 'transparent', color: color.textPrimary, fontFamily: font.body, fontSize: 13.5, padding: '11px 13px' }
const microLabel = { fontFamily: font.mono, fontSize: 10, letterSpacing: '0.12em', textTransform: 'uppercase', color: color.textFainter }

function PipelineMotif({ label }) {
  return (
    <div style={{ display: 'flex', alignItems: 'center', gap: 11, marginBottom: 22 }}>
      <div style={{ position: 'relative', width: 120, height: 14, display: 'flex', alignItems: 'center', flex: '0 0 auto' }}>
        <div style={{ position: 'absolute', left: 2, right: 2, height: 2, background: color.borderRaised, borderRadius: 2 }} />
        <div style={{ position: 'absolute', left: 0, top: '50%', transform: 'translateY(-50%)', width: 7, height: 7, borderRadius: '50%', background: color.teal }} />
        <div style={{ position: 'absolute', left: '50%', top: '50%', transform: 'translate(-50%,-50%)', width: 6, height: 6, borderRadius: '50%', background: color.amber }} />
        <div style={{ position: 'absolute', right: 0, top: '50%', width: 8, height: 8, borderRadius: '50%', background: color.teal, animation: 'pfx-nodepulse 1.4s ease-in-out infinite' }} />
        <div style={{ position: 'absolute', top: '50%', transform: 'translateY(-50%)', width: 6, height: 6, borderRadius: '50%', background: color.teal, boxShadow: `0 0 8px ${color.teal}`, animation: 'pfx-dot 1.7s ease-in-out infinite' }} />
      </div>
      <span style={microLabel}>{label}</span>
    </div>
  )
}

function AuthBackdrop() {
  return (
    <div style={{ position: 'absolute', inset: 0, pointerEvents: 'none', opacity: 0.5 }}>
      <div style={{ position: 'absolute', top: '22%', left: '8%', width: 220, height: 2, background: 'linear-gradient(90deg,transparent,#1b2422,transparent)' }} />
      <div style={{ position: 'absolute', top: '22%', left: 'calc(8% + 210px)', width: 8, height: 8, borderRadius: '50%', background: color.teal, opacity: 0.35, animation: 'pfx-drift 7s ease-in-out infinite' }} />
      <div style={{ position: 'absolute', bottom: '20%', right: '10%', width: 180, height: 2, background: 'linear-gradient(90deg,transparent,#241d14,transparent)' }} />
      <div style={{ position: 'absolute', bottom: '20%', right: '10%', width: 7, height: 7, borderRadius: '50%', background: color.amber, opacity: 0.4, animation: 'pfx-drift 9s ease-in-out infinite' }} />
    </div>
  )
}

function TopBar({ prompt, linkLabel, linkTo }) {
  return (
    <div style={{ width: '100%', maxWidth: 1180, display: 'flex', alignItems: 'center', justifyContent: 'space-between', padding: '28px 32px', position: 'relative', zIndex: 2 }}>
      <div className="pfx-logo" style={{ display: 'flex', alignItems: 'center', gap: 12 }}>
        <div style={{ width: 38, height: 38, borderRadius: 10, background: color.card, border: `1px solid ${color.borderRaised}`, display: 'flex', alignItems: 'center', justifyContent: 'center', gap: 2.5 }}>
          <div className="pfx-w1" style={{ width: 4, height: 14, background: color.teal, borderRadius: 2, transform: 'skewX(-14deg) scaleY(0.72)' }} />
          <div className="pfx-w2" style={{ width: 4, height: 21, background: color.textSecondary, borderRadius: 2, transform: 'skewX(-14deg)' }} />
          <div className="pfx-w3" style={{ width: 4, height: 14, background: color.amber, borderRadius: 2, transform: 'skewX(-14deg)' }} />
        </div>
        <span style={{ fontFamily: font.display, fontSize: 17, fontWeight: 600, color: color.textPrimary, letterSpacing: '-0.01em' }}>
          parafinix<span style={{ color: color.teal }}>.ai</span>
        </span>
      </div>
      <div style={{ fontSize: 12.5, color: color.textFaint }}>
        {prompt} <Link to={linkTo} className="pfx-link" style={{ fontWeight: 500 }}>{linkLabel}</Link>
      </div>
    </div>
  )
}

function DecorativeCheckbox({ label }) {
  return (
    <label style={{ display: 'flex', alignItems: 'center', gap: 9, fontSize: 12.5, color: color.textMuted, cursor: 'default', userSelect: 'none' }}>
      <span style={{ width: 16, height: 16, borderRadius: 4, border: `1px solid ${color.borderRaised}`, background: color.card, display: 'inline-flex', alignItems: 'center', justifyContent: 'center', flex: '0 0 auto' }}>
        <span style={{ width: 8, height: 8, borderRadius: 2, background: color.teal }} />
      </span>
      {label}
    </label>
  )
}

export default function Login() {
  const { login } = useAuth()
  const navigate = useNavigate()
  const location = useLocation()
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [error, setError] = useState('')
  const [notice, setNotice] = useState('')
  const [loading, setLoading] = useState(false)
  const [resetting, setResetting] = useState(false)

  const handleSubmit = async (e) => {
    e.preventDefault()
    setError('')
    setNotice('')
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

  const handleForgot = async (e) => {
    e.preventDefault()
    if (!email.trim()) { setError('Enter your email above first, then click "Forgot?".'); return }
    setError('')
    setResetting(true)
    try {
      const res = await forgotPassword(email)
      setNotice(res.message)
    } catch (err) {
      setError(apiErrorMessage(err, 'Could not send a reset link.'))
    } finally {
      setResetting(false)
    }
  }

  return (
    <div style={{ minHeight: '100vh', position: 'relative', overflow: 'hidden', fontFamily: font.body, background: 'radial-gradient(1100px 620px at 50% -12%, rgba(95,208,196,0.10), transparent 62%),radial-gradient(900px 560px at 82% 118%, rgba(199,137,63,0.10), transparent 58%),#0d0f11', display: 'flex', flexDirection: 'column', alignItems: 'center' }}>
      <AuthBackdrop />
      <TopBar prompt="New here?" linkLabel="Request access" linkTo="/register" />

      <div style={{ flex: 1, display: 'flex', alignItems: 'center', justifyContent: 'center', width: '100%', padding: 24, position: 'relative', zIndex: 2 }}>
        <div style={{ width: 412, maxWidth: '100%', background: 'linear-gradient(165deg,#181b1f,#131518)', border: `1px solid ${color.border}`, borderRadius: 18, boxShadow: '0 40px 90px -34px rgba(0,0,0,0.85)', overflow: 'hidden', animation: 'pfx-fadeup 0.42s cubic-bezier(.2,.8,.2,1) both' }}>
          <div style={{ position: 'relative', height: 3, background: color.raised, overflow: 'hidden' }}>
            <div style={{ position: 'absolute', top: 0, left: 0, height: '100%', width: '38%', background: `linear-gradient(90deg,transparent,${color.teal},transparent)`, animation: 'pfx-linetravel 2.6s ease-in-out infinite' }} />
          </div>

          <div style={{ padding: '34px 34px 30px' }}>
            <PipelineMotif label="Your report wingman" />

            <h2 style={{ fontFamily: font.display, fontSize: 23, fontWeight: 600, color: color.textPrimary, margin: 0, letterSpacing: '-0.01em' }}>Sign in to Parafinix</h2>
            <p style={{ margin: '7px 0 24px', fontSize: 13, color: color.textFaint }}>Welcome back. Enter your details to continue.</p>

            <div
              className="pfx-sso"
              onClick={() => setNotice('Single sign-on is not yet configured for this workspace — use your email and password below.')}
              style={{ display: 'flex', alignItems: 'center', justifyContent: 'center', gap: 10, border: `1px solid ${color.borderRaised}`, borderRadius: 10, padding: '11px 0', background: color.card, color: color.textSecondary, fontSize: 13.5, fontWeight: 500, cursor: 'pointer' }}
            >
              <span style={{ width: 16, height: 16, borderRadius: 4, background: color.amber, display: 'inline-block' }} />
              Continue with your firm's SSO
            </div>

            <div style={{ display: 'flex', alignItems: 'center', gap: 12, margin: '18px 0' }}>
              <div style={{ flex: 1, height: 1, background: color.borderSubtle }} />
              <span style={{ fontSize: 11, color: color.textFainter, fontFamily: font.mono }}>OR</span>
              <div style={{ flex: 1, height: 1, background: color.borderSubtle }} />
            </div>

            <form onSubmit={handleSubmit} style={{ display: 'flex', flexDirection: 'column', gap: 15 }}>
              <div>
                <div style={{ ...microLabel, marginBottom: 7 }}>Work email</div>
                <div className="pfx-field" style={fieldWrap}>
                  <input type="email" required autoComplete="email" placeholder="j.mercer@firm.co.uk" value={email} onChange={(e) => setEmail(e.target.value)} style={inputStyle} />
                </div>
              </div>
              <div>
                <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: 7 }}>
                  <div style={microLabel}>Password</div>
                  <a href="#" className="pfx-link" onClick={handleForgot} style={{ fontSize: 11.5, opacity: resetting ? 0.6 : 1 }}>{resetting ? 'Sending…' : 'Forgot?'}</a>
                </div>
                <div className="pfx-field" style={fieldWrap}>
                  <input type="password" required autoComplete="current-password" placeholder="••••••••••" value={password} onChange={(e) => setPassword(e.target.value)} style={inputStyle} />
                </div>
              </div>

              <DecorativeCheckbox label="Keep me signed in on this device" />

              {notice && <p style={{ fontSize: 12.5, color: color.teal, margin: 0 }}>{notice}</p>}
              {error && <p style={{ fontSize: 12.5, color: '#e08787', margin: 0 }}>{error}</p>}

              <button type="submit" disabled={loading} className="pfx-btn pfx-btn-teal" style={{ display: 'block', width: '100%', textAlign: 'center', background: color.teal, color: color.ink, fontSize: 14, fontWeight: 600, border: 'none', borderRadius: 10, padding: '12px 0', marginTop: 3, cursor: 'pointer', opacity: loading ? 0.7 : 1 }}>
                {loading ? 'Signing in…' : 'Sign in'}
              </button>
            </form>
          </div>

          <div style={{ padding: '14px 34px', borderTop: `1px solid ${color.borderSubtle}`, background: '#111316', textAlign: 'center', fontSize: 11, color: color.textFaintest, lineHeight: 1.5 }}>
            Encrypted in transit &amp; at rest · <a href="#" className="pfx-link" onClick={(e) => e.preventDefault()}>Terms</a> · <a href="#" className="pfx-link" onClick={(e) => e.preventDefault()}>Privacy</a>
          </div>
        </div>
      </div>

      <div style={{ padding: '0 32px 26px', fontSize: 11.5, color: color.textFaintest, fontFamily: font.mono, position: 'relative', zIndex: 2 }}>
        FCA-aligned · UK data residency · SOC 2
      </div>
    </div>
  )
}
