import { useEffect, useMemo, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { listAllCases } from '../api/cases'
import { getDashboardStats } from '../api/clients'
import { downloadSuitabilityDoc } from '../api/documents'
import { apiErrorMessage } from '../api/client'
import { color, font } from '../lib/theme'
import { formatDate, reportStatusBadge } from '../lib/format'
import Topbar from '../components/layout/Topbar'
import PageContainer from '../components/layout/PageContainer'
import SearchInput from '../components/ui/SearchInput'
import Chip from '../components/ui/Chip'
import ChatWidget from '../components/ChatWidget'

const FILTERS = ['All', 'In review', 'Finalised']

export default function Reports() {
  const navigate = useNavigate()
  const [cases, setCases] = useState([])
  const [stats, setStats] = useState(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')
  const [search, setSearch] = useState('')
  const [filter, setFilter] = useState('All')
  const [downloadError, setDownloadError] = useState('')

  useEffect(() => {
    setLoading(true)
    setError('')
    Promise.all([listAllCases(), getDashboardStats()])
      .then(([caseData, statsData]) => { setCases(caseData.cases || []); setStats(statsData) })
      .catch((err) => setError(apiErrorMessage(err, 'Could not load reports.')))
      .finally(() => setLoading(false))
  }, [])

  const rows = useMemo(() => cases.map((c) => ({ ...c, statusBadge: reportStatusBadge(c.status) })), [cases])

  const filtered = useMemo(() => {
    const q = search.trim().toLowerCase()
    return rows.filter((r) => {
      if (filter === 'In review' && r.statusBadge.label !== 'In review') return false
      if (filter === 'Finalised' && r.statusBadge.label !== 'Finalised') return false
      if (!q) return true
      return (r.case_title || '').toLowerCase().includes(q) || (r.client_name || '').toLowerCase().includes(q)
    })
  }, [rows, search, filter])

  const finalisedCount = rows.filter((r) => r.statusBadge.label === 'Finalised').length
  const inReviewCount = rows.filter((r) => r.statusBadge.label === 'In review').length

  const handleDownload = async (row) => {
    setDownloadError('')
    try {
      await downloadSuitabilityDoc({
        client_name: row.client_name,
        adviser_name: row.adviser_name,
        firm_name: row.firm_name,
        basis: row.basis,
        charges: row.charges,
        report_ref: row.report_ref,
        report_part1: row.report_part1,
        report_part2: row.report_part2,
        report_part3: row.report_part3,
        report_part4: row.report_part4,
      })
    } catch (err) {
      setDownloadError(apiErrorMessage(err, 'Could not download that document.'))
    }
  }

  return (
    <>
      <Topbar breadcrumb={[{ label: 'home', href: '/' }, { label: 'reports' }]} ghost={{ label: 'Export CSV' }} primary={{ label: '+ New document', onClick: () => navigate('/clients') }} />
      <PageContainer>
        <div>
          <h1 style={{ fontFamily: font.display, fontSize: 26, fontWeight: 600, color: color.textPrimary, margin: 0, letterSpacing: '-0.01em' }}>Reports</h1>
          <p style={{ margin: '6px 0 0', fontSize: 13.5, color: color.textMuted }}>
            All generated documents across your book. {inReviewCount > 0 && <span style={{ color: color.amber, fontWeight: 600 }}>{inReviewCount} in review</span>}{inReviewCount > 0 ? ' need sign-off.' : ''}
          </p>
        </div>

        {(error || downloadError) && (
          <div style={{ background: 'rgba(199,57,57,0.08)', border: '1px solid rgba(199,57,57,0.3)', borderRadius: 12, padding: 16, fontSize: 13, color: '#e08787' }}>{error || downloadError}</div>
        )}

        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(4,1fr)', gap: 14 }}>
          <Tile value={loading ? '—' : rows.length} label="Total reports" />
          <Tile value={loading ? '—' : finalisedCount} label="Finalised" />
          <Tile value={loading ? '—' : stats?.this_month ?? '—'} label="This month" />
          <Tile value={loading ? '—' : inReviewCount} label="In review" amber />
        </div>

        <div style={{ display: 'flex', alignItems: 'center', gap: 12, flexWrap: 'wrap' }}>
          <SearchInput value={search} onChange={setSearch} placeholder="Search reports or clients…" />
          <div style={{ display: 'flex', gap: 8 }}>
            {FILTERS.map((f) => <Chip key={f} label={f} active={filter === f} onClick={() => setFilter(f)} />)}
          </div>
        </div>

        <div style={{ background: color.card, border: `1px solid ${color.border}`, borderRadius: 13, overflow: 'hidden' }}>
          <div style={{ display: 'grid', gridTemplateColumns: '2.3fr 1.3fr 1fr 1fr 0.9fr 40px', gap: 12, padding: '12px 20px', background: color.rail, fontFamily: font.mono, fontSize: 10, letterSpacing: '0.12em', textTransform: 'uppercase', color: color.textFainter }}>
            <div>Document</div><div>Client</div><div>Type</div><div>Date</div><div>Status</div><div />
          </div>

          {loading ? (
            <div style={{ padding: '18px 20px', fontSize: 13, color: color.textFaint }}>Loading reports…</div>
          ) : filtered.length === 0 ? (
            <div style={{ padding: 34, textAlign: 'center', fontSize: 13, color: color.textFaint }}>No reports match this filter.</div>
          ) : filtered.map((r, i) => (
            <div key={r.id} className="pfx-row" style={{ display: 'grid', gridTemplateColumns: '2.3fr 1.3fr 1fr 1fr 0.9fr 40px', gap: 12, padding: '14px 20px', borderTop: i === 0 ? 'none' : `1px solid ${color.borderSubtle}`, alignItems: 'center', fontSize: 13, color: color.textSecondary }}>
              <div style={{ display: 'flex', alignItems: 'center', gap: 11, minWidth: 0 }}>
                <span style={{ width: 26, height: 26, borderRadius: 7, flex: '0 0 auto', display: 'flex', alignItems: 'center', justifyContent: 'center', fontFamily: font.mono, fontSize: 10, fontWeight: 700, color: color.amber, background: color.amberSoftBg, border: `1px solid ${color.amberSoftBorder}` }}>SR</span>
                <span style={{ fontWeight: 500, color: color.textPrimary, overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>{r.case_title}</span>
              </div>
              <div style={{ color: color.textSecondary2, overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>{r.client_name}</div>
              <div style={{ color: color.textMuted }}>Suitability</div>
              <div style={{ color: color.textMuted, fontFamily: font.mono, fontSize: 12 }}>{formatDate(r.created_at)}</div>
              <div><span style={{ fontSize: 11, color: r.statusBadge.tone === 'teal' ? color.teal : color.amber, background: r.statusBadge.tone === 'teal' ? color.tealSoftBg : color.amberSoftBg, padding: '2px 9px', borderRadius: 6 }}>{r.statusBadge.label}</span></div>
              <div className="pfx-dl" onClick={() => handleDownload(r)} style={{ color: color.teal, textAlign: 'center' }}>↓</div>
            </div>
          ))}
        </div>
      </PageContainer>
      <ChatWidget />
    </>
  )
}

function Tile({ value, label, amber = false }) {
  return (
    <div style={{ background: amber ? 'linear-gradient(160deg,#241d14,#16181b 75%)' : color.card, border: `1px solid ${amber ? '#4a3a1f' : color.border}`, borderRadius: 12, padding: 16 }}>
      <div style={{ fontFamily: font.display, fontSize: 24, fontWeight: 600, color: amber ? color.amber : color.textPrimary }}>{value}</div>
      <div style={{ fontSize: 12, color: amber ? '#c9b79a' : color.textFaint, marginTop: 2 }}>{label}</div>
    </div>
  )
}
