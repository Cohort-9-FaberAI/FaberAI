export default function SeverityLegend() {
  return (
    <div className="severity-legend">
      <span className="legend-item">
        <span className="legend-dot" style={{ background: '#4caf50' }} />
        Pro
      </span>
      <span className="legend-item">
        <span className="legend-dot" style={{ background: '#ffb84d' }} />
        Neutral
      </span>
      <span className="legend-item">
        <span className="legend-dot" style={{ background: '#ff4d4d' }} />
        Con
      </span>
    </div>
  )
}
