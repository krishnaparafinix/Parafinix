import { api } from './client'

function filenameFromDisposition(disposition, fallback) {
  if (!disposition) return fallback
  const match = /filename="?([^"]+)"?/.exec(disposition)
  return match ? match[1] : fallback
}

async function downloadBlob(path, payload, fallbackName) {
  let res
  try {
    res = await api.post(`${path}?download=true`, payload, { responseType: 'blob' })
  } catch (error) {
    // Error responses still come back as a Blob because of responseType — decode
    // it back to JSON so apiErrorMessage() can read the `detail` field normally.
    if (error.response?.data instanceof Blob) {
      try {
        const text = await error.response.data.text()
        error.response.data = JSON.parse(text)
      } catch {
        // leave as-is if it wasn't JSON
      }
    }
    throw error
  }
  const filename = filenameFromDisposition(res.headers['content-disposition'], fallbackName)
  const url = window.URL.createObjectURL(res.data)
  const link = document.createElement('a')
  link.href = url
  link.download = filename
  document.body.appendChild(link)
  link.click()
  link.remove()
  window.URL.revokeObjectURL(url)
}

export function downloadSuitabilityDoc(payload) {
  return downloadBlob('/documents/suitability', payload, `${payload.client_name}_Suitability_Report.docx`)
}

export function downloadComplianceDoc(payload) {
  return downloadBlob('/documents/compliance', payload, `${payload.client_name}_Compliance_Review.docx`)
}

export function downloadFactFindDoc(payload) {
  return downloadBlob('/documents/factfind', payload, `${payload.client_name}_FactFind.docx`)
}
