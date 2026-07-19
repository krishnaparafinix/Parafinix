import { useEffect, useState } from 'react'
import { listClients, createClient, getDashboardStats } from '../api/clients'
import { apiErrorMessage } from '../api/client'
import { useAuth } from '../context/AuthContext'
import StatCard from '../components/StatCard'
import ClientCard from '../components/ClientCard'
import Button from '../components/Button'
import Card from '../components/Card'

export default function Dashboard() {
  const { user } = useAuth()
  const [clients, setClients] = useState([])
  const [stats, setStats] = useState(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')
  const [showAdd, setShowAdd] = useState(false)

  const load = () => {
    setLoading(true)
    setError('')
    Promise.all([listClients(), getDashboardStats()])
      .then(([clientList, statsData]) => {
        setClients(clientList)
        setStats(statsData)
      })
      .catch((err) => setError(apiErrorMessage(err, 'Could not load your dashboard.')))
      .finally(() => setLoading(false))
  }

  useEffect(load, [])

  return (
    <div className="space-y-8">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-navy">
            Welcome back{user?.full_name ? `, ${user.full_name}` : ''}
          </h1>
          <p className="mt-1 text-text-secondary">Here's what's happening across your clients.</p>
        </div>
        <Button onClick={() => setShowAdd(true)}>+ Add new client</Button>
      </div>

      {error && (
        <Card className="border-red/30 bg-red/5 text-sm text-red">{error}</Card>
      )}

      <div className="grid grid-cols-2 gap-4 lg:grid-cols-4">
        <StatCard label="Clients" value={loading || !stats ? '—' : stats.clients} />
        <StatCard label="Reports total" value={loading || !stats ? '—' : stats.reports} />
        <StatCard label="This month" value={loading || !stats ? '—' : stats.this_month} />
        <StatCard label="Pending review" value={loading || !stats ? '—' : stats.pending_review} />
      </div>

      <div>
        <h2 className="mb-4 text-lg font-semibold text-navy">Clients</h2>
        {loading ? (
          <p className="text-sm text-text-secondary">Loading clients…</p>
        ) : clients.length === 0 ? (
          <Card className="text-center text-text-secondary">
            No clients yet. Add your first client to get started.
          </Card>
        ) : (
          <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-3">
            {clients.map((client) => (
              <ClientCard key={client.id} client={client} />
            ))}
          </div>
        )}
      </div>

      {showAdd && (
        <AddClientModal
          onClose={() => setShowAdd(false)}
          onCreated={() => { setShowAdd(false); load() }}
        />
      )}
    </div>
  )
}

function AddClientModal({ onClose, onCreated }) {
  const [form, setForm] = useState({ client_name: '', email: '', phone: '', segment: '', portfolio_value: '' })
  const [error, setError] = useState('')
  const [saving, setSaving] = useState(false)

  const update = (key) => (e) => setForm((f) => ({ ...f, [key]: e.target.value }))

  const handleSubmit = async (e) => {
    e.preventDefault()
    setError('')
    setSaving(true)
    try {
      await createClient({
        client_name: form.client_name,
        email: form.email || null,
        phone: form.phone || null,
        segment: form.segment || null,
        portfolio_value: form.portfolio_value ? Number(form.portfolio_value) : null,
      })
      onCreated()
    } catch (err) {
      setError(apiErrorMessage(err, 'Could not create client.'))
    } finally {
      setSaving(false)
    }
  }

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-navy/40 p-4" onClick={onClose}>
      <div className="w-full max-w-md animate-fade-in-up rounded-xl bg-surface p-6 shadow-lg" onClick={(e) => e.stopPropagation()}>
        <h3 className="text-lg font-semibold text-navy">Add new client</h3>
        <form onSubmit={handleSubmit} className="mt-4 space-y-4">
          <div>
            <label className="mb-1.5 block text-sm font-medium text-navy">Client name *</label>
            <input required value={form.client_name} onChange={update('client_name')}
              className="w-full rounded-lg border border-border px-3 py-2.5 text-sm outline-none focus:border-brand-blue focus:ring-2 focus:ring-brand-blue/20" />
          </div>
          <div className="grid grid-cols-2 gap-3">
            <div>
              <label className="mb-1.5 block text-sm font-medium text-navy">Email</label>
              <input type="email" value={form.email} onChange={update('email')}
                className="w-full rounded-lg border border-border px-3 py-2.5 text-sm outline-none focus:border-brand-blue focus:ring-2 focus:ring-brand-blue/20" />
            </div>
            <div>
              <label className="mb-1.5 block text-sm font-medium text-navy">Phone</label>
              <input value={form.phone} onChange={update('phone')}
                className="w-full rounded-lg border border-border px-3 py-2.5 text-sm outline-none focus:border-brand-blue focus:ring-2 focus:ring-brand-blue/20" />
            </div>
          </div>
          <div className="grid grid-cols-2 gap-3">
            <div>
              <label className="mb-1.5 block text-sm font-medium text-navy">Segment</label>
              <input value={form.segment} onChange={update('segment')}
                className="w-full rounded-lg border border-border px-3 py-2.5 text-sm outline-none focus:border-brand-blue focus:ring-2 focus:ring-brand-blue/20" />
            </div>
            <div>
              <label className="mb-1.5 block text-sm font-medium text-navy">Portfolio value</label>
              <input type="number" value={form.portfolio_value} onChange={update('portfolio_value')}
                className="w-full rounded-lg border border-border px-3 py-2.5 text-sm outline-none focus:border-brand-blue focus:ring-2 focus:ring-brand-blue/20" />
            </div>
          </div>

          {error && <p className="text-sm text-red">{error}</p>}

          <div className="flex justify-end gap-3 pt-2">
            <Button type="button" variant="secondary" onClick={onClose}>Cancel</Button>
            <Button type="submit" loading={saving}>Create client</Button>
          </div>
        </form>
      </div>
    </div>
  )
}
