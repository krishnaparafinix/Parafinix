import { useEffect, useRef, useState } from 'react'
import { sendChatMessage } from '../api/aiChat'
import { apiErrorMessage } from '../api/client'

const WELCOME = {
  role: 'assistant',
  content: "Hi, I'm your Parafinix assistant. Ask me about a client's report status, your account stats, or general product and compliance questions.",
}

function TraceIcon({ className = '' }) {
  return (
    <svg width="18" height="18" viewBox="0 0 28 28" fill="none" aria-hidden="true" className={className}>
      <path
        d="M2 20 L9 20 L12 10 L16 24 L19 14 L22 20 L26 20"
        stroke="currentColor"
        strokeWidth="2.2"
        strokeLinecap="round"
        strokeLinejoin="round"
        fill="none"
      />
    </svg>
  )
}

function TypingIndicator() {
  return (
    <div className="flex items-center gap-1 px-3.5 py-2.5">
      {[0, 1, 2].map((i) => (
        <span
          key={i}
          className="h-1.5 w-1.5 animate-bounce rounded-full bg-text-secondary/60"
          style={{ animationDelay: `${i * 0.15}s` }}
        />
      ))}
    </div>
  )
}

function MessageBubble({ role, content }) {
  const isUser = role === 'user'
  const isError = role === 'error'
  return (
    <div className={`flex ${isUser ? 'justify-end' : 'justify-start'}`}>
      <div className={`flex max-w-[85%] items-end gap-2 ${isUser ? 'flex-row-reverse' : ''}`}>
        {!isUser && (
          <span className="mb-0.5 flex h-6 w-6 shrink-0 items-center justify-center rounded-full bg-navy text-brand-blue">
            <TraceIcon />
          </span>
        )}
        <div
          className={[
            'whitespace-pre-wrap rounded-2xl px-3.5 py-2.5 text-sm leading-relaxed',
            isUser && 'rounded-br-sm bg-navy text-white',
            !isUser && !isError && 'rounded-bl-sm bg-bg text-navy',
            isError && 'rounded-bl-sm border border-red/30 bg-red/5 text-red',
          ].filter(Boolean).join(' ')}
        >
          {content}
        </div>
      </div>
    </div>
  )
}

export default function ChatWidget() {
  const [open, setOpen] = useState(false)
  const [messages, setMessages] = useState([WELCOME])
  const [input, setInput] = useState('')
  const [sending, setSending] = useState(false)
  const listRef = useRef(null)
  const inputRef = useRef(null)

  useEffect(() => {
    if (listRef.current) {
      listRef.current.scrollTop = listRef.current.scrollHeight
    }
  }, [messages, sending])

  useEffect(() => {
    if (open) {
      const t = setTimeout(() => inputRef.current?.focus(), 50)
      return () => clearTimeout(t)
    }
  }, [open])

  const handleSend = async (e) => {
    e.preventDefault()
    const text = input.trim()
    if (!text || sending) return

    setMessages((m) => [...m, { role: 'user', content: text }])
    setInput('')
    setSending(true)

    try {
      const { reply } = await sendChatMessage(text)
      setMessages((m) => [...m, { role: 'assistant', content: reply }])
    } catch (err) {
      setMessages((m) => [...m, { role: 'error', content: apiErrorMessage(err, "Couldn't reach the assistant. Please try again.") }])
    } finally {
      setSending(false)
    }
  }

  return (
    <div className="fixed bottom-6 right-6 z-50 flex flex-col items-end gap-3">
      {open && (
        <div className="flex h-[30rem] w-[22rem] max-w-[calc(100vw-3rem)] animate-fade-in-up flex-col overflow-hidden rounded-xl border border-border bg-surface shadow-lg">
          <div className="flex items-center justify-between border-b border-border bg-navy px-4 py-3.5">
            <div className="flex items-center gap-2.5">
              <span className="relative flex h-7 w-7 items-center justify-center rounded-full bg-white/10 text-emerald">
                <TraceIcon />
                <span className="absolute -right-0.5 -top-0.5 h-2 w-2 rounded-full bg-emerald animate-pulse-node" />
              </span>
              <div>
                <p className="text-sm font-semibold text-white">Parafinix Assistant</p>
                <p className="text-xs text-white/60">Answers about your clients & reports</p>
              </div>
            </div>
            <button
              onClick={() => setOpen(false)}
              aria-label="Close chat"
              className="rounded-md p-1 text-white/70 transition-colors hover:bg-white/10 hover:text-white"
            >
              <svg width="16" height="16" viewBox="0 0 16 16" fill="none" aria-hidden="true">
                <path d="M4 4l8 8M12 4l-8 8" stroke="currentColor" strokeWidth="1.6" strokeLinecap="round" />
              </svg>
            </button>
          </div>

          <div ref={listRef} className="flex-1 space-y-3 overflow-y-auto px-4 py-4">
            {messages.map((m, i) => (
              <MessageBubble key={i} role={m.role} content={m.content} />
            ))}
            {sending && (
              <div className="flex justify-start">
                <div className="flex items-end gap-2">
                  <span className="mb-0.5 flex h-6 w-6 shrink-0 items-center justify-center rounded-full bg-navy text-brand-blue">
                    <TraceIcon />
                  </span>
                  <div className="rounded-2xl rounded-bl-sm bg-bg">
                    <TypingIndicator />
                  </div>
                </div>
              </div>
            )}
          </div>

          <form onSubmit={handleSend} className="flex items-center gap-2 border-t border-border p-3">
            <input
              ref={inputRef}
              value={input}
              onChange={(e) => setInput(e.target.value)}
              placeholder="Ask about a client, report, or compliance…"
              disabled={sending}
              className="flex-1 rounded-lg border border-border bg-bg px-3 py-2 text-sm outline-none transition-colors focus:border-brand-blue focus:ring-2 focus:ring-brand-blue/20 disabled:opacity-60"
            />
            <button
              type="submit"
              disabled={sending || !input.trim()}
              aria-label="Send message"
              className="flex h-9 w-9 shrink-0 items-center justify-center rounded-lg bg-emerald text-white transition-all duration-200 hover:-translate-y-px hover:bg-emerald-600 disabled:cursor-not-allowed disabled:opacity-40 disabled:hover:translate-y-0"
            >
              <svg width="16" height="16" viewBox="0 0 16 16" fill="none" aria-hidden="true">
                <path d="M2 8h11M8 3l5 5-5 5" stroke="currentColor" strokeWidth="1.6" strokeLinecap="round" strokeLinejoin="round" />
              </svg>
            </button>
          </form>
        </div>
      )}

      <button
        onClick={() => setOpen((o) => !o)}
        aria-label={open ? 'Close assistant chat' : 'Open assistant chat'}
        aria-expanded={open}
        className="flex h-14 w-14 items-center justify-center rounded-full bg-emerald text-white shadow-lg transition-all duration-200 ease-out hover:-translate-y-0.5 hover:bg-emerald-600 hover:shadow-xl"
      >
        {open ? (
          <svg width="20" height="20" viewBox="0 0 16 16" fill="none" aria-hidden="true">
            <path d="M4 4l8 8M12 4l-8 8" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" />
          </svg>
        ) : (
          <span className="relative">
            <svg width="24" height="24" viewBox="0 0 24 24" fill="none" aria-hidden="true">
              <path
                d="M4 5.5A2.5 2.5 0 0 1 6.5 3h11A2.5 2.5 0 0 1 20 5.5v8a2.5 2.5 0 0 1-2.5 2.5H10l-4.5 4v-4H6.5A2.5 2.5 0 0 1 4 13.5v-8Z"
                stroke="currentColor"
                strokeWidth="1.6"
                strokeLinejoin="round"
              />
            </svg>
            <span className="absolute -right-0.5 -top-0.5 h-2.5 w-2.5 rounded-full bg-white animate-pulse-node" />
          </span>
        )}
      </button>
    </div>
  )
}
