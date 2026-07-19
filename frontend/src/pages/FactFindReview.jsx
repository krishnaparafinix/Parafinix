import { useEffect, useState } from 'react'
import { useNavigate, useParams } from 'react-router-dom'
import { getClient } from '../api/clients'
import { loadFactFind, saveFactFind } from '../lib/localFactFind'
import { emptyFactFind, normalizeFactFind, SIMPLE_SECTIONS, LIST_SECTIONS } from '../lib/factFindSchema'
import { apiErrorMessage } from '../api/client'
import Card from '../components/Card'
import Button from '../components/Button'
import FieldGroup from '../components/FieldGroup'
import RepeaterList from '../components/RepeaterList'
import FlagCallout from '../components/FlagCallout'

export default function FactFindReview() {
  const { clientId } = useParams()
  const navigate = useNavigate()

  const [client, setClient] = useState(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')
  const [data, setData] = useState(() => {
    const existing = loadFactFind(clientId)
    return existing ? normalizeFactFind(existing.data) : emptyFactFind()
  })
  const [flags, setFlags] = useState(() => loadFactFind(clientId)?.flags || [])
  const [saved, setSaved] = useState(false)

  // clientId can change without unmounting (e.g. browser back/forward), so
  // re-sync form state from localStorage explicitly rather than relying on
  // the useState initializers, which only run on first mount.
  useEffect(() => {
    const existing = loadFactFind(clientId)
    setData(existing ? normalizeFactFind(existing.data) : emptyFactFind())
    setFlags(existing?.flags || [])
    setSaved(false)
  }, [clientId])

  useEffect(() => {
    getClient(clientId)
      .then(setClient)
      .catch((err) => setError(apiErrorMessage(err, 'Could not load this client.')))
      .finally(() => setLoading(false))
  }, [clientId])

  const updateSimple = (sectionId, key, value) => {
    setSaved(false)
    setData((d) => ({ ...d, [sectionId]: { ...d[sectionId], [key]: value } }))
  }

  const updateList = (section, key, rows) => {
    setSaved(false)
    if (section) {
      setData((d) => ({ ...d, [section]: { ...d[section], [key]: rows } }))
    } else {
      setData((d) => ({ ...d, [key]: rows }))
    }
  }

  const persist = () => {
    saveFactFind(clientId, { data, flags })
    setSaved(true)
  }

  const handleSave = () => {
    persist()
  }

  const handleConfirm = () => {
    persist()
    navigate(`/clients/${clientId}`)
  }

  if (loading) return <p className="text-sm text-text-secondary">Loading…</p>
  if (error) return <Card className="border-red/30 bg-red/5 text-sm text-red">{error}</Card>

  return (
    <div className="space-y-6">
      <div>
        <button onClick={() => navigate(`/clients/${clientId}`)} className="mb-2 text-sm text-text-secondary hover:text-navy">← Back to {client?.client_name}</button>
        <h1 className="text-2xl font-bold text-navy">Fact-Find Review</h1>
        <p className="mt-1 text-text-secondary">Review and edit every extracted field before generating the report.</p>
      </div>

      <FlagCallout flags={flags} title="Flagged for review" />

      <div className="space-y-4">
        {SIMPLE_SECTIONS.map((section) => (
          <FieldGroup
            key={section.id}
            title={section.title}
            fields={section.fields}
            values={data[section.id]}
            onChange={(key, value) => updateSimple(section.id, key, value)}
          />
        ))}

        {LIST_SECTIONS.map((list) => (
          <RepeaterList
            key={list.key}
            title={list.title}
            fields={list.fields}
            items={list.section ? data[list.section][list.key] : data[list.key]}
            onChange={(rows) => updateList(list.section, list.key, rows)}
          />
        ))}
      </div>

      <div className="sticky bottom-4 flex items-center justify-end gap-3 rounded-xl border border-border bg-surface p-4 shadow-md">
        {saved && <span className="mr-auto text-sm text-emerald">Saved</span>}
        <Button variant="secondary" onClick={handleSave}>Save details</Button>
        <Button onClick={handleConfirm}>Confirm & continue to generate</Button>
      </div>
    </div>
  )
}
