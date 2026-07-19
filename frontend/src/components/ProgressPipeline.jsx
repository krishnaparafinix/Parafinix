export default function ProgressPipeline({ stages, currentIndex }) {
  const n = stages.length
  return (
    <div className="w-full py-2">
      <div className="relative flex items-center justify-between">
        <div className="absolute left-0 right-0 top-1/2 h-0.5 -translate-y-1/2 bg-border" />
        <div
          className="absolute left-0 top-1/2 h-0.5 -translate-y-1/2 bg-emerald transition-all duration-700 ease-out"
          style={{ width: n > 1 ? `${(Math.max(currentIndex, 0) / (n - 1)) * 100}%` : '0%' }}
        />
        {stages.map((stage, i) => {
          const done = i < currentIndex
          const active = i === currentIndex
          return (
            <div key={stage} className="relative z-10 flex flex-col items-center gap-2" style={{ flex: i === 0 || i === n - 1 ? '0 0 auto' : '1 1 auto' }}>
              <div
                className={[
                  'flex h-4 w-4 items-center justify-center rounded-full border-2 transition-colors duration-300',
                  done && 'border-emerald bg-emerald',
                  active && 'border-emerald bg-emerald animate-pulse-node',
                  !done && !active && 'border-border bg-surface',
                ].filter(Boolean).join(' ')}
              />
            </div>
          )
        })}
      </div>
      <div className="mt-4 text-center">
        <p className="text-sm font-semibold text-navy">
          {currentIndex >= 0 && currentIndex < n ? stages[currentIndex] : stages[n - 1]}
        </p>
      </div>
    </div>
  )
}
