import { useState } from 'react'
import { Link, useNavigate } from 'react-router-dom'
import { register } from '../api/auth'
import { apiErrorMessage } from '../api/client'
import { color, font } from '../lib/theme'

const fieldWrap = { border: `1px solid ${color.border}`, borderRadius: 10, background: color.bg, transition: 'border-color .16s ease, box-shadow .16s ease' }
const inputStyle = { width: '100%', boxSizing: 'border-box', border: 'none', outline: 'none', background: 'transparent', color: color.textPrimary, fontFamily: font.body, fontSize: 13.5, padding: '11px 13px' }
const microLabel = { fontFamily: font.mono, fontSize: 10, letterSpacing: '0.12em', textTransform: 'uppercase', color: color.textFainter, marginBottom: 7 }
const ROLES = ['Adviser', 'Paraplanner', 'Both']

export default function Register() {
  const navigate = useNavigate()
  const [form, setForm] = useState({ full_name: '', email: '', firm_name: '', frn: '', role: 'Adviser', password: '' })
  const [agreed, setAgreed] = useState(false)
  const [error, setError] = useState('')
  const [success, setSuccess] = useState(false)
  const [loading, setLoading] = useState(false)

  const update = (key) => (e) => setForm((f) => ({ ...f, [key]: e.target.value }))
  const canSubmit = form.full_name.trim() && form.email.trim() && form.password.length >= 10 && agreed

  const handleSubmit = async (e) => {
    e.preventDefault()
    if (!canSubmit) return
    setError('')
    setLoading(true)
    try {
      await register({ email: form.email, password: form.password, full_name: form.full_name, firm_name: form.firm_name })
      setSuccess(true)
    } catch (err) {
      setError(apiErrorMessage(err, 'Registration failed. Please try again.'))
    } finally {
      setLoading(false)
    }
  }

  return (
    <div style={{ minHeight: '100vh', position: 'relative', overflow: 'hidden', fontFamily: font.body, background: 'radial-gradient(1100px 620px at 50% -12%, rgba(95,208,196,0.10), transparent 62%),radial-gradient(900px 560px at 82% 118%, rgba(199,137,63,0.10), transparent 58%),#0d0f11', display: 'flex', flexDirection: 'column', alignItems: 'center' }}>
      <div style={{ position: 'absolute', inset: 0, pointerEvents: 'none', opacity: 0.5 }}>
        <div style={{ position: 'absolute', top: '22%', left: '8%', width: 220, height: 2, background: 'linear-gradient(90deg,transparent,#1b2422,transparent)' }} />
        <div style={{ position: 'absolute', top: '22%', left: 'calc(8% + 210px)', width: 8, height: 8, borderRadius: '50%', background: color.teal, opacity: 0.35, animation: 'pfx-drift 7s ease-in-out infinite' }} />
        <div style={{ position: 'absolute', bottom: '20%', right: '10%', width: 180, height: 2, background: 'linear-gradient(90deg,transparent,#241d14,transparent)' }} />
        <div style={{ position: 'absolute', bottom: '20%', right: '10%', width: 7, height: 7, borderRadius: '50%', background: color.amber, opacity: 0.4, animation: 'pfx-drift 9s ease-in-out infinite' }} />
      </div>

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
          Already have an account? <Link to="/login" className="pfx-link" style={{ fontWeight: 500 }}>Sign in</Link>
        </div>
      </div>

      <div style={{ flex: 1, display: 'flex', alignItems: 'center', justifyContent: 'center', width: '100%', padding: 24, position: 'relative', zIndex: 2 }}>
        <div style={{ width: 460, maxWidth: '100%', background: 'linear-gradient(165deg,#181b1f,#131518)', border: `1px solid ${color.border}`, borderRadius: 18, boxShadow: '0 40px 90px -34px rgba(0,0,0,0.85)', overflow: 'hidden', animation: 'pfx-fadeup 0.42s cubic-bezier(.2,.8,.2,1) both' }}>
          <div style={{ position: 'relative', height: 3, background: color.raised, overflow: 'hidden' }}>
            <div style={{ position: 'absolute', top: 0, left: 0, height: '100%', width: '38%', background: `linear-gradient(90deg,transparent,${color.teal},transparent)`, animation: 'pfx-linetravel 2.6s ease-in-out infinite' }} />
          </div>

          {success ? (
            <div style={{ padding: '34px 34px 30px', textAlign: 'center' }}>
              <h2 style={{ fontFamily: font.display, fontSize: 20, fontWeight: 600, color: color.textPrimary, margin: 0 }}>Account created</h2>
              <p style={{ marginTop: 8, fontSize: 13, color: color.textFaint }}>Your account is active — you can sign in now.</p>
              <button onClick={() => navigate('/login')} className="pfx-btn pfx-btn-teal" style={{ marginTop: 20, width: '100%', background: color.teal, color: color.ink, fontSize: 14, fontWeight: 600, border: 'none', borderRadius: 10, padding: '12px 0', cursor: 'pointer' }}>
                Go to sign in
              </button>
            </div>
          ) : (
            <div style={{ padding: '32px 34px 28px' }}>
              <div style={{ display: 'flex', alignItems: 'center', gap: 11, marginBottom: 20 }}>
                <div style={{ position: 'relative', width: 120, height: 14, display: 'flex', alignItems: 'center', flex: '0 0 auto' }}>
                  <div style={{ position: 'absolute', left: 2, right: 2, height: 2, background: color.borderRaised, borderRadius: 2 }} />
                  <div style={{ position: 'absolute', left: 0, top: '50%', transform: 'translateY(-50%)', width: 7, height: 7, borderRadius: '50%', background: color.teal }} />
                  <div style={{ position: 'absolute', left: '50%', top: '50%', transform: 'translate(-50%,-50%)', width: 6, height: 6, borderRadius: '50%', background: color.amber }} />
                  <div style={{ position: 'absolute', right: 0, top: '50%', width: 8, height: 8, borderRadius: '50%', background: color.teal, animation: 'pfx-nodepulse 1.4s ease-in-out infinite' }} />
                  <div style={{ position: 'absolute', top: '50%', transform: 'translateY(-50%)', width: 6, height: 6, borderRadius: '50%', background: color.teal, boxShadow: `0 0 8px ${color.teal}`, animation: 'pfx-dot 1.7s ease-in-out infinite' }} />
                </div>
                <span style={microLabel}>Request access</span>
              </div>

              <h2 style={{ fontFamily: font.display, fontSize: 23, fontWeight: 600, color: color.textPrimary, margin: 0, letterSpacing: '-0.01em' }}>Create your account</h2>
              <p style={{ margin: '7px 0 22px', fontSize: 13, color: color.textFaint }}>For UK regulated advisers &amp; paraplanners.</p>

              <form onSubmit={handleSubmit} style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '14px 16px' }}>
                <div style={{ gridColumn: 'span 2' }}>
                  <div style={microLabel}>Full name</div>
                  <div className="pfx-field" style={fieldWrap}><input required value={form.full_name} onChange={update('full_name')} placeholder="Eleanor Whitfield" style={inputStyle} /></div>
                </div>
                <div style={{ gridColumn: 'span 2' }}>
                  <div style={microLabel}>Work email</div>
                  <div className="pfx-field" style={fieldWrap}><input type="email" required value={form.email} onChange={update('email')} placeholder="j.mercer@firm.co.uk" style={inputStyle} /></div>
                </div>
                <div>
                  <div style={microLabel}>Firm</div>
                  <div className="pfx-field" style={fieldWrap}><input value={form.firm_name} onChange={update('firm_name')} placeholder="Firm name" style={inputStyle} /></div>
                </div>
                <div>
                  <div style={microLabel}>FCA / FRN</div>
                  <div className="pfx-field" style={fieldWrap}><input value={form.frn} onChange={update('frn')} placeholder="e.g. 123456" style={{ ...inputStyle, fontFamily: font.mono }} /></div>
                </div>
                <div style={{ gridColumn: 'span 2' }}>
                  <div style={microLabel}>Your role</div>
                  <div style={{ display: 'flex', gap: 8 }}>
                    {ROLES.map((r) => {
                      const on = form.role === r
                      return (
                        <div
                          key={r}
                          className="pfx-chip"
                          onClick={() => setForm((f) => ({ ...f, role: r }))}
                          style={{ flex: 1, textAlign: 'center', fontSize: 12.5, color: on ? color.textSecondary : color.textMuted, background: on ? '#1b2422' : 'transparent', border: `1px solid ${on ? color.teal : color.borderRaised}`, borderRadius: 9, padding: '9px 0', cursor: 'pointer' }}
                        >
                          {r}
                        </div>
                      )
                    })}
                  </div>
                </div>
                <div style={{ gridColumn: 'span 2' }}>
                  <div style={microLabel}>Password</div>
                  <div className="pfx-field" style={fieldWrap}><input type="password" required minLength={10} value={form.password} onChange={update('password')} placeholder="At least 10 characters" style={inputStyle} /></div>
                </div>

                <label style={{ gridColumn: 'span 2', display: 'flex', alignItems: 'flex-start', gap: 9, fontSize: 12, color: color.textMuted, cursor: 'pointer', userSelect: 'none', marginTop: 2, lineHeight: 1.5 }}>
                  <input type="checkbox" checked={agreed} onChange={(e) => setAgreed(e.target.checked)} style={{ marginTop: 3, accentColor: color.teal }} />
                  I confirm I'm authorised to act for regulated clients and agree to the <a href="#" className="pfx-link" onClick={(e) => e.preventDefault()}>Terms</a> &amp; <a href="#" className="pfx-link" onClick={(e) => e.preventDefault()}>Privacy Policy</a>.
                </label>

                {error && <p style={{ gridColumn: 'span 2', fontSize: 12.5, color: '#e08787', margin: 0 }}>{error}</p>}

                <button type="submit" disabled={!canSubmit || loading} className="pfx-btn pfx-btn-teal" style={{ gridColumn: 'span 2', display: 'block', textAlign: 'center', background: color.teal, color: color.ink, fontSize: 14, fontWeight: 600, border: 'none', borderRadius: 10, padding: '12px 0', marginTop: 6, cursor: canSubmit ? 'pointer' : 'default', opacity: canSubmit && !loading ? 1 : 0.5 }}>
                  {loading ? 'Creating…' : 'Request access'}
                </button>
              </form>
            </div>
          )}

          <div style={{ padding: '14px 34px', borderTop: `1px solid ${color.borderSubtle}`, background: '#111316', textAlign: 'center', fontSize: 11, color: color.textFaintest, lineHeight: 1.5 }}>
            {success ? 'Welcome to Parafinix.' : 'Accounts activate immediately — no manual approval step yet.'}
          </div>
        </div>
      </div>

      <div style={{ padding: '0 32px 26px', fontSize: 11.5, color: color.textFaintest, fontFamily: font.mono, position: 'relative', zIndex: 2 }}>
        FCA-aligned · UK data residency · SOC 2
      </div>
    </div>
  )
}
