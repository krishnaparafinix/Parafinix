import { Link } from 'react-router-dom'
import { color, font } from '../../lib/theme'

const NAV = [
  { key: 'dashboard', label: 'Dashboard', href: '/' },
  { key: 'clients', label: 'Clients', href: '/clients' },
  { key: 'reports', label: 'Reports', href: '/reports' },
  { key: 'settings', label: 'Settings', href: null },
]

function NavItem({ item, active }) {
  const isActive = item.key === active
  const style = {
    display: 'flex', alignItems: 'center', gap: 11, padding: '10px 12px', borderRadius: 7,
    fontSize: 13.5, textDecoration: 'none',
    background: isActive ? color.raised : 'transparent',
    color: isActive ? color.textPrimary : color.textMuted,
    fontWeight: isActive ? 500 : 400,
    border: isActive ? `1px solid ${color.borderRaised}` : '1px solid transparent',
    cursor: item.href ? 'pointer' : 'default',
  }
  const dot = <span style={{ width: 6, height: 6, borderRadius: 2, background: isActive ? color.teal : '#3a3f45', flex: '0 0 auto' }} />
  const label = <span className="pfx-label">{item.label}</span>

  if (!item.href) {
    return <div className="pfx-nav" style={style}>{dot}{label}</div>
  }
  return (
    <Link className="pfx-nav" to={item.href} style={style}>
      {dot}{label}
    </Link>
  )
}

export default function Sidebar({ active, user }) {
  const initials = (user?.full_name || user?.email || 'JM')
    .split(/\s+/).map((w) => w[0]).filter(Boolean).slice(0, 2).join('').toUpperCase() || 'JM'

  return (
    <div className="pfx-side">
      <div className="pfx-panel">
        <div className="pfx-panel-3d">
          <div
            className="pfx-logo"
            data-pfx-toggle
            style={{ display: 'flex', alignItems: 'center', gap: 12, padding: '0 18px 26px', cursor: 'pointer' }}
          >
            <div style={{ width: 36, height: 36, borderRadius: 9, background: color.raised, border: `1px solid ${color.borderRaised}`, display: 'flex', alignItems: 'center', justifyContent: 'center', gap: 2.5 }}>
              <div className="pfx-w1" style={{ width: 4, height: 14, background: color.teal, borderRadius: 2, transform: 'skewX(-14deg) scaleY(0.72)' }} />
              <div className="pfx-w2" style={{ width: 4, height: 20, background: color.textSecondary, borderRadius: 2, transform: 'skewX(-14deg)' }} />
              <div className="pfx-w3" style={{ width: 4, height: 14, background: color.amber, borderRadius: 2, transform: 'skewX(-14deg)' }} />
            </div>
            <span className="pfx-label" style={{ fontFamily: font.display, fontSize: 16, fontWeight: 600, color: color.textPrimary, letterSpacing: '-0.01em' }}>
              parafinix<span style={{ color: color.teal }}>.ai</span>
            </span>
          </div>

          <div style={{ display: 'flex', flexDirection: 'column', gap: 2, padding: '0 12px' }}>
            {NAV.map((item) => <NavItem key={item.key} item={item} active={active} />)}
          </div>

          <div style={{ marginTop: 'auto', padding: '16px 12px 0', borderTop: `1px solid ${color.border}`, marginLeft: 12, marginRight: 12, display: 'flex', alignItems: 'center', gap: 10 }}>
            <div style={{ width: 30, height: 30, borderRadius: 8, background: color.amber, color: color.ink, display: 'flex', alignItems: 'center', justifyContent: 'center', fontWeight: 700, fontSize: 12, flex: '0 0 auto' }}>
              {initials}
            </div>
            <div className="pfx-label" style={{ lineHeight: 1.2, minWidth: 0 }}>
              <div style={{ fontSize: 12.5, color: color.textPrimary, whiteSpace: 'nowrap' }}>{user?.full_name || 'Adviser'}</div>
              <div style={{ fontSize: 11, color: color.textFaint, whiteSpace: 'nowrap' }}>{user?.firm_name || 'Chartered Adviser'}</div>
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}
