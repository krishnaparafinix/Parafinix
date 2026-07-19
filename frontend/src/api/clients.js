import { api } from './client'

export function listClients() {
  return api.get('/clients').then((r) => r.data.clients)
}

export function getDashboardStats() {
  return api.get('/clients/stats').then((r) => r.data)
}

export function getClient(clientId) {
  return api.get(`/clients/${clientId}`).then((r) => r.data)
}

export function createClient(payload) {
  return api.post('/clients', payload).then((r) => r.data)
}

export function updateClient(clientId, payload) {
  return api.patch(`/clients/${clientId}`, payload).then((r) => r.data)
}

export function deleteClient(clientId) {
  return api.delete(`/clients/${clientId}`).then((r) => r.data)
}
