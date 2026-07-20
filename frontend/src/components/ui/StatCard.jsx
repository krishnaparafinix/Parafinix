import { color, font } from '../../lib/theme'

export default function StatCard({ code, value, label, amber = false }) {
  return (
    <div
      className={`pfx-tilt pfx-stat ${amber ? 'pfx-stat-amber' : ''}`}
      style={{
        background: amber ? 'linear-gradient(160deg,#241d14,#16181b 75%)' : color.card,
        border: `1px solid ${amber ? '#4a3a1f' : color.border}`,
        borderRadius: 13, padding: 20,
      }}
    >
      <div
        className="pfx-stat-icon"
        style={{
          width: 34, height: 34, borderRadius: 9,
          background: amber ? color.amberSoftBg : color.tealSoftBg,
          border: `1px solid ${amber ? color.amberSoftBorder : color.tealSoftBorder}`,
          display: 'flex', alignItems: 'center', justifyContent: 'center',
          fontFamily: font.mono, fontSize: 12, color: amber ? color.amber : color.teal, fontWeight: amber ? 700 : 600,
        }}
      >
        {code}
      </div>
      <div style={{ fontFamily: font.display, fontSize: 30, fontWeight: 600, color: amber ? color.textPrimary : color.textPrimary, marginTop: 14, animation: 'pfx-count 0.5s ease both' }}>
        {value}
      </div>
      <div style={{ fontSize: 12, color: amber ? '#c9b79a' : color.textFaint, marginTop: 2 }}>{label}</div>
    </div>
  )
}
