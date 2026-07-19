export default function FieldGroup({ title, fields, values, onChange }) {
  return (
    <div className="rounded-xl border border-border bg-surface p-6">
      <h3 className="mb-4 font-semibold text-navy">{title}</h3>
      <div className="grid grid-cols-1 gap-4 sm:grid-cols-2">
        {fields.map(([key, label]) => (
          <div key={key}>
            <label className="mb-1.5 block text-xs font-medium text-text-secondary">{label}</label>
            <input
              value={values[key] ?? ''}
              onChange={(e) => onChange(key, e.target.value)}
              className="w-full rounded-lg border border-border px-3 py-2 text-sm outline-none transition-colors focus:border-brand-blue focus:ring-2 focus:ring-brand-blue/20"
            />
          </div>
        ))}
      </div>
    </div>
  )
}
