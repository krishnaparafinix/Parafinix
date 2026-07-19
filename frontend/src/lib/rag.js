export const RAG_STYLES = {
  GREEN: { dot: 'bg-emerald', label: 'Green', text: 'text-emerald' },
  AMBER: { dot: 'bg-amber', label: 'Amber', text: 'text-amber' },
  RED: { dot: 'bg-red', label: 'Red', text: 'text-red' },
}

export function ragStyle(rag) {
  return RAG_STYLES[(rag || '').toUpperCase()] || { dot: 'bg-border', label: 'Not rated', text: 'text-text-secondary' }
}

export const STATUS_STYLES = {
  draft: { label: 'Draft', className: 'bg-slate-100 text-navy' },
  in_review: { label: 'In Review', className: 'bg-blue-50 text-brand-blue' },
  signed_off: { label: 'Signed Off', className: 'bg-emerald-50 text-emerald' },
}

export function statusStyle(status) {
  return STATUS_STYLES[status] || { label: status || 'Draft', className: 'bg-slate-100 text-navy' }
}

export const STATUS_ORDER = ['draft', 'in_review', 'signed_off']

export function nextStatus(status) {
  const idx = STATUS_ORDER.indexOf(status)
  if (idx === -1 || idx === STATUS_ORDER.length - 1) return null
  return STATUS_ORDER[idx + 1]
}
