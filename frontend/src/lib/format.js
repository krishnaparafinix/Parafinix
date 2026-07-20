export function timeAgo(iso) {
  if (!iso) return ''
  const diffMs = Date.now() - new Date(iso).getTime()
  const mins = Math.floor(diffMs / 60000)
  if (mins < 1) return 'Just now'
  if (mins < 60) return `${mins}m ago`
  const hours = Math.floor(mins / 60)
  if (hours < 24) return `${hours}h ago`
  const days = Math.floor(hours / 24)
  if (days === 1) return 'Yesterday'
  if (days < 7) return `${days}d ago`
  return new Date(iso).toLocaleDateString('en-GB', { day: 'numeric', month: 'short' })
}

export function formatDate(iso) {
  if (!iso) return '—'
  return new Date(iso).toLocaleDateString('en-GB', { day: '2-digit', month: 'short', year: 'numeric' })
}

export function isoDate(iso) {
  if (!iso) return '—'
  return new Date(iso).toISOString().slice(0, 10)
}

// Report status (draft|in_review|signed_off) -> design's 2-tone badge system.
export function reportStatusBadge(status) {
  if (status === 'signed_off') return { label: 'Finalised', tone: 'teal' }
  return { label: 'In review', tone: 'amber' }
}

export function ragTone(rag) {
  const r = (rag || '').toUpperCase()
  if (r === 'GREEN') return 'teal'
  if (r === 'AMBER' || r === 'RED') return 'amber'
  return 'grey'
}

// Buckets cases into the last `weeks` ISO weeks by created_at for the
// Documents/week chart. Real counts from real data — no synthetic fill.
export function weeklyDocumentCounts(cases, weeks = 4) {
  const now = new Date()
  const buckets = new Array(weeks).fill(0)
  const msWeek = 7 * 24 * 60 * 60 * 1000
  const startOfThisWeek = now.getTime() - (now.getTime() % msWeek)
  for (const c of cases) {
    const t = new Date(c.created_at).getTime()
    if (Number.isNaN(t)) continue
    const weeksAgo = Math.floor((startOfThisWeek + msWeek - t) / msWeek)
    const idx = weeks - weeksAgo
    if (idx >= 0 && idx < weeks) buckets[idx] += 1
  }
  return buckets
}
