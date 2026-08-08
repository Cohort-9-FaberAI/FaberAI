interface LegendItem {
  label: string
  color: string
}

interface SeverityLegendProps {
  items?: LegendItem[]
}

const defaultItems: LegendItem[] = [
  { label: 'Pro', color: '#4caf50' },
  { label: 'Neutral', color: '#ffb84d' },
  { label: 'Con', color: '#ff4d4d' },
]

export default function SeverityLegend({ items = defaultItems }: SeverityLegendProps) {
  return (
    <div className="severity-legend">
      {items.map((item) => (
        <span key={item.label} className="legend-item">
          <span className="legend-dot" style={{ background: item.color }} />
          {item.label}
        </span>
      ))}
    </div>
  )
}
