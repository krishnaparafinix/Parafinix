import { color, font } from '../lib/theme'

export default function AuthLogo() {
  return (
    <div className="pfx-logo" style={{ display: 'flex', alignItems: 'center', gap: 12, justifyContent: 'center' }}>
      <div style={{ width: 40, height: 40, borderRadius: 10, background: color.raised, border: `1px solid ${color.borderRaised}`, display: 'flex', alignItems: 'center', justifyContent: 'center', gap: 3 }}>
        <div className="pfx-w1" style={{ width: 4, height: 16, background: color.teal, borderRadius: 2, transform: 'skewX(-14deg) scaleY(0.72)' }} />
        <div className="pfx-w2" style={{ width: 4, height: 22, background: color.textSecondary, borderRadius: 2, transform: 'skewX(-14deg)' }} />
        <div className="pfx-w3" style={{ width: 4, height: 16, background: color.amber, borderRadius: 2, transform: 'skewX(-14deg)' }} />
      </div>
      <span style={{ fontFamily: font.display, fontSize: 19, fontWeight: 600, color: color.textPrimary, letterSpacing: '-0.01em' }}>
        parafinix<span style={{ color: color.teal }}>.ai</span>
      </span>
    </div>
  )
}
