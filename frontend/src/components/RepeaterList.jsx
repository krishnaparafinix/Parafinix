import Button from './Button'

function emptyRow(fields) {
  return Object.fromEntries(fields.map(([key]) => [key, '']))
}

export default function RepeaterList({ title, fields, items, onChange }) {
  const rows = items || []

  const updateRow = (i, key, value) => {
    const next = rows.map((row, idx) => (idx === i ? { ...row, [key]: value } : row))
    onChange(next)
  }

  const addRow = () => onChange([...rows, emptyRow(fields)])
  const removeRow = (i) => onChange(rows.filter((_, idx) => idx !== i))

  return (
    <div className="rounded-xl border border-border bg-surface p-6">
      <div className="mb-4 flex items-center justify-between">
        <h3 className="font-semibold text-navy">{title}</h3>
        <Button variant="outline" size="sm" onClick={addRow}>+ Add</Button>
      </div>
      {rows.length === 0 ? (
        <p className="text-sm text-text-secondary">None recorded.</p>
      ) : (
        <div className="space-y-4">
          {rows.map((row, i) => (
            <div key={i} className="rounded-lg border border-border p-4">
              <div className="grid grid-cols-1 gap-3 sm:grid-cols-2 lg:grid-cols-3">
                {fields.map(([key, label]) => (
                  <div key={key}>
                    <label className="mb-1 block text-xs font-medium text-text-secondary">{label}</label>
                    <input
                      value={row[key] ?? ''}
                      onChange={(e) => updateRow(i, key, e.target.value)}
                      className="w-full rounded-lg border border-border px-2.5 py-1.5 text-sm outline-none focus:border-brand-blue focus:ring-2 focus:ring-brand-blue/20"
                    />
                  </div>
                ))}
              </div>
              <button onClick={() => removeRow(i)} className="mt-3 text-xs font-medium text-red hover:underline">
                Remove
              </button>
            </div>
          ))}
        </div>
      )}
    </div>
  )
}
