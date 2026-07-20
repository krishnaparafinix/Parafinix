import { color, font } from '../../lib/theme'

export default function SearchInput({ value, onChange, placeholder, hint }) {
  return (
    <div
      className="pfx-search"
      style={{
        flex: 1, minWidth: 240, display: 'flex', alignItems: 'center', gap: 10,
        background: color.card, border: `1px solid ${color.border}`, borderRadius: 9, padding: '9px 14px',
        transition: 'border-color 0.16s ease, box-shadow 0.16s ease',
      }}
    >
      <span style={{ color: color.textFainter, fontSize: 14 }}>⌕</span>
      <input
        value={value}
        onChange={(e) => onChange(e.target.value)}
        placeholder={placeholder}
        style={{ flex: 1, background: 'transparent', border: 'none', outline: 'none', color: color.textSecondary, fontFamily: font.body, fontSize: 13 }}
      />
      {hint && (
        <span style={{ fontFamily: font.mono, fontSize: 10, color: '#4d5359', border: `1px solid ${color.borderRaised}`, borderRadius: 4, padding: '2px 6px' }}>
          {hint}
        </span>
      )}
    </div>
  )
}
