import { statusStyle } from '../lib/rag'

export default function StatusBadge({ status }) {
  const style = statusStyle(status)
  return (
    <span className={`inline-flex items-center rounded-full px-2.5 py-1 text-xs font-semibold ${style.className}`}>
      {style.label}
    </span>
  )
}
