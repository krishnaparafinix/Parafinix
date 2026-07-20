import { useState } from 'react'
import { createClient } from '../api/clients'
import { saveClientMeta } from '../lib/localClientMeta'
import { apiErrorMessage } from '../api/client'
import { color, font } from '../lib/theme'

const fieldWrapStyle = { border: `1px solid ${color.border}`, borderRadius: 9, background: color.bg, transition: 'border-color .16s ease, box-shadow .16s ease' }
const inputStyle = { width: '100%', boxSizing: 'border-box', border: 'none', outline: 'none', background: 'transparent', color: color.textPrimary, fontFamily: font.body, fontSize: 13.5, padding: '10px 12px' }
const labelStyle = { fontFamily: font.mono, fontSize: 10, letterSpacing: '0.12em', textTransform: 'uppercase', color: color.textFainter, marginBottom: 6 }
const STATUS_OPTIONS = ['Active', 'Prospect', 'Review due']

function parseMoney(v) {
  const n = Number(String(v).replace(/[£,\s]/g, ''))
  return Number.isFinite(n) && v.trim() !== '' ? n : null
}

export default function AddClientModal({ onClose, onCreated }) {
  const [form, setForm] = useState({ name: '', objective: '', risk: '', portfolio: '', review: '', status: 'Active' })
  const [error, setError] = useState('')
  const [saving, setSaving] = useState(false)

  const set = (key) => (e) => setForm((f) => ({ ...f, [key]: e.target.value }))
  const canSave = form.name.trim().length > 0

  const handleSave = async () => {
    if (!canSave || saving) return
    setError('')
    setSaving(true)
    try {
      const client = await createClient({
        client_name: form.name.trim(),
        portfolio_value: parseMoney(form.portfolio),
      })
      saveClientMeta(client.id, {
        objective: form.objective.trim() || null,
        risk: form.risk.trim() || null,
        next_review: form.review.trim() || null,
        status: form.status,
      })
      onCreated(client)
    } catch (err) {
      setError(apiErrorMessage(err, 'Could not create client.'))
    } finally {
      setSaving(false)
    }
  }

  return (
    <div onClick={onClose} style={{ position: 'fixed', inset: 0, zIndex: 70, background: 'rgba(9,10,12,0.72)', backdropFilter: 'blur(6px)', display: 'flex', alignItems: 'center', justifyContent: 'center', animation: 'pfx-fade 0.2s ease', padding: 24 }}>
      <div
        onClick={(e) => e.stopPropagation()}
        style={{ width: 520, maxWidth: '100%', maxHeight: 'calc(100vh - 48px)', overflow: 'auto', background: 'linear-gradient(160deg,#181b1f,#131518)', border: `1px solid ${color.border}`, borderRadius: 16, boxShadow: '0 40px 90px -30px rgba(0,0,0,0.85)', animation: 'pfx-pop 0.3s cubic-bezier(.2,.8,.2,1)' }}
      >
        <div style={{ display: 'flex', alignItems: 'center', gap: 14, padding: '22px 24px', borderBottom: `1px solid ${color.borderSubtle}` }}>
          <div style={{ width: 42, height: 42, borderRadius: 11, background: color.amberSoftBg, border: `1px solid ${color.amberSoftBorder}`, display: 'flex', alignItems: 'center', justifyContent: 'center', fontFamily: font.mono, fontSize: 16, fontWeight: 700, color: color.amber, flex: '0 0 auto' }}>+</div>
          <div style={{ flex: 1 }}>
            <div style={{ fontFamily: font.display, fontSize: 17, fontWeight: 600, color: color.textPrimary }}>Add client</div>
            <div style={{ fontSize: 12, color: color.textFaint, marginTop: 2 }}>A reference is assigned automatically. You can complete the fact-find later.</div>
          </div>
          <div className="pfx-btn pfx-btn-ghost" onClick={onClose} style={{ width: 32, height: 32, display: 'flex', alignItems: 'center', justifyContent: 'center', fontSize: 16, color: color.textSecondary2, border: `1px solid ${color.borderRaised}`, borderRadius: 9, background: color.raised, cursor: 'pointer', flex: '0 0 auto' }}>✕</div>
        </div>

        <div style={{ padding: '22px 24px', display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '16px 18px' }}>
          <div style={{ gridColumn: 'span 2' }}>
            <div style={labelStyle}>Full name</div>
            <div className="pfx-field" style={fieldWrapStyle}><input value={form.name} onChange={set('name')} placeholder="e.g. Eleanor Whitfield" style={inputStyle} /></div>
          </div>
          <div>
            <div style={labelStyle}>Objective</div>
            <div className="pfx-field" style={fieldWrapStyle}><input value={form.objective} onChange={set('objective')} placeholder="e.g. Retirement income" style={inputStyle} /></div>
          </div>
          <div>
            <div style={labelStyle}>Risk profile</div>
            <div className="pfx-field" style={fieldWrapStyle}><input value={form.risk} onChange={set('risk')} placeholder="e.g. 4 · Balanced" style={inputStyle} /></div>
          </div>
          <div>
            <div style={labelStyle}>Portfolio</div>
            <div className="pfx-field" style={fieldWrapStyle}><input value={form.portfolio} onChange={set('portfolio')} placeholder="e.g. £250,000" style={{ ...inputStyle, fontFamily: font.mono }} /></div>
          </div>
          <div>
            <div style={labelStyle}>Next review</div>
            <div className="pfx-field" style={fieldWrapStyle}><input value={form.review} onChange={set('review')} placeholder="e.g. Aug 2026 or —" style={{ ...inputStyle, fontFamily: font.mono }} /></div>
          </div>
          <div style={{ gridColumn: 'span 2' }}>
            <div style={labelStyle}>Status</div>
            <div style={{ display: 'flex', gap: 8 }}>
              {STATUS_OPTIONS.map((s) => {
                const on = form.status === s
                return (
                  <div
                    key={s}
                    className="pfx-chip"
                    onClick={() => setForm((f) => ({ ...f, status: s }))}
                    style={{ fontSize: 12, borderRadius: 20, padding: '7px 14px', border: `1px solid ${on ? color.teal : color.borderRaised}`, background: on ? '#1b2422' : 'transparent', color: on ? color.textSecondary : color.textMuted, cursor: 'pointer' }}
                  >
                    {s}
                  </div>
                )
              })}
            </div>
          </div>
          {error && <p style={{ gridColumn: 'span 2', fontSize: 12.5, color: '#e08787', margin: 0 }}>{error}</p>}
        </div>

        <div style={{ padding: '16px 24px', borderTop: `1px solid ${color.borderSubtle}`, display: 'flex', gap: 10, justifyContent: 'flex-end' }}>
          <div className="pfx-btn pfx-btn-ghost" onClick={onClose} style={{ fontSize: 13, fontWeight: 500, color: color.textSecondary2, border: `1px solid ${color.borderRaised}`, borderRadius: 9, padding: '10px 18px', background: color.raised, cursor: 'pointer' }}>Cancel</div>
          <div
            className="pfx-btn pfx-btn-amber"
            onClick={handleSave}
            style={{ fontSize: 13, fontWeight: 600, color: color.ink, background: color.amber, borderRadius: 9, padding: '10px 20px', cursor: canSave && !saving ? 'pointer' : 'default', opacity: canSave && !saving ? 1 : 0.5 }}
          >
            {saving ? 'Creating…' : 'Add client'}
          </div>
        </div>
      </div>
    </div>
  )
}
