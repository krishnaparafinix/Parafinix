import { color, font } from '../../lib/theme'

export function initialsOf(name) {
  if (!name) return '?'
  return name.trim().split(/\s+/).map((w) => w[0]).filter(Boolean).slice(0, 2).join('').toUpperCase()
}

const TEAL_GRAD = `linear-gradient(150deg,${color.teal},${color.teal2})`
const AMBER_GRAD = `linear-gradient(150deg,${color.amberLight},${color.amber})`

export function avatarBackground(tone) {
  if (tone === 'teal') return TEAL_GRAD
  if (tone === 'amber') return AMBER_GRAD
  return color.borderRaised
}

export default function Avatar({ name, tone = 'flat', size = 36, radius = 10, className = '', style = {} }) {
  const filled = tone === 'teal' || tone === 'amber'
  return (
    <div
      className={className}
      style={{
        width: size, height: size, borderRadius: radius, flex: '0 0 auto',
        display: 'flex', alignItems: 'center', justifyContent: 'center',
        fontFamily: font.display, fontWeight: 700, fontSize: size <= 36 ? 12 : Math.round(size * 0.33),
        color: filled ? color.ink : color.teal,
        background: avatarBackground(tone),
        border: filled ? 'none' : `1px solid ${color.borderRaised}`,
        ...style,
      }}
    >
      {initialsOf(name)}
    </div>
  )
}
