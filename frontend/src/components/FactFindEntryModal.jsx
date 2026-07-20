import { useRef, useState } from 'react'
import { uploadPdf, extractFactFind } from '../api/generate'
import { apiErrorMessage } from '../api/client'
import { color, font } from '../lib/theme'

export default function FactFindEntryModal({ onClose, onExtracted }) {
  const [mode, setMode] = useState('paste') // 'paste' | 'upload'
  const [notes, setNotes] = useState('')
  const [busy, setBusy] = useState(false)
  const [error, setError] = useState('')
  const fileRef = useRef(null)

  const runExtract = async (rawNotes) => {
    setBusy(true)
    setError('')
    try {
      const { data, flags } = await extractFactFind(rawNotes)
      onExtracted({ data, flags })
    } catch (err) {
      setError(apiErrorMessage(err, 'Extraction failed. Please try again.'))
    } finally {
      setBusy(false)
    }
  }

  const handleFile = async (file) => {
    setBusy(true)
    setError('')
    try {
      const uploaded = await uploadPdf(file)
      if (!uploaded.success || !uploaded.extracted_text?.trim()) {
        throw new Error('Could not read any text from that PDF. Try pasting the notes instead.')
      }
      await runExtract(uploaded.extracted_text)
    } catch (err) {
      setError(apiErrorMessage(err, 'Upload failed. Please try again.'))
      setBusy(false)
    }
  }

  const tabStyle = (active) => ({
    fontSize: 12.5, padding: '7px 14px', borderRadius: 20, cursor: 'pointer',
    border: `1px solid ${active ? color.teal : color.borderRaised}`,
    background: active ? '#1b2422' : 'transparent',
    color: active ? color.textSecondary : color.textMuted,
  })

  return (
    <div onClick={busy ? undefined : onClose} style={{ position: 'fixed', inset: 0, zIndex: 70, background: 'rgba(9,10,12,0.72)', backdropFilter: 'blur(6px)', display: 'flex', alignItems: 'center', justifyContent: 'center', animation: 'pfx-fade 0.2s ease' }}>
      <div onClick={(e) => e.stopPropagation()} style={{ width: 520, maxWidth: 'calc(100vw - 40px)', background: 'linear-gradient(160deg,#181b1f,#131518)', border: `1px solid ${color.border}`, borderRadius: 16, padding: 28, boxShadow: '0 40px 90px -30px rgba(0,0,0,0.85)', animation: 'pfx-pop 0.28s cubic-bezier(.2,.7,.2,1)' }}>
        <h3 style={{ fontFamily: font.display, fontSize: 17, fontWeight: 600, color: color.textPrimary, margin: 0 }}>Add fact-find data</h3>
        <p style={{ fontSize: 12.5, color: color.textFaint, marginTop: 6 }}>Paste raw meeting notes, or upload a fact-find PDF — Parafinix AI extracts the structured data.</p>

        <div style={{ display: 'flex', gap: 8, marginTop: 16 }}>
          <div style={tabStyle(mode === 'paste')} onClick={() => setMode('paste')}>Paste notes</div>
          <div style={tabStyle(mode === 'upload')} onClick={() => setMode('upload')}>Upload PDF</div>
        </div>

        {mode === 'paste' ? (
          <>
            <textarea
              rows={8}
              value={notes}
              onChange={(e) => setNotes(e.target.value)}
              disabled={busy}
              placeholder="Paste raw meeting notes here…"
              style={{ width: '100%', boxSizing: 'border-box', marginTop: 14, background: color.bg, border: `1px solid ${color.borderRaised}`, borderRadius: 9, padding: '10px 12px', color: color.textPrimary, fontSize: 13, outline: 'none', fontFamily: font.body, resize: 'vertical' }}
            />
            <div style={{ display: 'flex', gap: 10, marginTop: 16 }}>
              <div className="pfx-btn pfx-btn-ghost" onClick={onClose} style={{ flex: 1, fontSize: 13, fontWeight: 500, color: color.textSecondary2, border: `1px solid ${color.borderRaised}`, borderRadius: 9, padding: '11px 0', textAlign: 'center', background: color.raised, cursor: 'pointer' }}>Cancel</div>
              <div
                className="pfx-btn pfx-btn-teal"
                onClick={() => !busy && notes.trim() && runExtract(notes)}
                style={{ flex: 1.4, fontSize: 13, fontWeight: 600, color: color.ink, background: color.teal, borderRadius: 9, padding: '11px 0', textAlign: 'center', cursor: notes.trim() && !busy ? 'pointer' : 'default', opacity: notes.trim() && !busy ? 1 : 0.5 }}
              >
                {busy ? 'Extracting…' : 'Extract data'}
              </div>
            </div>
          </>
        ) : (
          <>
            <div
              onClick={() => !busy && fileRef.current?.click()}
              style={{ marginTop: 14, border: `2px dashed ${color.borderRaised}`, borderRadius: 12, padding: 30, textAlign: 'center', cursor: busy ? 'default' : 'pointer', background: color.bg }}
            >
              <div style={{ fontSize: 13, color: color.textSecondary }}>{busy ? 'Reading document…' : 'Click to choose a PDF'}</div>
              <div style={{ fontSize: 11.5, color: color.textFainter, marginTop: 4 }}>Typed/digital fact-find PDFs only — no OCR for scans</div>
              <input ref={fileRef} type="file" accept=".pdf" disabled={busy} onChange={(e) => e.target.files[0] && handleFile(e.target.files[0])} style={{ display: 'none' }} />
            </div>
            <div style={{ display: 'flex', gap: 10, marginTop: 16 }}>
              <div className="pfx-btn pfx-btn-ghost" onClick={onClose} style={{ flex: 1, fontSize: 13, fontWeight: 500, color: color.textSecondary2, border: `1px solid ${color.borderRaised}`, borderRadius: 9, padding: '11px 0', textAlign: 'center', background: color.raised, cursor: 'pointer' }}>Cancel</div>
            </div>
          </>
        )}

        {error && <p style={{ fontSize: 12.5, color: '#e08787', marginTop: 12 }}>{error}</p>}
      </div>
    </div>
  )
}
