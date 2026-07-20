import { useState } from 'react'
import { SIMPLE_SECTIONS, LIST_SECTIONS } from '../lib/factFindSchema'
import { color, font } from '../lib/theme'
import Avatar from './ui/Avatar'

// Maps the backend's 10 field categories onto the approved design's 6
// drawer sections, plus 2 extra sections (Estate Planning, Tax) in the same
// visual style so no real backend data is dropped from the UI.
const GROUPS = [
  { title: 'Personal details', simple: ['personal'], lists: [] },
  { title: 'Objectives & risk', simple: ['objectives', 'risk'], lists: [] },
  { title: 'Income & expenditure', simple: ['income', 'expenditure'], lists: [] },
  { title: 'Assets', simple: ['assets'], lists: ['cash_savings', 'isas', 'gia'] },
  { title: 'Pensions', simple: [], lists: ['pensions'] },
  { title: 'Liabilities & protection', simple: ['liabilities'], lists: ['protection'] },
  { title: 'Estate planning', simple: ['estate_planning'], lists: [] },
  { title: 'Tax', simple: ['tax'], lists: [] },
]

const simpleById = Object.fromEntries(SIMPLE_SECTIONS.map((s) => [s.id, s]))
const listByKey = Object.fromEntries(LIST_SECTIONS.map((l) => [l.key, l]))

const fieldWrap = { fontSize: 11, color: color.textFainter }
const valueBase = { fontSize: 13.5, marginTop: 3, color: color.textPrimary }
const inputBase = {
  marginTop: 4, width: '100%', boxSizing: 'border-box', background: color.bg,
  border: `1px solid ${color.borderRaised}`, borderRadius: 7, padding: '7px 10px',
  color: color.textPrimary, fontSize: 13, outline: 'none', fontFamily: font.body,
}

function SimpleField({ label, value, editing, onChange, mono = false }) {
  return (
    <div>
      <div style={fieldWrap}>{label}</div>
      {editing ? (
        <input value={value ?? ''} onChange={(e) => onChange(e.target.value)} style={{ ...inputBase, fontFamily: mono ? font.mono : font.body }} />
      ) : (
        <div style={{ ...valueBase, fontFamily: mono ? font.mono : font.body }}>{value || '—'}</div>
      )}
    </div>
  )
}

function composeSummary(item, fieldDefs) {
  const parts = fieldDefs.map(([key]) => item[key]).filter((v) => v && String(v).trim())
  return parts.join(' · ') || 'No details recorded'
}

function ListSectionView({ list, items }) {
  if (!items || items.length === 0) {
    return <div style={{ gridColumn: 'span 2', fontSize: 13, color: color.textFainter }}>None recorded.</div>
  }
  return items.map((item, i) => (
    <div key={i} style={{ gridColumn: 'span 2' }}>
      <div style={fieldWrap}>{item[list.fields[0][0]] || `${list.title} ${i + 1}`}</div>
      <div style={{ ...valueBase, fontFamily: font.mono }}>{composeSummary(item, list.fields.slice(1))}</div>
    </div>
  ))
}

function ListSectionEdit({ list, items, onChange }) {
  const rows = items || []
  const updateRow = (i, key, value) => onChange(rows.map((row, idx) => (idx === i ? { ...row, [key]: value } : row)))
  const addRow = () => onChange([...rows, Object.fromEntries(list.fields.map(([k]) => [k, '']))])
  const removeRow = (i) => onChange(rows.filter((_, idx) => idx !== i))

  return (
    <div style={{ gridColumn: 'span 2', display: 'flex', flexDirection: 'column', gap: 10 }}>
      {rows.map((row, i) => (
        <div key={i} style={{ border: `1px solid ${color.borderRaised}`, borderRadius: 9, padding: 12, display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '10px 14px' }}>
          {list.fields.map(([key, label]) => (
            <SimpleField key={key} label={label} value={row[key]} editing onChange={(v) => updateRow(i, key, v)} />
          ))}
          <button type="button" onClick={() => removeRow(i)} style={{ gridColumn: 'span 2', justifySelf: 'start', background: 'none', border: 'none', color: '#e08787', fontSize: 11.5, cursor: 'pointer', padding: 0 }}>
            Remove
          </button>
        </div>
      ))}
      <button type="button" onClick={addRow} style={{ alignSelf: 'flex-start', background: 'none', border: `1px solid ${color.borderRaised}`, color: color.teal, fontSize: 12, borderRadius: 7, padding: '6px 12px', cursor: 'pointer' }}>
        + Add {list.title.replace(/s$/, '')}
      </button>
    </div>
  )
}

const DEPENDANT_FIELDS = [['name', 'Name'], ['age', 'Age'], ['relationship', 'Relationship']]

// The mockup shows "Dependants" as a single summary field (e.g. "2 · adult,
// independent"), not one row per dependant like Pensions/Protection — so this
// is handled separately from the generic list-section renderer above.
function DependantsField({ dependants, editing, onChange }) {
  const list = dependants || []
  if (!editing) {
    const summary = list.length === 0 ? 'None' : list.map((d) => `${d.name || 'Unnamed'}${d.age ? ` (${d.age})` : ''}`).join(', ')
    return <SimpleField label="Dependants" value={`${list.length} · ${summary}`} editing={false} />
  }
  const updateRow = (i, key, value) => onChange(list.map((row, idx) => (idx === i ? { ...row, [key]: value } : row)))
  const addRow = () => onChange([...list, { name: '', age: '', relationship: '' }])
  const removeRow = (i) => onChange(list.filter((_, idx) => idx !== i))
  return (
    <div style={{ gridColumn: 'span 2', display: 'flex', flexDirection: 'column', gap: 10 }}>
      <div style={fieldWrap}>Dependants</div>
      {list.map((row, i) => (
        <div key={i} style={{ border: `1px solid ${color.borderRaised}`, borderRadius: 9, padding: 12, display: 'grid', gridTemplateColumns: '1fr 1fr 1fr', gap: '10px 14px' }}>
          {DEPENDANT_FIELDS.map(([key, label]) => (
            <SimpleField key={key} label={label} value={row[key]} editing onChange={(v) => updateRow(i, key, v)} />
          ))}
          <button type="button" onClick={() => removeRow(i)} style={{ gridColumn: 'span 3', justifySelf: 'start', background: 'none', border: 'none', color: '#e08787', fontSize: 11.5, cursor: 'pointer', padding: 0 }}>Remove</button>
        </div>
      ))}
      <button type="button" onClick={addRow} style={{ alignSelf: 'flex-start', background: 'none', border: `1px solid ${color.borderRaised}`, color: color.teal, fontSize: 12, borderRadius: 7, padding: '6px 12px', cursor: 'pointer' }}>+ Add dependant</button>
    </div>
  )
}

export default function FactFindDrawer({ client, factFind, onClose, onSave }) {
  const [editing, setEditing] = useState(false)
  const [draft, setDraft] = useState(null)

  const data = editing ? draft : factFind?.data
  const savedAt = factFind?.savedAt

  const startEdit = () => { setDraft(JSON.parse(JSON.stringify(factFind.data))); setEditing(true) }
  const cancelEdit = () => { setEditing(false); setDraft(null) }
  const saveEdit = () => { onSave(draft); setEditing(false); setDraft(null) }

  const updateSimple = (sectionId, key, value) => {
    setDraft((d) => ({ ...d, [sectionId]: { ...d[sectionId], [key]: value } }))
  }
  const updateList = (list, rows) => {
    setDraft((d) => (list.section ? { ...d, [list.section]: { ...d[list.section], [list.key]: rows } } : { ...d, [list.key]: rows }))
  }

  if (!data) return null

  return (
    <>
      <div onClick={editing ? undefined : onClose} style={{ position: 'fixed', inset: 0, zIndex: 60, background: 'rgba(9,10,12,0.72)', backdropFilter: 'blur(6px)', animation: 'pfx-fade 0.2s ease' }} />
      <div style={{ position: 'fixed', top: 0, right: 0, height: '100vh', width: 620, maxWidth: '100vw', zIndex: 61, background: 'linear-gradient(165deg,#181b1f,#121417)', borderLeft: `1px solid ${color.borderRaised}`, boxShadow: '-40px 0 90px -30px rgba(0,0,0,0.85)', animation: 'pfx-slidein 0.4s cubic-bezier(.2,.8,.2,1)', display: 'flex', flexDirection: 'column' }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: 16, padding: '22px 26px', borderBottom: `1px solid ${color.border}`, flex: '0 0 auto' }}>
          <Avatar name={client.client_name} tone="teal" size={52} radius={13} style={{ fontSize: 19, boxShadow: '0 8px 20px -8px rgba(95,208,196,0.5)' }} />
          <div style={{ flex: 1, minWidth: 0 }}>
            <div style={{ fontFamily: font.display, fontSize: 19, fontWeight: 600, color: color.textPrimary, letterSpacing: '-0.01em' }}>{client.client_name}</div>
            <div style={{ fontFamily: font.mono, fontSize: 11, color: color.textFaint, marginTop: 3 }}>Full fact-find · PFX-{client.id.replace(/-/g, '').slice(0, 5).toUpperCase()}</div>
          </div>
          <div className="pfx-btn pfx-btn-ghost" onClick={onClose} style={{ fontSize: 18, lineHeight: 1, color: color.textSecondary2, border: `1px solid ${color.borderRaised}`, borderRadius: 9, padding: '8px 13px', background: color.raised, cursor: 'pointer' }}>✕</div>
        </div>

        <div style={{ padding: '14px 26px', borderBottom: `1px solid ${color.border}`, display: 'flex', alignItems: 'center', gap: 10, flex: '0 0 auto', background: 'rgba(95,208,196,0.04)' }}>
          <span style={{ width: 7, height: 7, borderRadius: '50%', background: color.teal, animation: 'pfx-pulse 1.8s ease-in-out infinite', flex: '0 0 auto' }} />
          <span style={{ fontSize: 12, color: '#9fb4b0' }}>
            Extracted from meeting notes / uploaded documents · <span style={{ color: color.teal }}>saved &amp; verified</span>
            {savedAt ? ` · updated ${new Date(savedAt).toLocaleDateString('en-GB', { day: '2-digit', month: 'short', year: 'numeric' })}` : ''}
          </span>
        </div>

        <div style={{ flex: 1, overflow: 'auto', padding: '24px 26px', display: 'flex', flexDirection: 'column', gap: 22 }}>
          {GROUPS.map((group) => {
            const hasContent = group.simple.length > 0 || group.lists.length > 0
            if (!hasContent) return null
            return (
              <div key={group.title}>
                <div style={{ fontFamily: font.mono, fontSize: 10, letterSpacing: '0.16em', textTransform: 'uppercase', color: color.amber, marginBottom: 12 }}>{group.title}</div>
                <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '14px 22px' }}>
                  {group.simple.flatMap((sectionId) => {
                    const section = simpleById[sectionId]
                    const values = data[sectionId] || {}
                    return section.fields.map(([key, label]) => (
                      <SimpleField
                        key={`${sectionId}.${key}`}
                        label={label}
                        value={values[key]}
                        editing={editing}
                        onChange={(v) => updateSimple(sectionId, key, v)}
                        mono={/value|amount|salary|income|£|surplus|balance|contribution/i.test(key)}
                      />
                    ))
                  })}
                  {group.title === 'Personal details' && (
                    <DependantsField
                      dependants={data.personal?.dependants}
                      editing={editing}
                      onChange={(rows) => updateSimple('personal', 'dependants', rows)}
                    />
                  )}
                  {group.lists.map((listKey) => {
                    const list = listByKey[listKey]
                    const items = list.section ? (data[list.section] || {})[list.key] : data[list.key]
                    return editing
                      ? <ListSectionEdit key={listKey} list={list} items={items} onChange={(rows) => updateList(list, rows)} />
                      : <ListSectionView key={listKey} list={list} items={items} />
                  })}
                </div>
                <div style={{ height: 1, background: color.borderSubtle, marginTop: 22 }} />
              </div>
            )
          })}

          <div style={{ background: color.rail, border: `1px solid ${color.borderSubtle}`, borderRadius: 10, padding: '14px 16px', fontSize: 11.5, color: color.textFaint, lineHeight: 1.5 }}>
            <span style={{ fontFamily: font.mono, color: color.teal }}>source:</span> Extracted &amp; saved by Parafinix AI. Review all figures before generating advice.
          </div>
        </div>

        <div style={{ padding: '16px 26px', borderTop: `1px solid ${color.border}`, display: 'flex', gap: 10, flex: '0 0 auto' }}>
          {!editing ? (
            <>
              <div className="pfx-btn pfx-btn-ghost" onClick={onClose} style={{ flex: 1, fontSize: 13, fontWeight: 500, color: color.textSecondary2, border: `1px solid ${color.borderRaised}`, borderRadius: 9, padding: '11px 0', textAlign: 'center', background: color.raised, cursor: 'pointer' }}>Close</div>
              <div className="pfx-btn pfx-btn-amber" onClick={startEdit} style={{ flex: 1.3, fontSize: 13, fontWeight: 600, color: color.ink, background: color.amber, borderRadius: 9, padding: '11px 0', textAlign: 'center', cursor: 'pointer' }}>Edit fact-find</div>
            </>
          ) : (
            <>
              <div className="pfx-btn pfx-btn-ghost" onClick={cancelEdit} style={{ flex: 1, fontSize: 13, fontWeight: 500, color: color.textSecondary2, border: `1px solid ${color.borderRaised}`, borderRadius: 9, padding: '11px 0', textAlign: 'center', background: color.raised, cursor: 'pointer' }}>Cancel</div>
              <div className="pfx-btn pfx-btn-teal" onClick={saveEdit} style={{ flex: 1.3, fontSize: 13, fontWeight: 600, color: color.ink, background: color.teal, borderRadius: 9, padding: '11px 0', textAlign: 'center', cursor: 'pointer' }}>Save changes</div>
            </>
          )}
        </div>
      </div>
    </>
  )
}
