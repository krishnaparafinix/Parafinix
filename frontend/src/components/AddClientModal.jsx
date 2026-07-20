import { useState } from 'react'
import { createClient } from '../api/clients'
import { apiErrorMessage } from '../api/client'
import { color, font } from '../lib/theme'

const inputStyle = {
  width: '100%', boxSizing: 'border-box', background: color.bg, border: `1px solid ${color.borderRaised}`,
  borderRadius: 8, padding: '9px 12px', color: color.textPrimary, fontSize: 13, outline: 'none',
  fontFamily: font.body,
}
const labelStyle = { display: 'block', marginBottom: 6, fontSize: 11.5, color: color.textFaint }

export default function AddClientModal({ onClose, onCreated }) {
  const [form, setForm] = useState({ client_name: '', email: '', phone: '', segment: '', portfolio_value: '' })
  const [error, setError] = useState('')
  const [saving, setSaving] = useState(false)

  const update = (key) => (e) => setForm((f) => ({ ...f, [key]: e.target.value }))

  const handleSubmit = async (e) => {
    e.preventDefault()
    setError('')
    setSaving(true)
    try {
      const client = await createClient({
        client_name: form.client_name,
        email: form.email || null,
        phone: form.phone || null,
        segment: form.segment || null,
        portfolio_value: form.portfolio_value ? Number(form.portfolio_value) : null,
      })
      onCreated(client)
    } catch (err) {
      setError(apiErrorMessage(err, 'Could not create client.'))
    } finally {
      setSaving(false)
    }
  }

  return (
    <div onClick={onClose} style={{ position: 'fixed', inset: 0, zIndex: 70, background: 'rgba(9,10,12,0.72)', backdropFilter: 'blur(6px)', display: 'flex', alignItems: 'center', justifyContent: 'center', animation: 'pfx-fade 0.2s ease' }}>
      <div
        onClick={(e) => e.stopPropagation()}
        style={{ width: 440, maxWidth: 'calc(100vw - 40px)', background: 'linear-gradient(160deg,#181b1f,#131518)', border: `1px solid ${color.border}`, borderRadius: 16, padding: 28, boxShadow: '0 40px 90px -30px rgba(0,0,0,0.85)', animation: 'pfx-pop 0.28s cubic-bezier(.2,.7,.2,1)' }}
      >
        <h3 style={{ fontFamily: font.display, fontSize: 17, fontWeight: 600, color: color.textPrimary, margin: 0 }}>Add new client</h3>
        <form onSubmit={handleSubmit} style={{ marginTop: 18, display: 'flex', flexDirection: 'column', gap: 14 }}>
          <div>
            <label style={labelStyle}>Client name *</label>
            <input required value={form.client_name} onChange={update('client_name')} style={inputStyle} />
          </div>
          <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 12 }}>
            <div>
              <label style={labelStyle}>Email</label>
              <input type="email" value={form.email} onChange={update('email')} style={inputStyle} />
            </div>
            <div>
              <label style={labelStyle}>Phone</label>
              <input value={form.phone} onChange={update('phone')} style={inputStyle} />
            </div>
          </div>
          <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 12 }}>
            <div>
              <label style={labelStyle}>Segment</label>
              <input value={form.segment} onChange={update('segment')} style={inputStyle} />
            </div>
            <div>
              <label style={labelStyle}>Portfolio value</label>
              <input type="number" value={form.portfolio_value} onChange={update('portfolio_value')} style={{ ...inputStyle, fontFamily: font.mono }} />
            </div>
          </div>

          {error && <p style={{ fontSize: 12.5, color: '#e08787', margin: 0 }}>{error}</p>}

          <div style={{ display: 'flex', gap: 10, marginTop: 6 }}>
            <div className="pfx-btn pfx-btn-ghost" onClick={onClose} style={{ flex: 1, fontSize: 13, fontWeight: 500, color: color.textSecondary2, border: `1px solid ${color.borderRaised}`, borderRadius: 9, padding: '11px 0', textAlign: 'center', background: color.raised, cursor: 'pointer' }}>
              Cancel
            </div>
            <button type="submit" disabled={saving} className="pfx-btn pfx-btn-amber" style={{ flex: 1.3, fontSize: 13, fontWeight: 600, color: color.ink, background: color.amber, border: 'none', borderRadius: 9, padding: '11px 0', textAlign: 'center', cursor: 'pointer', opacity: saving ? 0.7 : 1 }}>
              {saving ? 'Creating…' : 'Create client'}
            </button>
          </div>
        </form>
      </div>
    </div>
  )
}
