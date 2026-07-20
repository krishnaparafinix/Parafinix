import { useEffect, useRef, useState } from 'react'
import { sendChatMessage } from '../api/aiChat'
import { apiErrorMessage } from '../api/client'
import { useAuth } from '../context/AuthContext'
import { color, font } from '../lib/theme'

const WORKSPACE_PROMPTS = ["What's my report status?", 'How many reports did I generate this month?']
const KNOWLEDGE_PROMPTS = ['What must a suitability report cover?', 'Explain COBS 9 in plain terms']

function TraceLine({ width = 30, height = 12, dotDuration = '1.7s', pulseDuration = '1.4s' }) {
  return (
    <div style={{ position: 'relative', width, height, flex: '0 0 auto', display: 'flex', alignItems: 'center' }}>
      <div style={{ position: 'absolute', left: 1, right: 1, height: 2, background: color.borderRaised, borderRadius: 2 }} />
      <div style={{ position: 'absolute', left: 0, top: '50%', transform: 'translateY(-50%)', width: 6, height: 6, borderRadius: '50%', background: color.teal }} />
      <div style={{ position: 'absolute', left: '50%', top: '50%', transform: 'translate(-50%,-50%)', width: 5, height: 5, borderRadius: '50%', background: color.amber }} />
      <div style={{ position: 'absolute', right: 0, top: '50%', width: 8, height: 8, borderRadius: '50%', background: color.teal, animation: `pfx-nodepulse ${pulseDuration} ease-in-out infinite` }} />
      <div style={{ position: 'absolute', top: '50%', transform: 'translateY(-50%)', width: 5, height: 5, borderRadius: '50%', background: color.teal, boxShadow: `0 0 8px ${color.teal}`, animation: `pfx-dot ${dotDuration} ease-in-out infinite` }} />
    </div>
  )
}

function MessageBubble({ who, text }) {
  const isUser = who === 'user'
  return (
    <div
      style={{
        maxWidth: isUser ? '82%' : '88%',
        alignSelf: isUser ? 'flex-end' : 'flex-start',
        background: isUser ? color.teal : color.raised,
        color: isUser ? color.ink : color.textSecondary,
        border: isUser ? 'none' : `1px solid ${color.borderRaised}`,
        borderRadius: isUser ? '14px 14px 4px 14px' : '14px 14px 14px 4px',
        padding: '10px 13px',
        fontSize: 13.5,
        lineHeight: isUser ? 1.5 : 1.55,
        fontWeight: isUser ? 500 : 400,
        animation: 'pfx-msg .22s ease',
        whiteSpace: 'pre-wrap',
      }}
    >
      {text}
    </div>
  )
}

function PromptChip({ label, dotColor, onClick }) {
  return (
    <div
      className="pfx-achip"
      onClick={onClick}
      style={{ display: 'flex', alignItems: 'center', gap: 9, border: `1px solid ${color.border}`, borderRadius: 10, padding: '10px 12px', fontSize: 13, color: color.textSecondary, background: color.card }}
    >
      <span style={{ width: 6, height: 6, borderRadius: '50%', background: dotColor, flex: '0 0 auto' }} />
      {label}
    </div>
  )
}

export default function ChatWidget() {
  const { user } = useAuth()
  const [open, setOpen] = useState(false)
  const [messages, setMessages] = useState([])
  const [input, setInput] = useState('')
  const [thinking, setThinking] = useState(false)
  const [thinkingLabel, setThinkingLabel] = useState('Thinking…')
  const listRef = useRef(null)
  const inputRef = useRef(null)

  useEffect(() => {
    if (listRef.current) listRef.current.scrollTop = listRef.current.scrollHeight
  }, [messages, thinking])

  useEffect(() => {
    if (open) {
      const t = setTimeout(() => inputRef.current?.focus(), 60)
      return () => clearTimeout(t)
    }
  }, [open])

  const thinkingLabelFor = (q) => {
    const t = q.toLowerCase()
    if (t.includes('report') || t.includes('client') || t.includes('this month') || t.includes('how many')) return 'Checking your workspace…'
    if (t.includes('cobs') || t.includes('suitability') || t.includes('compliance') || t.includes('rule')) return 'Reviewing guidance…'
    return 'Thinking…'
  }

  const sendText = async (text) => {
    const q = (text || '').trim()
    if (!q || thinking) return
    setMessages((m) => [...m, { who: 'user', text: q }])
    setInput('')
    setThinking(true)
    setThinkingLabel(thinkingLabelFor(q))
    try {
      const { reply } = await sendChatMessage(q)
      setMessages((m) => [...m, { who: 'ai', text: reply }])
    } catch (err) {
      setMessages((m) => [...m, { who: 'ai', text: apiErrorMessage(err, "Couldn't reach the assistant. Please try again.") }])
    } finally {
      setThinking(false)
    }
  }

  const onSubmit = (e) => { e.preventDefault(); sendText(input) }
  const onKey = (e) => { if (e.key === 'Enter' && !e.shiftKey) { e.preventDefault(); sendText(input) } }
  const canSend = input.trim().length > 0 && !thinking
  const showWelcome = messages.length === 0 && !thinking
  const firstName = (user?.full_name || '').split(' ')[0]

  return (
    <div style={{ position: 'fixed', bottom: 24, right: 24, zIndex: 60 }}>
      {!open && (
        <div
          className="pfx-btnround"
          onClick={() => setOpen(true)}
          style={{ display: 'inline-flex', alignItems: 'center', background: color.card, border: `1px solid ${color.borderRaised}`, color: color.textPrimary, height: 56, padding: '0 18px', borderRadius: 999, boxShadow: '0 14px 34px -10px rgba(0,0,0,0.7)', cursor: 'pointer' }}
        >
          <TraceLine />
          <span className="pfx-btnlabel" style={{ fontSize: 14, fontWeight: 500 }}>Ask Parafinix</span>
        </div>
      )}

      {open && (
        <div style={{ width: 388, height: 576, maxHeight: 'calc(100vh - 48px)', background: color.rail, border: `1px solid ${color.border}`, borderRadius: 16, boxShadow: '0 30px 60px -22px rgba(0,0,0,0.7)', display: 'flex', flexDirection: 'column', overflow: 'hidden', animation: 'pfx-pop .34s cubic-bezier(.2,.8,.2,1)' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: 12, padding: '15px 16px', borderBottom: `1px solid ${color.borderSubtle}`, flex: '0 0 auto' }}>
            <div style={{ width: 38, height: 38, borderRadius: 10, background: color.raised, border: `1px solid ${color.borderRaised}`, display: 'flex', alignItems: 'center', justifyContent: 'center', flex: '0 0 auto' }}>
              <TraceLine width={20} height={10} />
            </div>
            <div style={{ flex: 1, minWidth: 0 }}>
              <div style={{ fontFamily: font.display, fontSize: 14, fontWeight: 600, color: color.textPrimary, letterSpacing: '-0.01em' }}>Parafinix Assistant</div>
              <div style={{ display: 'flex', alignItems: 'center', gap: 6, marginTop: 2 }}>
                <span style={{ width: 6, height: 6, borderRadius: '50%', background: color.teal, animation: 'pfx-nodepulse-c 1.6s ease-in-out infinite', flex: '0 0 auto' }} />
                <span style={{ fontSize: 11.5, color: color.textFaint }}>Online · reads your workspace</span>
              </div>
            </div>
            <div className="pfx-iconbtn" onClick={() => setOpen(false)} style={{ width: 30, height: 30, borderRadius: 8, display: 'flex', alignItems: 'center', justifyContent: 'center', color: color.textFaint, fontSize: 15, flex: '0 0 auto' }}>▁</div>
          </div>

          <div ref={listRef} style={{ flex: 1, overflow: 'auto', padding: '18px 16px', display: 'flex', flexDirection: 'column', gap: 12 }}>
            {showWelcome && (
              <div style={{ display: 'flex', flexDirection: 'column', gap: 18 }}>
                <div style={{ display: 'flex', flexDirection: 'column', gap: 11 }}>
                  <div style={{ width: 44, height: 44, borderRadius: 12, background: color.raised, border: `1px solid ${color.borderRaised}`, display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
                    <TraceLine width={24} height={12} pulseDuration="1.5s" />
                  </div>
                  <div>
                    <div style={{ fontFamily: font.display, fontSize: 16, fontWeight: 600, color: color.textPrimary, letterSpacing: '-0.01em' }}>
                      How can I help{firstName ? `, ${firstName}` : ''}?
                    </div>
                    <div style={{ fontSize: 13, color: color.textMuted, lineHeight: 1.55, marginTop: 4 }}>
                      Ask about your clients and reports, or anything on compliance and product rules.
                    </div>
                  </div>
                </div>
                <div style={{ display: 'flex', flexDirection: 'column', gap: 8 }}>
                  <div style={{ fontFamily: font.mono, fontSize: 10, fontWeight: 600, letterSpacing: '0.12em', textTransform: 'uppercase', color: color.textFainter }}>Your workspace</div>
                  {WORKSPACE_PROMPTS.map((p) => <PromptChip key={p} label={p} dotColor={color.teal} onClick={() => sendText(p)} />)}
                </div>
                <div style={{ display: 'flex', flexDirection: 'column', gap: 8 }}>
                  <div style={{ fontFamily: font.mono, fontSize: 10, fontWeight: 600, letterSpacing: '0.12em', textTransform: 'uppercase', color: color.textFainter }}>Compliance &amp; products</div>
                  {KNOWLEDGE_PROMPTS.map((p) => <PromptChip key={p} label={p} dotColor={color.amber} onClick={() => sendText(p)} />)}
                </div>
              </div>
            )}

            {messages.map((m, i) => <MessageBubble key={i} who={m.who} text={m.text} />)}

            {thinking && (
              <div style={{ alignSelf: 'flex-start', display: 'flex', alignItems: 'center', gap: 11, background: color.raised, border: `1px solid ${color.borderRaised}`, borderRadius: '14px 14px 14px 4px', padding: '11px 14px', animation: 'pfx-msg .2s ease' }}>
                <div style={{ position: 'relative', width: 120, height: 14, display: 'flex', alignItems: 'center', flex: '0 0 auto' }}>
                  <div style={{ position: 'absolute', left: 2, right: 2, height: 2, background: color.borderRaised, borderRadius: 2, animation: 'pfx-spinline 1.4s ease-in-out infinite' }} />
                  <div style={{ position: 'absolute', left: 0, top: '50%', transform: 'translateY(-50%)', width: 7, height: 7, borderRadius: '50%', background: color.teal }} />
                  <div style={{ position: 'absolute', left: '50%', top: '50%', transform: 'translate(-50%,-50%)', width: 6, height: 6, borderRadius: '50%', background: color.amber }} />
                  <div style={{ position: 'absolute', right: 0, top: '50%', width: 8, height: 8, borderRadius: '50%', background: color.teal, animation: 'pfx-nodepulse 1.3s ease-in-out infinite' }} />
                  <div style={{ position: 'absolute', top: '50%', transform: 'translateY(-50%)', width: 6, height: 6, borderRadius: '50%', background: color.teal, boxShadow: `0 0 8px ${color.teal}`, animation: 'pfx-dot 1.5s ease-in-out infinite' }} />
                </div>
                <span style={{ fontSize: 12.5, color: color.textFaint }}>{thinkingLabel}</span>
              </div>
            )}
          </div>

          <form onSubmit={onSubmit} style={{ padding: '12px 14px 14px', borderTop: `1px solid ${color.borderSubtle}`, flex: '0 0 auto' }}>
            <div className="pfx-input" style={{ display: 'flex', alignItems: 'flex-end', gap: 8, border: `1px solid ${color.border}`, borderRadius: 12, padding: '8px 8px 8px 13px', background: color.card, transition: 'border-color .16s ease, box-shadow .16s ease' }}>
              <input
                ref={inputRef}
                value={input}
                onChange={(e) => setInput(e.target.value)}
                onKeyDown={onKey}
                disabled={thinking}
                placeholder="Ask about a client, report, or rule…"
                style={{ flex: 1, border: 'none', outline: 'none', fontFamily: font.body, fontSize: 13.5, color: color.textPrimary, background: 'transparent', padding: '5px 0' }}
              />
              <button
                type="submit"
                disabled={!canSend}
                className="pfx-send"
                style={{ width: 34, height: 34, borderRadius: 9, display: 'flex', alignItems: 'center', justifyContent: 'center', flex: '0 0 auto', background: color.teal, border: 'none', cursor: canSend ? 'pointer' : 'default', opacity: canSend ? 1 : 0.4 }}
              >
                <svg width="16" height="16" viewBox="0 0 24 24" fill="none"><path d="M4 12h15M13 6l6 6-6 6" stroke="#0f1113" strokeWidth="2.2" strokeLinecap="round" strokeLinejoin="round" /></svg>
              </button>
            </div>
            <div style={{ textAlign: 'center', fontSize: 10.5, color: color.textFainter, marginTop: 9 }}>Parafinix can be wrong — verify figures before advising.</div>
          </form>
        </div>
      )}
    </div>
  )
}
