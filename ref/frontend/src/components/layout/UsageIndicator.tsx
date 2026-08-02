export default function UsageIndicator() {
  const used = 8
  const total = 25

  return (
    <div className="usage-indicator">
      <div className="usage-text">
        {used}/{total} analyses used
      </div>
      <div className="usage-bar">
        <div className="usage-bar-fill" style={{ width: `${(used / total) * 100}%` }} />
      </div>
      <button className="usage-upgrade" type="button">
        Upgrade to Pro
      </button>
    </div>
  )
}
