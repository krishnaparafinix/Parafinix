const VARIANTS = {
  primary: 'bg-emerald text-white hover:bg-emerald-600 disabled:bg-emerald/50',
  secondary: 'bg-white text-navy border border-border hover:border-navy/30 disabled:opacity-50',
  outline: 'bg-transparent text-brand-blue border border-brand-blue/40 hover:bg-blue-50 disabled:opacity-50',
  danger: 'bg-white text-red border border-red/30 hover:bg-red/5 disabled:opacity-50',
  ghost: 'bg-transparent text-text-secondary hover:text-navy disabled:opacity-50',
}

const SIZES = {
  sm: 'px-3 py-1.5 text-sm',
  md: 'px-4 py-2.5 text-sm',
  lg: 'px-6 py-3 text-base',
}

export default function Button({
  variant = 'primary',
  size = 'md',
  className = '',
  disabled = false,
  loading = false,
  children,
  ...props
}) {
  return (
    <button
      disabled={disabled || loading}
      className={[
        'inline-flex items-center justify-center gap-2 rounded-lg font-semibold',
        'transition-all duration-200 ease-out active:translate-y-0',
        'disabled:cursor-not-allowed disabled:hover:translate-y-0',
        !disabled && 'hover:-translate-y-px',
        VARIANTS[variant],
        SIZES[size],
        className,
      ].filter(Boolean).join(' ')}
      {...props}
    >
      {loading && (
        <span className="h-3.5 w-3.5 animate-spin rounded-full border-2 border-current border-t-transparent" />
      )}
      {children}
    </button>
  )
}
