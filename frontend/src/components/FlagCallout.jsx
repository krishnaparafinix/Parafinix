export default function FlagCallout({ flags, title = 'Needs your attention' }) {
  if (!flags || flags.length === 0) return null
  return (
    <div className="rounded-xl border border-amber/30 bg-amber/5 p-4">
      <p className="flex items-center gap-2 text-sm font-semibold text-amber">
        <svg width="16" height="16" viewBox="0 0 16 16" fill="none" aria-hidden="true">
          <path d="M8 1.5 15 14.5H1L8 1.5Z" stroke="currentColor" strokeWidth="1.4" strokeLinejoin="round" />
          <path d="M8 6.5v3.2M8 12v.02" stroke="currentColor" strokeWidth="1.4" strokeLinecap="round" />
        </svg>
        {title} ({flags.length})
      </p>
      <ul className="mt-2 space-y-1 pl-6 text-sm text-navy/80">
        {flags.map((f, i) => (
          <li key={i} className="list-disc">{f}</li>
        ))}
      </ul>
    </div>
  )
}
