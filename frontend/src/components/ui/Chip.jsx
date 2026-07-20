import { color } from '../../lib/theme'

export default function Chip({ label, active, onClick, pill = true }) {
  return (
    <div
      className="pfx-chip"
      onClick={onClick}
      style={{
        fontSize: 12, borderRadius: pill ? 20 : 7, padding: '7px 14px',
        border: `1px solid ${active ? color.teal : color.borderRaised}`,
        background: active ? '#1b2422' : 'transparent',
        color: active ? color.textSecondary : color.textMuted,
        cursor: onClick ? 'pointer' : 'default',
      }}
    >
      {label}
    </div>
  )
}
