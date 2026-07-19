// The `clients` table has no fact_find_data column yet (backend gap — see README),
// so the structured fact-find JSON is persisted client-side per client id until the
// backend adds a `fact_find_data` JSONB field. Once saved, a report can still be
// generated and is stored properly server-side via POST /clients/{id}/cases.

const PREFIX = 'parafinix_factfind_'

export function loadFactFind(clientId) {
  const raw = localStorage.getItem(PREFIX + clientId)
  return raw ? JSON.parse(raw) : null
}

export function saveFactFind(clientId, { data, flags }) {
  localStorage.setItem(PREFIX + clientId, JSON.stringify({ data, flags, savedAt: new Date().toISOString() }))
}

export function clearFactFind(clientId) {
  localStorage.removeItem(PREFIX + clientId)
}
