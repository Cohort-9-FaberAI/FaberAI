import { SEVERITY_COLORS } from '../../lib/analysisView'

interface LegendItem {
  label: string
  color: string
}

interface SeverityLegendProps {
  items?: LegendItem[]
}

const defaultItems: LegendItem[] = [
  { label: 'Minor', color: SEVERITY_COLORS.minor },
  { label: 'Problematic', color: SEVERITY_COLORS.problematic },
  { label: 'Severe', color: SEVERITY_COLORS.severe },
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
