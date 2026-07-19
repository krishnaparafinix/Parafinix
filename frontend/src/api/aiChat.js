import { api } from './client'

export function sendChatMessage(message) {
  // Runs the data-aware assistant server-side (tool-calls into the user's
  // own clients/cases), which can take a few seconds — give it real headroom.
  return api.post('/ai/chat', { message }, { timeout: 60000 }).then((r) => r.data)
}
