import { useNavigate } from 'react-router-dom'
import Card from './Card'
import RAGBadge from './RAGBadge'

function timeAgo(iso) {
  if (!iso) return 'No activity yet'
  const diffMs = Date.now() - new Date(iso).getTime()
  const mins = Math.floor(diffMs / 60000)
  if (mins < 1) return 'Just now'
  if (mins < 60) return `${mins}m ago`
  const hours = Math.floor(mins / 60)
  if (hours < 24) return `${hours}h ago`
  const days = Math.floor(hours / 24)
  if (days < 30) return `${days}d ago`
  return new Date(iso).toLocaleDateString('en-GB', { day: 'numeric', month: 'short', year: 'numeric' })
}

export default function ClientCard({ client }) {
  const navigate = useNavigate()
  return (
    <Card hover onClick={() => navigate(`/clients/${client.id}`)}>
      <div className="flex items-start justify-between gap-3">
        <div>
          <h3 className="font-semibold text-navy">{client.client_name}</h3>
          <p className="mt-1 text-sm text-text-secondary">
            {client.case_count ?? 0} report{(client.case_count ?? 0) === 1 ? '' : 's'}
          </p>
        </div>
        {client.latest_rag && <RAGBadge rag={client.latest_rag} size="sm" />}
      </div>
      <p className="mt-4 text-xs text-text-secondary">{timeAgo(client.updated_at)}</p>
    </Card>
  )
}
