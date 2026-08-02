export default function UsageIndicator() {
  const used = 8
  const total = 25
  const remaining = total - used

  return (
    <div className="usage-indicator">
      <div className="usage-copy">
        <span className="usage-label">Usage</span>
        <strong className="usage-text">
          {used}/{total} analyses
        </strong>
      </div>
      <div className="usage-bar">
        <div className="usage-bar-fill" style={{ width: `${(used / total) * 100}%` }} />
      </div>
      <span className="usage-remaining">{remaining} left</span>
      <button className="usage-upgrade" type="button">
        Upgrade Pro
      </button>
    </div>
  )
}
