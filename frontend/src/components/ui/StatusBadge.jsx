import { color } from '../../lib/theme'

// tone: 'amber' | 'teal' | 'grey'
export default function StatusBadge({ label, tone = 'teal' }) {
  const styles = {
    amber: { c: color.amber, bg: color.amberSoftBg },
    teal: { c: color.teal, bg: color.tealSoftBg },
    grey: { c: color.textMuted, bg: 'rgba(146,152,160,0.1)' },
  }[tone]
  return (
    <span style={{ fontSize: 11, color: styles.c, background: styles.bg, padding: '3px 9px', borderRadius: 6, whiteSpace: 'nowrap' }}>
      {label}
    </span>
  )
}
