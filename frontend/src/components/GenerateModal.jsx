import { useEffect, useRef, useState } from 'react'
import { color, font, docAccent } from '../lib/theme'
import { apiErrorMessage } from '../api/client'

const STEPS = ['Reading meeting notes', 'Extracting client data', 'Drafting sections', 'Running compliance checks', 'Finalising document']

// The backend has no streaming progress endpoint — generation is one blocking
// call. This drives the step choreography up to ~92% on an estimated timer,
// then holds there for real until `task` actually resolves, so the modal
// never lies about being "done" before the API call returns.
const EST_DURATION_MS = { factfind: 5000, suitability: 100000, compliance: 18000 }

export default function GenerateModal({ docKey, title, subtitle, task, onClose, onDone }) {
  const [phase, setPhase] = useState('running') // running | done | error
  const [pct, setPct] = useState(0)
  const [stepIdx, setStepIdx] = useState(0)
  const [error, setError] = useState('')
  const timer = useRef(null)
  const ranTask = useRef(false)

  const d = docAccent[docKey] || docAccent.suitability

  useEffect(() => {
    const total = EST_DURATION_MS[docKey] || 60000
    const t0 = Date.now()
    timer.current = setInterval(() => {
      const elapsed = Date.now() - t0
      const p = Math.min(92, Math.round((elapsed / total) * 100))
      const idx = Math.min(STEPS.length - 1, Math.floor((p / 100) * STEPS.length))
      setPct((prev) => (prev >= 100 ? prev : p))
      setStepIdx((prev) => (prev >= STEPS.length ? prev : idx))
    }, 120)

    if (!ranTask.current) {
      ranTask.current = true
      task()
        .then((result) => {
          clearInterval(timer.current)
          setPct(100)
          setStepIdx(STEPS.length)
          setPhase('done')
          onDone?.(result)
        })
        .catch((err) => {
          clearInterval(timer.current)
          setPhase('error')
          setError(apiErrorMessage(err, 'Something went wrong.'))
        })
    }
    return () => clearInterval(timer.current)
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [])

  const running = phase === 'running'
  const done = phase === 'done'
  const failed = phase === 'error'

  const steps = STEPS.map((label, i) => {
    const complete = i < stepIdx || done
    const active = i === stepIdx && running
    let dotStyle, dotGlyph = '', textColor = '#5a6067'
    if (complete) {
      textColor = '#e7e9ea'
      dotGlyph = '✓'
      dotStyle = { width: 18, height: 18, borderRadius: '50%', background: d.accent, color: color.ink, display: 'flex', alignItems: 'center', justifyContent: 'center', fontSize: 11, fontWeight: 700, flex: '0 0 auto' }
    } else if (active) {
      textColor = color.textPrimary
      dotStyle = { width: 18, height: 18, borderRadius: '50%', border: `2px solid ${d.accent}`, boxShadow: `0 0 0 4px ${d.soft}`, flex: '0 0 auto' }
    } else {
      dotStyle = { width: 18, height: 18, borderRadius: '50%', border: `2px solid ${color.borderRaised}`, flex: '0 0 auto' }
    }
    return { label, dotGlyph, dotStyle, textColor }
  })

  return (
    <div style={{ position: 'fixed', inset: 0, zIndex: 50, background: 'rgba(9,10,12,0.72)', backdropFilter: 'blur(6px)', display: 'flex', alignItems: 'center', justifyContent: 'center', animation: 'pfx-fade 0.2s ease' }}>
      <div style={{ width: 440, maxWidth: 'calc(100vw - 40px)', background: 'linear-gradient(160deg,#181b1f,#131518)', border: `1px solid ${d.border}`, borderRadius: 16, padding: 28, boxShadow: '0 40px 90px -30px rgba(0,0,0,0.85)', animation: 'pfx-pop 0.28s cubic-bezier(.2,.7,.2,1)' }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: 14 }}>
          <div style={{ width: 46, height: 46, borderRadius: 11, background: d.soft, border: `1px solid ${d.border}`, display: 'flex', alignItems: 'center', justifyContent: 'center', fontFamily: font.mono, fontSize: 14, fontWeight: 700, color: d.accent, position: 'relative' }}>
            {done ? (
              <svg width="24" height="24" viewBox="0 0 24 24" fill="none"><path d="M5 12.5l4.5 4.5L19 7.5" stroke={d.accent} strokeWidth="2.4" strokeLinecap="round" strokeLinejoin="round" style={{ strokeDasharray: 26, animation: 'pfx-check 0.4s ease forwards' }} /></svg>
            ) : failed ? '!' : (
              <span style={{ position: 'relative', display: 'flex', alignItems: 'center', justifyContent: 'center', width: '100%', height: '100%' }}>
                <span style={{ position: 'absolute', width: 26, height: 26, border: `2.5px solid ${d.border}`, borderTopColor: d.accent, borderRadius: '50%', animation: 'pfx-spin 0.8s linear infinite' }} />
                <span style={{ fontSize: 11 }}>{d.code}</span>
              </span>
            )}
          </div>
          <div style={{ flex: 1 }}>
            <div style={{ fontFamily: font.display, fontSize: 17, fontWeight: 600, color: color.textPrimary }}>
              {failed ? `${title} failed` : done ? `${title} ready` : `Generating ${title}`}
            </div>
            <div style={{ fontSize: 12, color: color.textFaint, marginTop: 2 }}>
              {failed ? error : done ? subtitle.done : subtitle.running}
            </div>
          </div>
          {!failed && <div style={{ fontFamily: font.mono, fontSize: 20, fontWeight: 600, color: d.accent }}>{pct}%</div>}
        </div>

        {!failed && (
          <div style={{ height: 6, borderRadius: 4, background: color.borderSubtle, margin: '22px 0 20px', overflow: 'hidden', position: 'relative' }}>
            <div style={{ height: '100%', width: `${pct}%`, background: `linear-gradient(90deg,${d.accent},${d.accent2})`, borderRadius: 4, transition: 'width 0.4s cubic-bezier(.4,0,.2,1)', position: 'relative', overflow: 'hidden' }}>
              {running && <span style={{ position: 'absolute', top: 0, left: 0, width: '40%', height: '100%', background: 'linear-gradient(90deg,transparent,rgba(255,255,255,0.5),transparent)', animation: 'pfx-scan 1.1s ease-in-out infinite' }} />}
            </div>
          </div>
        )}

        {!failed && (
          <div style={{ display: 'flex', flexDirection: 'column', gap: 11 }}>
            {steps.map((st) => (
              <div key={st.label} style={{ display: 'flex', alignItems: 'center', gap: 11, fontSize: 13, color: st.textColor, transition: 'color 0.3s ease' }}>
                <span className="pfx-step-dot" style={st.dotStyle}>{st.dotGlyph}</span>
                {st.label}
              </div>
            ))}
          </div>
        )}

        {(done || failed) && (
          <div style={{ display: 'flex', gap: 10, marginTop: 24 }}>
            <div className="pfx-btn pfx-btn-ghost" onClick={onClose} style={{ flex: 1, fontSize: 13, fontWeight: 500, color: color.textSecondary2, border: `1px solid ${color.borderRaised}`, borderRadius: 9, padding: '11px 0', textAlign: 'center', cursor: 'pointer' }}>
              Close
            </div>
            {done && (
              <div className="pfx-btn" onClick={onClose} style={{ flex: 1.4, fontSize: 13, fontWeight: 600, color: color.ink, background: d.accent, borderRadius: 9, padding: '11px 0', textAlign: 'center', cursor: 'pointer' }}>
                Done
              </div>
            )}
          </div>
        )}
      </div>
    </div>
  )
}
