export default function Card({ children, className = '', accent, hover = false, as: Tag = 'div', style, ...props }) {
  return (
    <Tag
      className={[
        'rounded-xl border border-border bg-surface p-6 shadow-sm',
        'transition-all duration-200 ease-out animate-fade-in-up',
        accent && 'border-l-4',
        hover && 'hover:-translate-y-0.5 hover:shadow-md hover:border-brand-blue/40 cursor-pointer',
        className,
      ].filter(Boolean).join(' ')}
      style={{ ...(accent ? { borderLeftColor: accent } : {}), ...style }}
      {...props}
    >
      {children}
    </Tag>
  )
}
