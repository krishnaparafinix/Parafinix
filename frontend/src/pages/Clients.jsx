import { useEffect, useMemo, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { listClients } from '../api/clients'
import { apiErrorMessage } from '../api/client'
import { color, font } from '../lib/theme'
import Topbar from '../components/layout/Topbar'
import PageContainer from '../components/layout/PageContainer'
import SearchInput from '../components/ui/SearchInput'
import Chip from '../components/ui/Chip'
import Avatar from '../components/ui/Avatar'
import AddClientModal from '../components/AddClientModal'
import ChatWidget from '../components/ChatWidget'

const PAGE_SIZE = 20

function refOf(id) {
  return 'PFX-' + (id || '').replace(/-/g, '').slice(0, 5).toUpperCase()
}

function deriveStatus(client) {
  if (!client.case_count) return 'Prospect'
  if (client.latest_status === 'draft' || client.latest_status === 'in_review') return 'Review due'
  return 'Active'
}

function statusStyle(status) {
  if (status === 'Review due') return { color: color.amber, bg: color.amberSoftBg, tone: 'amber' }
  if (status === 'Prospect') return { color: color.textMuted, bg: 'rgba(146,152,160,0.1)', tone: 'flat' }
  return { color: color.teal, bg: color.tealSoftBg, tone: 'teal' }
}

function formatMoney(v) {
  if (v === null || v === undefined || v === '') return '—'
  return '£' + Number(v).toLocaleString('en-GB', { maximumFractionDigits: 0 })
}

const FILTERS = ['All', 'Active', 'Review due', 'Prospect']

export default function Clients() {
  const navigate = useNavigate()
  const [clients, setClients] = useState([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')
  const [search, setSearch] = useState('')
  const [filter, setFilter] = useState('All')
  const [page, setPage] = useState(1)
  const [showAdd, setShowAdd] = useState(false)

  const load = () => {
    setLoading(true)
    setError('')
    listClients()
      .then(setClients)
      .catch((err) => setError(apiErrorMessage(err, 'Could not load clients.')))
      .finally(() => setLoading(false))
  }

  useEffect(load, [])

  const enriched = useMemo(() => clients.map((c) => ({ ...c, status: deriveStatus(c), ref: refOf(c.id) })), [clients])

  const filtered = useMemo(() => {
    const q = search.trim().toLowerCase()
    return enriched.filter((c) => {
      if (filter !== 'All' && c.status !== filter) return false
      if (!q) return true
      return (c.client_name || '').toLowerCase().includes(q) || c.ref.toLowerCase().includes(q) || (c.segment || '').toLowerCase().includes(q)
    })
  }, [enriched, search, filter])

  const pageCount = Math.max(1, Math.ceil(filtered.length / PAGE_SIZE))
  const pageClients = filtered.slice((page - 1) * PAGE_SIZE, page * PAGE_SIZE)
  const reviewDueCount = enriched.filter((c) => c.status === 'Review due').length

  useEffect(() => { setPage(1) }, [search, filter])

  return (
    <>
      <Topbar
        breadcrumb={[{ label: 'home', href: '/' }, { label: 'clients' }]}
        ghost={{ label: 'Import' }}
        primary={{ label: '+ Add client', onClick: () => setShowAdd(true) }}
      />
      <PageContainer>
        <div>
          <h1 style={{ fontFamily: font.display, fontSize: 26, fontWeight: 600, color: color.textPrimary, margin: 0, letterSpacing: '-0.01em' }}>Clients</h1>
          <p style={{ margin: '6px 0 0', fontSize: 13.5, color: color.textMuted }}>
            <span style={{ color: color.textPrimary, fontWeight: 600 }}>{enriched.length}</span> total ·{' '}
            <span style={{ color: color.amber, fontWeight: 600 }}>{reviewDueCount}</span> review{reviewDueCount === 1 ? '' : 's'} due
          </p>
        </div>

        {error && (
          <div style={{ background: 'rgba(199,57,57,0.08)', border: '1px solid rgba(199,57,57,0.3)', borderRadius: 12, padding: 16, fontSize: 13, color: '#e08787' }}>{error}</div>
        )}

        <div style={{ display: 'flex', alignItems: 'center', gap: 12, flexWrap: 'wrap' }}>
          <SearchInput value={search} onChange={setSearch} placeholder="Search clients, reference, segment…" hint="⌘K" />
          <div style={{ display: 'flex', gap: 8 }}>
            {FILTERS.map((f) => <Chip key={f} label={f} active={filter === f} onClick={() => setFilter(f)} />)}
          </div>
        </div>

        <div style={{ background: color.card, border: `1px solid ${color.border}`, borderRadius: 13, overflow: 'hidden' }}>
          <div style={{ display: 'grid', gridTemplateColumns: '2.2fr 1fr 1.1fr 1fr 1fr 40px', gap: 12, padding: '12px 20px', background: color.rail, fontFamily: font.mono, fontSize: 10, letterSpacing: '0.12em', textTransform: 'uppercase', color: color.textFainter }}>
            <div>Client</div><div>Segment</div><div>Portfolio</div><div>Reports</div><div>Status</div><div />
          </div>

          {loading ? (
            <div style={{ padding: '18px 20px', fontSize: 13, color: color.textFaint }}>Loading clients…</div>
          ) : pageClients.length === 0 ? (
            <div style={{ padding: '34px', textAlign: 'center', fontSize: 13, color: color.textFaint }}>
              {clients.length === 0 ? 'No clients yet — add your first client to get started.' : 'No clients match this filter.'}
            </div>
          ) : pageClients.map((c, i) => {
            const st = statusStyle(c.status)
            return (
              <div
                key={c.id}
                className="pfx-row"
                onClick={() => navigate(`/clients/${c.id}`)}
                style={{ display: 'grid', gridTemplateColumns: '2.2fr 1fr 1.1fr 1fr 1fr 40px', gap: 12, padding: '14px 20px', borderTop: i === 0 ? 'none' : `1px solid ${color.borderSubtle}`, alignItems: 'center', color: color.textSecondary, cursor: 'pointer' }}
              >
                <div style={{ display: 'flex', alignItems: 'center', gap: 12, minWidth: 0 }}>
                  <Avatar className="pfx-avatar" name={c.client_name} tone={st.tone} />
                  <div style={{ minWidth: 0 }}>
                    <div style={{ fontSize: 13.5, fontWeight: 500, color: color.textPrimary }}>{c.client_name}</div>
                    <div style={{ fontFamily: font.mono, fontSize: 11, color: color.textFaint }}>{c.ref}{c.segment ? ` · ${c.segment}` : ''}</div>
                  </div>
                </div>
                <div style={{ fontSize: 13, color: color.textSecondary2 }}>{c.segment || '—'}</div>
                <div style={{ fontSize: 13, color: color.teal, fontFamily: font.mono, fontWeight: 500 }}>{formatMoney(c.portfolio_value)}</div>
                <div style={{ fontSize: 13, color: color.textMuted, fontFamily: font.mono }}>{c.case_count ?? 0}</div>
                <div><span style={{ fontSize: 11, color: st.color, background: st.bg, padding: '3px 9px', borderRadius: 6 }}>{c.status}</span></div>
                <div className="pfx-arrow" style={{ color: color.teal, textAlign: 'center' }}>→</div>
              </div>
            )
          })}
        </div>

        {!loading && filtered.length > 0 && (
          <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', fontSize: 12, color: color.textFaint, fontFamily: font.mono }}>
            <span>Showing {pageClients.length} of {filtered.length}</span>
            {pageCount > 1 && (
              <div style={{ display: 'flex', gap: 6 }}>
                {Array.from({ length: pageCount }, (_, i) => i + 1).map((p) => (
                  <span
                    key={p}
                    onClick={() => setPage(p)}
                    className="pfx-chip"
                    style={{ padding: '6px 11px', border: `1px solid ${color.borderRaised}`, borderRadius: 7, color: p === page ? color.textSecondary : color.textMuted, background: p === page ? color.raised : 'transparent', cursor: 'pointer' }}
                  >
                    {p}
                  </span>
                ))}
              </div>
            )}
          </div>
        )}
      </PageContainer>

      {showAdd && <AddClientModal onClose={() => setShowAdd(false)} onCreated={(client) => { setShowAdd(false); navigate(`/clients/${client.id}`) }} />}
      <ChatWidget />
    </>
  )
}
