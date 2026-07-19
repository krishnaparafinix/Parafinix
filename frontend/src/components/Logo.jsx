export default function Logo({ size = 'md' }) {
  const textSize = size === 'lg' ? 'text-2xl' : 'text-lg'
  return (
    <div className="flex items-center gap-2.5">
      <svg width="28" height="28" viewBox="0 0 28 28" fill="none" aria-hidden="true">
        <path
          d="M2 20 L9 20 L12 10 L16 24 L19 14 L22 20 L26 20"
          stroke="#3B82F6"
          strokeWidth="2"
          strokeLinecap="round"
          strokeLinejoin="round"
          fill="none"
        />
        <circle cx="26" cy="20" r="3" fill="#10B981" className="animate-pulse-node" />
      </svg>
      <span className={`${textSize} font-bold text-navy tracking-tight`}>Parafinix</span>
    </div>
  )
}
