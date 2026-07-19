import { api } from './client'

export function listAllCases() {
  return api.get('/cases').then((r) => r.data)
}

export function listClientCases(clientId) {
  return api.get(`/clients/${clientId}/cases`).then((r) => r.data)
}

export function saveCase(clientId, payload) {
  return api.post(`/clients/${clientId}/cases`, payload).then((r) => r.data)
}

export function getCase(caseId) {
  return api.get(`/cases/${caseId}`).then((r) => r.data)
}

export function getCaseCompliance(caseId) {
  return api.get(`/cases/${caseId}/compliance`).then((r) => r.data)
}

export function updateCaseStatus(caseId, status) {
  return api.patch(`/cases/${caseId}/status`, { status }).then((r) => r.data)
}

export function deleteCase(caseId) {
  return api.delete(`/cases/${caseId}`).then((r) => r.data)
}
