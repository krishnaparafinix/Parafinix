// The clients table has no columns for objective/risk profile/next review
// date/status (only name/email/phone/segment/portfolio_value/rag) — same
// backend gap as fact-find data. Persisted client-side per client id until
// the backend adds real columns. See lib/localFactFind.js for the sibling
// pattern.

const PREFIX = 'parafinix_clientmeta_'

export function loadClientMeta(clientId) {
  const raw = localStorage.getItem(PREFIX + clientId)
  return raw ? JSON.parse(raw) : null
}

export function saveClientMeta(clientId, meta) {
  const existing = loadClientMeta(clientId) || {}
  localStorage.setItem(PREFIX + clientId, JSON.stringify({ ...existing, ...meta }))
}

export function loadAllClientMeta() {
  const all = {}
  for (let i = 0; i < localStorage.length; i++) {
    const key = localStorage.key(i)
    if (key && key.startsWith(PREFIX)) {
      const clientId = key.slice(PREFIX.length)
      all[clientId] = JSON.parse(localStorage.getItem(key))
    }
  }
  return all
}
