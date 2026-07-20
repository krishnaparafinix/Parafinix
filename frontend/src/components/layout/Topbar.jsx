import { Link } from 'react-router-dom'
import { color, font } from '../../lib/theme'

export default function Topbar({ breadcrumb, ghost, primary }) {
  return (
    <div
      style={{
        display: 'flex', alignItems: 'center', justifyContent: 'space-between',
        padding: '16px 34px', background: 'rgba(19,21,24,0.7)', backdropFilter: 'blur(8px)',
        borderBottom: `1px solid ${color.border}`, position: 'sticky', top: 0, zIndex: 5,
      }}
    >
      <div style={{ fontFamily: font.mono, fontSize: 11, color: color.textFaint, letterSpacing: '0.06em', display: 'flex', gap: 6 }}>
        {breadcrumb.map((seg, i) => {
          const isLast = i === breadcrumb.length - 1
          const content = isLast ? <span style={{ color: color.textPrimary }}>{seg.label}</span> : seg.label
          return (
            <span key={i} style={{ display: 'flex', gap: 6 }}>
              {seg.href && !isLast ? (
                <Link to={seg.href} style={{ color: color.textFaint }}>{content}</Link>
              ) : content}
              {!isLast && <span>/</span>}
            </span>
          )
        })}
      </div>
      <div style={{ display: 'flex', gap: 10 }}>
        {ghost && (
          <div
            className="pfx-btn pfx-btn-ghost"
            onClick={ghost.onClick}
            style={{ fontSize: 12.5, color: color.textSecondary2, border: `1px solid ${color.borderRaised}`, padding: '8px 15px', borderRadius: 8, background: color.raised, cursor: ghost.onClick ? 'pointer' : 'default' }}
          >
            {ghost.label}
          </div>
        )}
        {primary && (
          <div
            className="pfx-btn pfx-btn-amber"
            onClick={primary.onClick}
            style={{ fontSize: 12.5, color: color.ink, background: color.amber, padding: '8px 17px', borderRadius: 8, fontWeight: 600, cursor: primary.onClick ? 'pointer' : 'default' }}
          >
            {primary.label}
          </div>
        )}
      </div>
    </div>
  )
}
