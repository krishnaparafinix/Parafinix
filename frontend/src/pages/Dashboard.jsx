import { useEffect, useMemo, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { listClients, getDashboardStats } from '../api/clients'
import { listAllCases } from '../api/cases'
import { apiErrorMessage } from '../api/client'
import { useAuth } from '../context/AuthContext'
import { color, font } from '../lib/theme'
import { timeAgo, weeklyDocumentCounts } from '../lib/format'
import Topbar from '../components/layout/Topbar'
import PageContainer from '../components/layout/PageContainer'
import StatCard from '../components/ui/StatCard'
import Avatar from '../components/ui/Avatar'
import ChatWidget from '../components/ChatWidget'
import AddClientModal from '../components/AddClientModal'

function greeting() {
  const h = new Date().getHours()
  if (h < 12) return 'Good morning'
  if (h < 18) return 'Good afternoon'
  return 'Good evening'
}

const QUICK_ACTIONS = [
  { code: 'SR', label: 'Suitability Report', tone: 'amber' },
  { code: 'CR', label: 'Compliance Report', tone: 'teal' },
  { code: 'FF', label: 'Fact-Find', tone: 'teal' },
  { code: '+', label: 'Add client', tone: 'grey' },
]

export default function Dashboard() {
  const { user } = useAuth()
  const navigate = useNavigate()
  const [clients, setClients] = useState([])
  const [cases, setCases] = useState([])
  const [stats, setStats] = useState(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')
  const [showAdd, setShowAdd] = useState(false)

  const load = () => {
    setLoading(true)
    setError('')
    Promise.all([listClients(), getDashboardStats(), listAllCases()])
      .then(([clientList, statsData, caseData]) => {
        setClients(clientList)
        setStats(statsData)
        setCases(caseData.cases || [])
      })
      .catch((err) => setError(apiErrorMessage(err, 'Could not load your dashboard.')))
      .finally(() => setLoading(false))
  }

  useEffect(load, [])

  const needsAttention = useMemo(() => {
    return clients
      .filter((c) => c.latest_status === 'draft' || c.latest_status === 'in_review' || ['AMBER', 'RED'].includes((c.latest_rag || '').toUpperCase()))
      .slice(0, 4)
      .map((c) => {
        const isReview = c.latest_status === 'in_review' || c.latest_status === 'draft'
        return {
          client: c,
          note: isReview ? 'Latest report awaiting sign-off' : 'Compliance review flagged an item',
          badge: isReview ? 'In review' : 'Flagged',
        }
      })
  }, [clients])

  const recentActivity = useMemo(() => {
    return cases.slice(0, 5).map((c) => ({
      id: c.id,
      dot: ['AMBER', 'RED'].includes((c.rag_rating || '').toUpperCase()) ? color.amber : color.teal,
      client: c.client_name,
      text: c.status === 'signed_off' ? 'Report finalised for' : 'Suitability + Compliance Report generated for',
      when: timeAgo(c.created_at),
    }))
  }, [cases])

  const weekly = useMemo(() => weeklyDocumentCounts(cases, 4), [cases])
  const maxWeekly = Math.max(1, ...weekly)
  const wowChange = weekly[2] > 0 ? Math.round(((weekly[3] - weekly[2]) / weekly[2]) * 100) : null

  const handleQuickAction = (code) => {
    if (code === '+') { setShowAdd(true); return }
    if (clients[0]) navigate(`/clients/${clients[0].id}`)
    else setShowAdd(true)
  }

  return (
    <>
      <Topbar
        breadcrumb={[{ label: 'home' }, { label: 'dashboard' }]}
        ghost={{ label: 'Upload notes', onClick: () => setShowAdd(true) }}
        primary={{ label: '+ New document', onClick: () => setShowAdd(true) }}
      />
      <PageContainer gap={26}>
        <div>
          <h1 style={{ fontFamily: font.display, fontSize: 26, fontWeight: 600, color: color.textPrimary, margin: 0, letterSpacing: '-0.01em' }}>
            {greeting()}{user?.full_name ? `, ${user.full_name.split(' ')[0]}` : ''}
          </h1>
          <p style={{ margin: '6px 0 0', fontSize: 13.5, color: color.textMuted }}>
            {stats ? (
              <>You have <span style={{ color: color.amber, fontWeight: 600 }}>{stats.pending_review} report{stats.pending_review === 1 ? '' : 's'} in review</span>. Your wingman is ready.</>
            ) : 'Your wingman is ready.'}
          </p>
        </div>

        {error && (
          <div style={{ background: 'rgba(199,57,57,0.08)', border: '1px solid rgba(199,57,57,0.3)', borderRadius: 12, padding: 16, fontSize: 13, color: '#e08787' }}>
            {error}
          </div>
        )}

        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(4,1fr)', gap: 16 }}>
          <StatCard code="CL" value={loading ? '—' : stats?.clients ?? 0} label="Active clients" />
          <StatCard code="RV" value={loading ? '—' : stats?.pending_review ?? 0} label="Reports in review" amber />
          <StatCard code="GN" value={loading ? '—' : stats?.this_month ?? 0} label="Generated this month" />
          <StatCard code="RP" value={loading ? '—' : stats?.reports ?? 0} label="Reports total" />
        </div>

        <div style={{ display: 'grid', gridTemplateColumns: '1.55fr 1fr', gap: 20, alignItems: 'start' }}>
          <div style={{ display: 'flex', flexDirection: 'column', gap: 20 }}>
            <div>
              <div style={{ display: 'flex', alignItems: 'baseline', justifyContent: 'space-between', marginBottom: 12 }}>
                <h3 style={{ fontFamily: font.display, fontSize: 16, fontWeight: 600, color: color.textPrimary, margin: 0, letterSpacing: '-0.01em' }}>Needs your attention</h3>
                <a href="/clients" style={{ fontSize: 12, fontFamily: font.mono }}>view all →</a>
              </div>
              <div style={{ background: color.card, border: `1px solid ${color.border}`, borderRadius: 13, overflow: 'hidden' }}>
                {needsAttention.length === 0 ? (
                  <div style={{ padding: '20px 18px', fontSize: 13, color: color.textFaint }}>
                    {loading ? 'Loading…' : "Nothing needs attention right now."}
                  </div>
                ) : needsAttention.map((row, i) => (
                  <div
                    key={row.client.id}
                    className="pfx-row"
                    onClick={() => navigate(`/clients/${row.client.id}`)}
                    style={{ display: 'flex', alignItems: 'center', gap: 14, padding: '15px 18px', borderTop: i === 0 ? 'none' : `1px solid ${color.borderSubtle}`, color: color.textSecondary, cursor: 'pointer' }}
                  >
                    <Avatar name={row.client.client_name} tone={row.badge === 'In review' ? 'teal' : 'flat'} size={34} />
                    <div style={{ flex: 1, minWidth: 0 }}>
                      <div style={{ fontSize: 13.5, fontWeight: 500 }}>{row.client.client_name}</div>
                      <div style={{ fontSize: 11.5, color: color.textFaint }}>{row.note}</div>
                    </div>
                    <span style={{ fontSize: 11, color: color.amber, background: color.amberSoftBg, padding: '3px 9px', borderRadius: 6 }}>{row.badge}</span>
                    <span className="pfx-arrow" style={{ color: color.teal }}>→</span>
                  </div>
                ))}
              </div>
            </div>

            <div>
              <h3 style={{ fontFamily: font.display, fontSize: 16, fontWeight: 600, color: color.textPrimary, margin: '0 0 12px', letterSpacing: '-0.01em' }}>Recent activity</h3>
              <div style={{ background: color.card, border: `1px solid ${color.border}`, borderRadius: 13, padding: '6px 0' }}>
                {recentActivity.length === 0 ? (
                  <div style={{ padding: '14px 18px', fontSize: 13, color: color.textFaint }}>{loading ? 'Loading…' : 'No activity yet.'}</div>
                ) : recentActivity.map((row) => (
                  <div key={row.id} className="pfx-row" style={{ display: 'flex', alignItems: 'center', gap: 12, padding: '12px 18px', fontSize: 13, color: color.textSecondary2 }}>
                    <span style={{ width: 7, height: 7, borderRadius: '50%', background: row.dot, flex: '0 0 auto' }} />
                    {row.text} <span style={{ color: color.textPrimary, marginLeft: 4 }}>{row.client}</span>
                    <span style={{ marginLeft: 'auto', fontFamily: font.mono, fontSize: 11, color: color.textFainter }}>{row.when}</span>
                  </div>
                ))}
              </div>
            </div>
          </div>

          <div style={{ display: 'flex', flexDirection: 'column', gap: 20 }}>
            <div>
              <h3 style={{ fontFamily: font.display, fontSize: 16, fontWeight: 600, color: color.textPrimary, margin: '0 0 12px', letterSpacing: '-0.01em' }}>Quick actions</h3>
              <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 12 }}>
                {QUICK_ACTIONS.map((qa) => (
                  <div
                    key={qa.code}
                    className="pfx-quick"
                    onClick={() => handleQuickAction(qa.code)}
                    style={{ background: color.card, border: `1px solid ${color.border}`, borderRadius: 12, padding: 16, display: 'flex', flexDirection: 'column', gap: 10 }}
                  >
                    <div
                      className="pfx-quick-ico"
                      style={{
                        width: 32, height: 32, borderRadius: 9,
                        background: qa.tone === 'amber' ? color.amberSoftBg : qa.tone === 'teal' ? color.tealSoftBg : color.raised,
                        border: `1px solid ${qa.tone === 'amber' ? color.amberSoftBorder : qa.tone === 'teal' ? color.tealSoftBorder : color.borderRaised}`,
                        display: 'flex', alignItems: 'center', justifyContent: 'center',
                        fontFamily: font.mono, fontSize: 11, fontWeight: 700,
                        color: qa.tone === 'amber' ? color.amber : qa.tone === 'teal' ? color.teal : color.textMuted,
                      }}
                    >
                      {qa.code}
                    </div>
                    <div style={{ fontSize: 13, fontWeight: 600, color: color.textPrimary }}>{qa.label}</div>
                  </div>
                ))}
              </div>
            </div>

            <div style={{ background: color.card, border: `1px solid ${color.border}`, borderRadius: 13, padding: 20 }}>
              <div style={{ display: 'flex', alignItems: 'baseline', justifyContent: 'space-between' }}>
                <h3 style={{ fontFamily: font.display, fontSize: 15, fontWeight: 600, color: color.textPrimary, margin: 0, letterSpacing: '-0.01em' }}>Documents / week</h3>
                {wowChange !== null && (
                  <span style={{ fontFamily: font.mono, fontSize: 11, color: color.teal }}>{wowChange >= 0 ? '▲' : '▼'} {Math.abs(wowChange)}%</span>
                )}
              </div>
              <div style={{ display: 'flex', alignItems: 'flex-end', gap: 9, height: 110, marginTop: 20 }}>
                {weekly.map((count, i) => {
                  const isLast = i === weekly.length - 1
                  const pct = Math.max(4, Math.round((count / maxWeekly) * 100))
                  return (
                    <div key={i} style={{ flex: 1, display: 'flex', flexDirection: 'column', alignItems: 'center', gap: 8 }}>
                      <div
                        className="pfx-bar"
                        style={{
                          width: '100%', height: `${pct}%`,
                          background: isLast ? 'linear-gradient(180deg,#c7893f,#8a5d24)' : color.borderRaised,
                          borderRadius: '4px 4px 0 0',
                        }}
                      />
                      <span style={{ fontFamily: font.mono, fontSize: 9, color: isLast ? color.amber : color.textFainter }}>W{i + 1}</span>
                    </div>
                  )
                })}
              </div>
            </div>
          </div>
        </div>
      </PageContainer>

      {showAdd && <AddClientModal onClose={() => setShowAdd(false)} onCreated={(client) => { setShowAdd(false); navigate(`/clients/${client.id}`) }} />}

      <ChatWidget />
    </>
  )
}
