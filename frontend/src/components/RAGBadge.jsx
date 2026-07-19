import { ragStyle } from '../lib/rag'

export default function RAGBadge({ rag, size = 'md' }) {
  const style = ragStyle(rag)
  const dotSize = size === 'sm' ? 'h-2 w-2' : 'h-2.5 w-2.5'
  return (
    <span className="inline-flex items-center gap-1.5 text-sm font-medium text-navy">
      <span className={`rounded-full ${dotSize} ${style.dot}`} />
      {style.label}
    </span>
  )
}
