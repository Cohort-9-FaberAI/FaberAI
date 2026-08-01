interface Field {
  label: string
  value: string
}

interface Action {
  label: string
  onClick: () => void
}

interface ListRowProps {
  fields: Field[]
  actions: Action[]
}

export default function ListRow({ fields, actions }: ListRowProps) {
  return (
    <div className="list-row">
      <div className="list-row-fields">
        {fields.map((f) => (
          <div key={f.label} className="list-row-field">
            <span className="list-row-label">{f.label}</span>
            <span className="list-row-value">{f.value}</span>
          </div>
        ))}
      </div>
      <div className="list-row-actions">
        {actions.map((a) => (
          <button key={a.label} type="button" className="list-row-action" onClick={a.onClick}>
            {a.label}
          </button>
        ))}
      </div>
    </div>
  )
}
