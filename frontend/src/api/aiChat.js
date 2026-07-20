import { api } from './client'

export function sendChatMessage(message) {
  // Runs the data-aware assistant server-side (tool-calls into the user's
  // own clients/cases), which can take a few seconds — give it real headroom.
  return api.post('/ai/chat', { message }, { timeout: 60000 }).then((r) => r.data)
}

export function rerunCompliance(caseId) {
  // Reruns the 28-point compliance check against an existing case's report
  // text and updates that case's compliance fields in place.
  return api.post('/ai/compliance/rerun', { case_id: caseId }, { timeout: 60000 }).then((r) => r.data)
}
