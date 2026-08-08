interface LegendItem {
  label: string
  color: string
}

interface SeverityLegendProps {
  items?: LegendItem[]
}

const defaultItems: LegendItem[] = [
  { label: 'Minor', color: '#ffd54f' },
  { label: 'Problematic', color: '#ffb74d' },
  { label: 'Severe', color: '#ef5350' },
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
