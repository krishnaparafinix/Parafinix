import { api } from './client'

export function uploadPdf(file) {
  const form = new FormData()
  form.append('file', file)
  return api.post('/upload/pdf', form, {
    headers: { 'Content-Type': 'multipart/form-data' },
  }).then((r) => r.data)
}

export function extractFactFind(notes) {
  return api.post('/generate/extract', { notes }).then((r) => r.data)
}

export function preflightCheck(notes) {
  return api.post('/generate/preflight', { notes }).then((r) => r.data)
}

export function generateReport(payload) {
  // Long-running: 3 AI passes + compliance check on the server.
  return api.post('/generate/report', payload, { timeout: 300000 }).then((r) => r.data)
}
