import { useEffect, useMemo, useRef, useState } from 'react'
import { useNavigate, useParams } from 'react-router-dom'
import { getClient } from '../api/clients'
import { saveCase } from '../api/cases'
import { generateReport } from '../api/generate'
import { rerunCompliance } from '../api/aiChat'
import { downloadFactFindDoc, downloadSuitabilityDoc, downloadComplianceDoc } from '../api/documents'
import { loadFactFind, saveFactFind } from '../lib/localFactFind'
import { factFindToNotes } from '../lib/factFindToNotes'
import { apiErrorMessage } from '../api/client'
import { useAuth } from '../context/AuthContext'
import { color, font, docAccent } from '../lib/theme'
import { formatDate, reportStatusBadge } from '../lib/format'
import Topbar from '../components/layout/Topbar'
import PageContainer from '../components/layout/PageContainer'
import Avatar from '../components/ui/Avatar'
import GenerateModal from '../components/GenerateModal'
import FactFindDrawer from '../components/FactFindDrawer'
import FactFindEntryModal from '../components/FactFindEntryModal'
import EditClientModal from '../components/EditClientModal'
import ChatWidget from '../components/ChatWidget'

function formatMoney(v) {
  if (v === null || v === undefined || v === '') return '—'
  return '£' + Number(v).toLocaleString('en-GB', { maximumFractionDigits: 0 })
}

const DOC_CARDS = [
  { key: 'factfind', code: 'FF', title: 'Fact-Find', desc: 'Structured data extraction' },
  { key: 'suitability', code: 'SR', title: 'Suitability Report', desc: 'Full advised recommendation', hero: true },
  { key: 'compliance', code: 'CR', title: 'Compliance Report', desc: 'FCA-aligned review' },
]

export default function ClientProfile() {
  const { clientId } = useParams()
  const navigate = useNavigate()
  const { user } = useAuth()

  const [client, setClient] = useState(null)
  const [cases, setCases] = useState([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')
  const [factFind, setFactFind] = useState(null)

  const [showDrawer, setShowDrawer] = useState(false)
  const [showEntry, setShowEntry] = useState(false)
  const [entryThen, setEntryThen] = useState(null) // 'factfind-download' | null — chains into the FF generate flow
  const [showEdit, setShowEdit] = useState(false)
  const [activeGenerate, setActiveGenerate] = useState(null)
  const [generateError, setGenerateError] = useState('')
  const [newRowId, setNewRowId] = useState(null)
  const lastGenerated = useRef(null) // holds the case data behind the modal's "Download" button

  const load = () => {
    setLoading(true)
    setError('')
    getClient(clientId)
      .then((data) => { setClient(data); setCases(data.cases || []) })
      .catch((err) => setError(apiErrorMessage(err, 'Could not load this client.')))
      .finally(() => setLoading(false))
  }

  useEffect(load, [clientId])
  useEffect(() => { setFactFind(loadFactFind(clientId)) }, [clientId])

  const latestCase = cases[0] || null

  const keyFacts = useMemo(() => {
    const p = factFind?.data?.personal
    const risk = factFind?.data?.risk
    const obj = factFind?.data?.objectives
    return {
      dob: p?.client1_dob || '—',
      risk: risk?.profile_assigned || '—',
      objective: obj?.primary_objective || '—',
    }
  }, [factFind])

  const handleExtracted = ({ data, flags }) => {
    saveFactFind(clientId, { data, flags })
    setFactFind(loadFactFind(clientId))
    setShowEntry(false)
    if (entryThen === 'factfind-download') {
      setEntryThen(null)
      setActiveGenerate('factfind')
    }
  }

  const runSuitability = async () => {
    const notes = factFindToNotes(factFind.data)
    const result = await generateReport({
      client_name: client.client_name,
      adviser_name: user?.full_name || '',
      firm_name: user?.firm_name || '',
      basis: 'Independent',
      charges: '',
      report_ref: '',
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
      firm_name: user?.firm_name || '',
      adviser_name: user?.full_name || '',
      basis: 'Independent',
      status: 'draft',
    })
    setCases((prev) => [saved, ...prev])
    setNewRowId(saved.id)
    lastGenerated.current = saved
    return saved
  }

  const runCompliance = async () => {
    const result = await rerunCompliance(latestCase.id)
    const updated = { ...latestCase, compliance_result: result.check_text, passes: result.passes, flags: result.flags, fails: result.fails, rag_rating: result.rag_rating }
    setCases((prev) => prev.map((c) => (c.id === latestCase.id ? updated : c)))
    setNewRowId(latestCase.id)
    lastGenerated.current = updated
    return result
  }

  const runFactFindDoc = async () => {
    await downloadFactFindDoc({
      client_name: client.client_name,
      adviser_name: user?.full_name || '',
      firm_name: user?.firm_name || '',
      fact_find_data: factFind.data,
      client_facing: false,
    })
    return {}
  }

  const downloadFor = (key) => {
    if (key === 'factfind') return runFactFindDoc
    const c = lastGenerated.current
    if (!c) return null
    if (key === 'suitability') {
      return () => downloadSuitabilityDoc({
        client_name: client.client_name,
        adviser_name: c.adviser_name,
        firm_name: c.firm_name,
        basis: c.basis,
        charges: c.charges,
        report_ref: c.report_ref,
        report_part1: c.report_part1,
        report_part2: c.report_part2,
        report_part3: c.report_part3,
        report_part4: c.report_part4,
      })
    }
    return () => downloadComplianceDoc({
      client_name: client.client_name,
      adviser_name: c.adviser_name,
      firm_name: c.firm_name,
      report_ref: c.report_ref,
      check_text: c.compliance_result,
      passes: c.passes,
      flags: c.flags,
      fails: c.fails,
    })
  }

  const handleGenerateClick = (key) => {
    setGenerateError('')
    if (key === 'factfind') {
      if (!factFind) { setEntryThen('factfind-download'); setShowEntry(true); return }
      setActiveGenerate('factfind')
      return
    }
    if (key === 'suitability') {
      if (!factFind) { setGenerateError('Add fact-find data before generating a Suitability Report.'); return }
      setActiveGenerate('suitability')
      return
    }
    if (key === 'compliance') {
      if (!latestCase) { setGenerateError('Generate a Suitability Report first — compliance reruns against the latest report on file.'); return }
      setActiveGenerate('compliance')
    }
  }

  const taskFor = (key) => {
    if (key === 'factfind') return runFactFindDoc
    if (key === 'suitability') return runSuitability
    return runCompliance
  }

  const titleFor = (key) => DOC_CARDS.find((d) => d.key === key)?.title || ''
  const subtitleFor = (key) => {
    if (key === 'factfind') return { running: 'Building the fact-find document…', done: 'Downloaded to your device.' }
    if (key === 'suitability') return { running: 'AI is reading your notes and drafting…', done: 'Saved to report history — download below, or find it there any time.' }
    return { running: 'Rerunning the 28-point compliance check…', done: 'Compliance rating updated on the latest report — download below.' }
  }

  if (loading) return <div style={{ padding: 34, color: color.textFaint, fontSize: 13 }}>Loading client…</div>
  if (error) return <div style={{ padding: 34 }}><div style={{ background: 'rgba(199,57,57,0.08)', border: '1px solid rgba(199,57,57,0.3)', borderRadius: 12, padding: 16, fontSize: 13, color: '#e08787' }}>{error}</div></div>
  if (!client) return null

  const isActiveClient = cases.length > 0
  const slug = client.client_name.toLowerCase().replace(/[^a-z0-9]+/g, '_')

  return (
    <>
      <Topbar
        breadcrumb={[{ label: 'clients', href: '/clients' }, { label: slug }]}
        ghost={{ label: 'Edit client', onClick: () => setShowEdit(true) }}
        primary={{ label: '+ New document', onClick: () => handleGenerateClick('suitability') }}
      />
      <PageContainer gap={24}>
        <div
          className="pfx-tilt"
          onClick={() => (factFind ? setShowDrawer(true) : setShowEntry(true))}
          style={{ background: 'linear-gradient(150deg,#181b1f,#131518)', border: `1px solid ${color.border}`, borderRadius: 14, padding: 26, display: 'flex', gap: 22, alignItems: 'flex-start', cursor: 'pointer' }}
        >
          <Avatar name={client.client_name} tone={isActiveClient ? 'teal' : 'flat'} size={64} radius={14} style={{ fontSize: 24, boxShadow: isActiveClient ? '0 8px 20px -8px rgba(95,208,196,0.5)' : 'none' }} />
          <div style={{ flex: 1 }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: 12, flexWrap: 'wrap' }}>
              <h2 style={{ fontFamily: font.display, fontSize: 24, fontWeight: 600, color: color.textPrimary, margin: 0, letterSpacing: '-0.01em' }}>{client.client_name}</h2>
              {isActiveClient && (
                <span style={{ fontSize: 11, fontWeight: 500, color: color.teal, background: color.tealSoftBg, border: `1px solid ${color.tealSoftBorder}`, padding: '3px 9px', borderRadius: 6, display: 'inline-flex', alignItems: 'center', gap: 6 }}>
                  <span style={{ width: 6, height: 6, borderRadius: '50%', background: color.teal, animation: 'pfx-pulse 1.8s ease-in-out infinite' }} />
                  Active client
                </span>
              )}
            </div>
            <div style={{ display: 'flex', alignItems: 'center', gap: 12, flexWrap: 'wrap', marginTop: 6 }}>
              <div style={{ fontFamily: font.mono, fontSize: 11.5, color: color.textFaint }}>
                PFX-{client.id.replace(/-/g, '').slice(0, 5).toUpperCase()} · onboarded {formatDate(client.created_at)}
              </div>
              <span className="pfx-ff-hint" style={{ fontFamily: font.mono, fontSize: 10, letterSpacing: '0.08em', color: '#8a8f96', border: `1px solid ${color.borderRaised}`, borderRadius: 6, padding: '3px 8px' }}>
                {factFind ? 'FULL FACT-FIND ON FILE →' : 'NO FACT-FIND ON FILE — ADD →'}
              </span>
            </div>
            <div style={{ display: 'grid', gridTemplateColumns: 'repeat(4,1fr)', gap: 18, marginTop: 22 }}>
              <Fact label="Date of birth" value={keyFacts.dob} mono />
              <Fact label="Risk" value={keyFacts.risk} />
              <Fact label="Portfolio" value={formatMoney(client.portfolio_value)} mono color={color.teal} />
              <Fact label="Objective" value={keyFacts.objective} />
            </div>
          </div>
        </div>

        <div>
          <div style={{ display: 'flex', alignItems: 'baseline', justifyContent: 'space-between', marginBottom: 14 }}>
            <h3 style={{ fontFamily: font.display, fontSize: 16, fontWeight: 600, color: color.textPrimary, margin: 0, letterSpacing: '-0.01em' }}>Generate document</h3>
            <span style={{ fontSize: 12, color: color.textFaint, fontFamily: font.mono }}>source: notes + fact-find</span>
          </div>
          {generateError && <p style={{ fontSize: 12.5, color: '#e08787', marginBottom: 12 }}>{generateError}</p>}
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(3,1fr)', gap: 16 }}>
            {DOC_CARDS.map((d) => {
              const acc = docAccent[d.key]
              const btnClass = d.key === 'suitability' ? 'pfx-btn-amber' : 'pfx-btn-teal'
              return (
                <div
                  key={d.key}
                  className={`pfx-tilt ${d.hero ? 'pfx-tilt-hero' : 'pfx-tilt-glow'}`}
                  style={{
                    background: d.hero ? 'linear-gradient(160deg,#2a2018,#16181b 70%)' : color.card,
                    border: `1px solid ${d.hero ? '#6a4c22' : color.border}`,
                    borderRadius: 13, padding: 20, display: 'flex', flexDirection: 'column', gap: 14, cursor: 'pointer', position: 'relative', overflow: 'hidden',
                  }}
                >
                  {d.hero && (
                    <div style={{ position: 'absolute', top: 14, right: 14, fontFamily: font.mono, fontSize: 9, letterSpacing: '0.12em', color: color.amber, background: color.amberSoftBg, border: `1px solid ${color.amberSoftBorder}`, padding: '3px 7px', borderRadius: 5 }}>
                      RECOMMENDED
                    </div>
                  )}
                  <div
                    className="pfx-doc-icon"
                    style={{
                      width: 36, height: 36, borderRadius: 10,
                      background: d.hero ? `linear-gradient(150deg,${color.amberLight},${color.amber})` : color.raised,
                      border: d.hero ? 'none' : `1px solid ${color.borderRaised}`,
                      display: 'flex', alignItems: 'center', justifyContent: 'center',
                      fontFamily: font.mono, fontSize: 12, fontWeight: d.hero ? 700 : 600,
                      color: d.hero ? color.ink : color.teal,
                      animation: d.hero ? 'pfx-float 3.4s ease-in-out infinite' : 'none',
                      boxShadow: d.hero ? '0 8px 18px -6px rgba(199,137,63,0.5)' : 'none',
                    }}
                  >
                    {d.code}
                  </div>
                  <div>
                    <div style={{ fontSize: 15, fontWeight: 600, color: color.textPrimary }}>{d.title}</div>
                    <div style={{ fontSize: 12, color: d.hero ? '#c9b79a' : color.textFaint, lineHeight: 1.45, marginTop: 4 }}>{d.desc}</div>
                  </div>
                  <div
                    className={`pfx-btn ${btnClass} pfx-sheen`}
                    onClick={() => handleGenerateClick(d.key)}
                    style={{ marginTop: 'auto', fontSize: 12.5, fontWeight: 600, color: color.ink, background: d.key === 'suitability' ? color.amber : color.teal, borderRadius: 8, padding: '9px 0', textAlign: 'center' }}
                  >
                    Generate <span className="pfx-arrow">→</span>
                  </div>
                </div>
              )
            })}
          </div>
        </div>

        <div>
          <h3 style={{ fontFamily: font.display, fontSize: 16, fontWeight: 600, color: color.textPrimary, margin: '0 0 14px', letterSpacing: '-0.01em' }}>Report history</h3>
          <div style={{ background: color.card, border: `1px solid ${color.border}`, borderRadius: 13, overflow: 'hidden' }}>
            <div style={{ display: 'grid', gridTemplateColumns: '1.7fr 1fr 1fr 0.9fr 40px', gap: 12, padding: '12px 20px', background: color.rail, fontFamily: font.mono, fontSize: 10, letterSpacing: '0.12em', textTransform: 'uppercase', color: color.textFainter }}>
              <div>Document</div><div>Type</div><div>Date</div><div>Status</div><div />
            </div>
            {cases.length === 0 ? (
              <div style={{ padding: '18px 20px', fontSize: 13, color: color.textFaint }}>No reports generated yet.</div>
            ) : cases.map((c, i) => {
              const badge = reportStatusBadge(c.status)
              const isNew = c.id === newRowId
              return (
                <div
                  key={c.id}
                  className="pfx-row"
                  style={{
                    display: 'grid', gridTemplateColumns: '1.7fr 1fr 1fr 0.9fr 40px', gap: 12, padding: '15px 20px',
                    borderTop: i === 0 ? 'none' : `1px solid ${color.borderSubtle}`, alignItems: 'center', fontSize: 13, color: color.textSecondary,
                    animation: isNew ? 'pfx-newrow 1.4s ease' : 'none',
                  }}
                >
                  <div style={{ fontWeight: 500, color: color.textPrimary, overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>{c.case_title}</div>
                  <div style={{ color: color.textMuted }}>Suitability</div>
                  <div style={{ color: color.textMuted, fontFamily: font.mono, fontSize: 12 }}>{formatDate(c.created_at)}</div>
                  <div><span style={{ fontSize: 11, color: badge.tone === 'teal' ? color.teal : color.amber, background: badge.tone === 'teal' ? color.tealSoftBg : color.amberSoftBg, padding: '2px 9px', borderRadius: 6 }}>{badge.label}</span></div>
                  <div
                    className="pfx-dl"
                    onClick={() => downloadSuitabilityDoc({
                      client_name: client.client_name,
                      adviser_name: c.adviser_name,
                      firm_name: c.firm_name,
                      basis: c.basis,
                      charges: c.charges,
                      report_ref: c.report_ref,
                      report_part1: c.report_part1,
                      report_part2: c.report_part2,
                      report_part3: c.report_part3,
                      report_part4: c.report_part4,
                    }).catch((err) => setGenerateError(apiErrorMessage(err, 'Could not download that document.')))}
                    style={{ color: color.teal, textAlign: 'center' }}
                    title="Download Suitability Report"
                  >
                    ↓
                  </div>
                </div>
              )
            })}
          </div>
        </div>
      </PageContainer>

      {activeGenerate && (
        <GenerateModal
          docKey={activeGenerate}
          title={titleFor(activeGenerate)}
          subtitle={subtitleFor(activeGenerate)}
          task={taskFor(activeGenerate)}
          onDownload={downloadFor(activeGenerate)}
          onClose={() => setActiveGenerate(null)}
        />
      )}

      {showDrawer && factFind && (
        <FactFindDrawer
          client={client}
          factFind={factFind}
          onClose={() => setShowDrawer(false)}
          onSave={(data) => { saveFactFind(clientId, { data, flags: factFind.flags }); setFactFind(loadFactFind(clientId)) }}
        />
      )}

      {showEntry && <FactFindEntryModal onClose={() => { setShowEntry(false); setEntryThen(null) }} onExtracted={handleExtracted} />}
      {showEdit && (
        <EditClientModal
          client={client}
          onClose={() => setShowEdit(false)}
          onSaved={(updated) => { setClient((c) => ({ ...c, ...updated })); setShowEdit(false) }}
          onDeleted={() => navigate('/clients')}
        />
      )}

      <ChatWidget />
    </>
  )
}

function Fact({ label, value, mono, color: c }) {
  return (
    <div>
      <div style={{ fontFamily: font.mono, fontSize: 10, letterSpacing: '0.12em', textTransform: 'uppercase', color: color.textFainter }}>{label}</div>
      <div style={{ fontSize: 15, color: c || color.textPrimary, marginTop: 5, fontWeight: 500, fontFamily: mono ? font.mono : font.body }}>{value}</div>
    </div>
  )
}
