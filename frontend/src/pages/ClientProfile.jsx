import { useEffect, useMemo, useState } from 'react'
import { useNavigate, useParams } from 'react-router-dom'
import { getClient, deleteClient } from '../api/clients'
import { saveCase, deleteCase, updateCaseStatus } from '../api/cases'
import { uploadPdf, extractFactFind, generateReport } from '../api/generate'
import { downloadFactFindDoc, downloadSuitabilityDoc, downloadComplianceDoc } from '../api/documents'
import { loadFactFind, saveFactFind } from '../lib/localFactFind'
import { factFindToNotes } from '../lib/factFindToNotes'
import { useTimedStages } from '../lib/useTimedStages'
import { apiErrorMessage } from '../api/client'
import { useAuth } from '../context/AuthContext'
import { nextStatus, statusStyle } from '../lib/rag'
import Card from '../components/Card'
import Button from '../components/Button'
import RAGBadge from '../components/RAGBadge'
import StatusBadge from '../components/StatusBadge'
import FlagCallout from '../components/FlagCallout'
import FileUploadZone from '../components/FileUploadZone'
import ConfirmModal from '../components/ConfirmModal'
import ProgressPipeline from '../components/ProgressPipeline'

const GENERATE_STAGES = [
  'Pass 1 of 3 — drafting client circumstances & objectives…',
  'Pass 2 of 3 — drafting recommendations…',
  'Pass 3 of 3 — drafting next steps & paraplanner check…',
  'Running the 28-point compliance review…',
]
const GENERATE_DURATIONS = [34000, 34000, 24000, 16000]

export default function ClientProfile() {
  const { clientId } = useParams()
  const navigate = useNavigate()
  const { user } = useAuth()

  const [client, setClient] = useState(null)
  const [cases, setCases] = useState([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')
  const [factFind, setFactFind] = useState(() => loadFactFind(clientId))

  const [entryMode, setEntryMode] = useState(null) // 'paste' | 'upload'
  const [notesInput, setNotesInput] = useState('')
  const [extracting, setExtracting] = useState(false)
  const [extractError, setExtractError] = useState('')

  const [reportMeta, setReportMeta] = useState({ adviser_name: '', firm_name: '', basis: 'Independent', charges: '', report_ref: '' })
  const [generating, setGenerating] = useState(false)
  const [generateError, setGenerateError] = useState('')
  const [confirmGenerate, setConfirmGenerate] = useState(false)
  const [viewingCase, setViewingCase] = useState(null)
  const [deletingClient, setDeletingClient] = useState(false)
  const [downloadError, setDownloadError] = useState('')

  const runDownload = (fn) => async () => {
    setDownloadError('')
    try {
      await fn()
    } catch (err) {
      setDownloadError(apiErrorMessage(err, 'Could not generate that document. Please try again.'))
    }
  }

  const stageIndex = useTimedStages(generating, GENERATE_DURATIONS)

  const loadClient = () => {
    setLoading(true)
    setError('')
    // getClient() already embeds this client's cases — no need for a second,
    // fully redundant GET /clients/{id}/cases call on top of it.
    getClient(clientId)
      .then((clientData) => {
        setClient(clientData)
        setCases(clientData.cases || [])
      })
      .catch((err) => setError(apiErrorMessage(err, 'Could not load this client.')))
      .finally(() => setLoading(false))
  }

  useEffect(loadClient, [clientId])

  // clientId can change without unmounting (e.g. browser back/forward between
  // two client profiles), so re-read localStorage explicitly rather than
  // relying on the useState initializer, which only runs on first mount.
  useEffect(() => {
    setFactFind(loadFactFind(clientId))
  }, [clientId])

  useEffect(() => {
    setReportMeta((m) => ({
      ...m,
      adviser_name: m.adviser_name || user?.full_name || '',
      firm_name: m.firm_name || user?.firm_name || '',
    }))
  }, [user])

  const flags = factFind?.flags || []

  const summary = useMemo(() => {
    if (!factFind?.data) return null
    const p = factFind.data.personal || {}
    const obj = factFind.data.objectives || {}
    return {
      names: [p.client1_name, p.client2_name].filter(Boolean).join(' & ') || 'Unnamed client',
      employment: [p.client1_employment, p.client2_employment].filter(Boolean).join(' / ') || '—',
      objective: obj.primary_objective || '—',
      flagCount: flags.length,
    }
  }, [factFind, flags])

  const runExtract = async (notes) => {
    setExtracting(true)
    setExtractError('')
    try {
      const { data, flags: extractedFlags } = await extractFactFind(notes)
      saveFactFind(clientId, { data, flags: extractedFlags })
      navigate(`/clients/${clientId}/fact-find`)
    } catch (err) {
      setExtractError(apiErrorMessage(err, 'Extraction failed. Please try again.'))
    } finally {
      setExtracting(false)
    }
  }

  const handlePdfUpload = async (file) => {
    setExtracting(true)
    setExtractError('')
    try {
      const uploaded = await uploadPdf(file)
      if (!uploaded.success || !uploaded.extracted_text?.trim()) {
        throw new Error('Could not read any text from that PDF. Try pasting the notes instead.')
      }
      await runExtract(uploaded.extracted_text)
    } catch (err) {
      setExtractError(apiErrorMessage(err, 'Upload failed. Please try again.'))
      setExtracting(false)
    }
  }

  const doGenerate = async () => {
    setConfirmGenerate(false)
    setGenerating(true)
    setGenerateError('')
    try {
      const notes = factFindToNotes(factFind.data)
      const result = await generateReport({
        client_name: client.client_name,
        adviser_name: reportMeta.adviser_name,
        firm_name: reportMeta.firm_name,
        basis: reportMeta.basis,
        charges: reportMeta.charges,
        report_ref: reportMeta.report_ref,
        notes,
      })
      const saved = await saveCase(clientId, {
        case_title: `${client.client_name} — Suitability Report`,
        fact_find: notes,
        report_part1: result.part1,
        report_part2: result.part2,
        report_part3: result.part3,
        report_part4: result.part4,
        compliance_result: result.check_text,
        rag_rating: result.rag_rating,
        passes: result.passes,
        flags: result.flags,
        fails: result.fails,
        firm_name: reportMeta.firm_name,
        adviser_name: reportMeta.adviser_name,
        basis: reportMeta.basis,
        charges: reportMeta.charges,
        report_ref: reportMeta.report_ref,
        status: 'draft',
      })
      setCases((prev) => [saved, ...prev])
    } catch (err) {
      setGenerateError(apiErrorMessage(err, 'Report generation failed. Please try again.'))
    } finally {
      setGenerating(false)
    }
  }

  const handleGenerateClick = () => {
    if (flags.length > 0) setConfirmGenerate(true)
    else doGenerate()
  }

  const handleDeleteClient = async () => {
    if (!confirm(`Delete ${client.client_name} and all associated reports? This cannot be undone.`)) return
    setDeletingClient(true)
    try {
      await deleteClient(clientId)
      navigate('/')
    } catch (err) {
      setError(apiErrorMessage(err, 'Could not delete client.'))
      setDeletingClient(false)
    }
  }

  if (loading) return <p className="text-sm text-text-secondary">Loading client…</p>
  if (error) return <Card className="border-red/30 bg-red/5 text-sm text-red">{error}</Card>
  if (!client) return null

  return (
    <div className="space-y-8">
      <div className="flex items-start justify-between">
        <div>
          <button onClick={() => navigate('/')} className="mb-2 text-sm text-text-secondary hover:text-navy">← Back to dashboard</button>
          <h1 className="text-2xl font-bold text-navy">{client.client_name}</h1>
          <p className="mt-1 text-sm text-text-secondary">
            {client.email || 'No email on file'}{client.phone ? ` · ${client.phone}` : ''}
          </p>
        </div>
        <div className="flex items-center gap-3">
          {client.latest_rag && <RAGBadge rag={client.latest_rag} />}
          <Button variant="danger" size="sm" onClick={handleDeleteClient} loading={deletingClient}>Delete client</Button>
        </div>
      </div>

      {/* A. Client details block */}
      <section>
        <h2 className="mb-4 text-lg font-semibold text-navy">Client details</h2>
        {summary ? (
          <Card>
            <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-4">
              <div>
                <p className="text-xs font-medium uppercase tracking-wide text-text-secondary">Client(s)</p>
                <p className="mt-1 font-medium text-navy">{summary.names}</p>
              </div>
              <div>
                <p className="text-xs font-medium uppercase tracking-wide text-text-secondary">Employment</p>
                <p className="mt-1 font-medium text-navy">{summary.employment}</p>
              </div>
              <div>
                <p className="text-xs font-medium uppercase tracking-wide text-text-secondary">Primary objective</p>
                <p className="mt-1 font-medium text-navy">{summary.objective}</p>
              </div>
              <div>
                <p className="text-xs font-medium uppercase tracking-wide text-text-secondary">Flags</p>
                <p className={`mt-1 font-medium ${summary.flagCount > 0 ? 'text-amber' : 'text-emerald'}`}>
                  {summary.flagCount > 0 ? `${summary.flagCount} to review` : 'None'}
                </p>
              </div>
            </div>
            <div className="mt-5 border-t border-border pt-4">
              <Button variant="outline" size="sm" onClick={() => navigate(`/clients/${clientId}/fact-find`)}>
                View / edit full details
              </Button>
            </div>
          </Card>
        ) : (
          <FactFindEntryPrompt
            navigate={navigate}
            clientId={clientId}
            entryMode={entryMode}
            setEntryMode={setEntryMode}
            notesInput={notesInput}
            setNotesInput={setNotesInput}
            extracting={extracting}
            extractError={extractError}
            onPaste={() => runExtract(notesInput)}
            onUpload={handlePdfUpload}
          />
        )}
      </section>

      {/* B. Generate documents block */}
      <section>
        <h2 className="mb-4 text-lg font-semibold text-navy">Generate documents</h2>
        <div className="grid grid-cols-1 gap-4 lg:grid-cols-2">
          <Card>
            <h3 className="font-semibold text-navy">Fact-Find Document</h3>
            <p className="mt-1 text-sm text-text-secondary">
              {summary ? 'Download the fact-find using the saved details.' : 'No details saved yet — this downloads a blank template.'}
            </p>
            <div className="mt-4 flex flex-wrap gap-3">
              <Button
                variant="secondary"
                size="sm"
                onClick={runDownload(() => downloadFactFindDoc({
                  client_name: client.client_name,
                  adviser_name: reportMeta.adviser_name,
                  firm_name: reportMeta.firm_name,
                  fact_find_data: factFind?.data || {},
                  client_facing: false,
                }))}
              >
                Internal copy
              </Button>
              <Button
                variant="secondary"
                size="sm"
                onClick={runDownload(() => downloadFactFindDoc({
                  client_name: client.client_name,
                  adviser_name: reportMeta.adviser_name,
                  firm_name: reportMeta.firm_name,
                  fact_find_data: factFind?.data || {},
                  client_facing: true,
                }))}
              >
                Client copy
              </Button>
            </div>
            {downloadError && <p className="mt-3 text-sm text-red">{downloadError}</p>}
          </Card>

          <Card>
            <h3 className="font-semibold text-navy">Suitability + Compliance Report</h3>
            <p className="mt-1 text-sm text-text-secondary">Runs the 3-pass drafting pipeline plus a COBS 9A compliance review.</p>
            <div className="mt-4 grid grid-cols-2 gap-3">
              <input placeholder="Adviser name" value={reportMeta.adviser_name}
                onChange={(e) => setReportMeta((m) => ({ ...m, adviser_name: e.target.value }))}
                className="rounded-lg border border-border px-3 py-2 text-sm outline-none focus:border-brand-blue focus:ring-2 focus:ring-brand-blue/20" />
              <input placeholder="Firm name" value={reportMeta.firm_name}
                onChange={(e) => setReportMeta((m) => ({ ...m, firm_name: e.target.value }))}
                className="rounded-lg border border-border px-3 py-2 text-sm outline-none focus:border-brand-blue focus:ring-2 focus:ring-brand-blue/20" />
              <select value={reportMeta.basis}
                onChange={(e) => setReportMeta((m) => ({ ...m, basis: e.target.value }))}
                className="rounded-lg border border-border px-3 py-2 text-sm outline-none focus:border-brand-blue focus:ring-2 focus:ring-brand-blue/20">
                <option>Independent</option>
                <option>Restricted</option>
              </select>
              <input placeholder="Report ref" value={reportMeta.report_ref}
                onChange={(e) => setReportMeta((m) => ({ ...m, report_ref: e.target.value }))}
                className="rounded-lg border border-border px-3 py-2 text-sm outline-none focus:border-brand-blue focus:ring-2 focus:ring-brand-blue/20" />
              <input placeholder="Charges" value={reportMeta.charges}
                onChange={(e) => setReportMeta((m) => ({ ...m, charges: e.target.value }))}
                className="col-span-2 rounded-lg border border-border px-3 py-2 text-sm outline-none focus:border-brand-blue focus:ring-2 focus:ring-brand-blue/20" />
            </div>

            {generateError && <p className="mt-3 text-sm text-red">{generateError}</p>}

            <Button
              className="mt-4 w-full"
              disabled={!summary || generating}
              loading={generating}
              onClick={handleGenerateClick}
            >
              Generate report
            </Button>
          </Card>
        </div>

        {/* C. Generation progress */}
        {generating && (
          <Card className="mt-4">
            <ProgressPipeline stages={GENERATE_STAGES} currentIndex={stageIndex} />
          </Card>
        )}
      </section>

      {/* D. Report history */}
      <section>
        <h2 className="mb-4 text-lg font-semibold text-navy">Report history</h2>
        {cases.length === 0 ? (
          <Card className="text-center text-text-secondary">No reports generated yet.</Card>
        ) : (
          <div className="space-y-3">
            {cases.map((c) => (
              <ReportRow
                key={c.id}
                caseItem={c}
                client={client}
                reportMeta={reportMeta}
                onView={() => setViewingCase(c)}
                onChanged={loadClient}
                runDownload={runDownload}
              />
            ))}
          </div>
        )}
      </section>

      <ConfirmModal
        open={confirmGenerate}
        title="Some details are missing"
        message={`This client has ${flags.length} flagged item${flags.length === 1 ? '' : 's'} in their fact-find. Generate the report anyway?`}
        confirmLabel="Generate anyway"
        onConfirm={doGenerate}
        onCancel={() => setConfirmGenerate(false)}
      />

      {viewingCase && (
        <ReportViewer caseItem={viewingCase} onClose={() => setViewingCase(null)} />
      )}
    </div>
  )
}

function FactFindEntryPrompt({ navigate, clientId, entryMode, setEntryMode, notesInput, setNotesInput, extracting, extractError, onPaste, onUpload }) {
  return (
    <Card>
      <p className="text-sm text-text-secondary">No fact-find details saved for this client yet. Get started with one of the options below:</p>
      <div className="mt-4 grid grid-cols-1 gap-3 sm:grid-cols-3">
        <Button variant="secondary" onClick={() => navigate(`/clients/${clientId}/fact-find`)}>
          Type details directly
        </Button>
        <Button variant="secondary" onClick={() => setEntryMode(entryMode === 'upload' ? null : 'upload')}>
          Upload a document
        </Button>
        <Button variant="secondary" onClick={() => setEntryMode(entryMode === 'paste' ? null : 'paste')}>
          Paste meeting notes
        </Button>
      </div>

      {entryMode === 'upload' && (
        <div className="mt-4">
          <FileUploadZone onFile={onUpload} disabled={extracting} />
        </div>
      )}

      {entryMode === 'paste' && (
        <div className="mt-4">
          <textarea
            rows={8}
            value={notesInput}
            onChange={(e) => setNotesInput(e.target.value)}
            placeholder="Paste raw meeting notes here…"
            disabled={extracting}
            className="w-full rounded-lg border border-border px-3 py-2.5 text-sm outline-none focus:border-brand-blue focus:ring-2 focus:ring-brand-blue/20"
          />
          <Button className="mt-3" onClick={onPaste} loading={extracting} disabled={!notesInput.trim()}>
            Extract fact-find data
          </Button>
        </div>
      )}

      {extracting && entryMode === 'upload' && (
        <p className="mt-3 text-sm text-text-secondary">Reading document and extracting structured data…</p>
      )}
      {extractError && <p className="mt-3 text-sm text-red">{extractError}</p>}
    </Card>
  )
}

function ReportRow({ caseItem, client, reportMeta, onView, onChanged, runDownload }) {
  const [busy, setBusy] = useState(false)
  const upcoming = nextStatus(caseItem.status)

  const advance = async () => {
    if (!upcoming) return
    setBusy(true)
    try {
      await updateCaseStatus(caseItem.id, upcoming)
      onChanged()
    } finally {
      setBusy(false)
    }
  }

  const remove = async () => {
    if (!confirm('Delete this report? This cannot be undone.')) return
    setBusy(true)
    try {
      await deleteCase(caseItem.id)
      onChanged()
    } finally {
      setBusy(false)
    }
  }

  return (
    <Card className="flex flex-wrap items-center justify-between gap-4">
      <div>
        <p className="font-medium text-navy">{caseItem.case_title} <span className="text-text-secondary">· v{caseItem.version}</span></p>
        <p className="mt-1 text-xs text-text-secondary">{new Date(caseItem.created_at).toLocaleDateString('en-GB', { day: 'numeric', month: 'short', year: 'numeric' })}</p>
      </div>
      <div className="flex items-center gap-3">
        <RAGBadge rag={caseItem.rag_rating} size="sm" />
        <StatusBadge status={caseItem.status} />
      </div>
      <div className="flex flex-wrap items-center gap-2">
        <Button size="sm" variant="ghost" onClick={onView}>View</Button>
        <Button size="sm" variant="secondary" onClick={runDownload(() => downloadSuitabilityDoc({
          client_name: client.client_name,
          adviser_name: caseItem.adviser_name || reportMeta.adviser_name,
          firm_name: caseItem.firm_name || reportMeta.firm_name,
          basis: caseItem.basis,
          charges: caseItem.charges,
          report_ref: caseItem.report_ref,
          report_part1: caseItem.report_part1,
          report_part2: caseItem.report_part2,
          report_part3: caseItem.report_part3,
          report_part4: caseItem.report_part4,
        }))}>
          Suitability .docx
        </Button>
        <Button size="sm" variant="secondary" onClick={runDownload(() => downloadComplianceDoc({
          client_name: client.client_name,
          adviser_name: caseItem.adviser_name || reportMeta.adviser_name,
          firm_name: caseItem.firm_name || reportMeta.firm_name,
          report_ref: caseItem.report_ref,
          check_text: caseItem.compliance_result,
          passes: caseItem.passes,
          flags: caseItem.flags,
          fails: caseItem.fails,
        }))}>
          Compliance .docx
        </Button>
        {upcoming && (
          <Button size="sm" variant="outline" onClick={advance} loading={busy}>
            Mark {statusStyle(upcoming).label}
          </Button>
        )}
        <Button size="sm" variant="danger" onClick={remove} loading={busy}>Delete</Button>
      </div>
    </Card>
  )
}

function ReportViewer({ caseItem, onClose }) {
  const [tab, setTab] = useState('report')
  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-navy/40 p-4" onClick={onClose}>
      <div className="flex h-[85vh] w-full max-w-3xl flex-col animate-fade-in-up rounded-xl bg-surface shadow-lg" onClick={(e) => e.stopPropagation()}>
        <div className="flex items-center justify-between border-b border-border px-6 py-4">
          <h3 className="font-semibold text-navy">{caseItem.case_title}</h3>
          <button onClick={onClose} className="text-text-secondary hover:text-navy">✕</button>
        </div>
        <div className="flex gap-2 border-b border-border px-6 pt-3">
          <button onClick={() => setTab('report')} className={`border-b-2 px-2 pb-2 text-sm font-medium ${tab === 'report' ? 'border-emerald text-navy' : 'border-transparent text-text-secondary'}`}>Suitability Report</button>
          <button onClick={() => setTab('compliance')} className={`border-b-2 px-2 pb-2 text-sm font-medium ${tab === 'compliance' ? 'border-emerald text-navy' : 'border-transparent text-text-secondary'}`}>Compliance Review</button>
        </div>
        <div className="flex-1 overflow-y-auto px-6 py-4">
          <pre className="whitespace-pre-wrap font-sans text-sm leading-relaxed text-navy">
            {tab === 'report'
              ? [caseItem.report_part1, caseItem.report_part2, caseItem.report_part3, caseItem.report_part4].filter(Boolean).join('\n\n')
              : caseItem.compliance_result || 'No compliance data recorded for this report.'}
          </pre>
        </div>
      </div>
    </div>
  )
}
