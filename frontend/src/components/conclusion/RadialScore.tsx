interface RadialScoreProps {
  percentage: number
  label: string
  recommended?: boolean
}

export default function RadialScore({ percentage, label, recommended }: RadialScoreProps) {
  const radius = 40
  const circumference = 2 * Math.PI * radius
  const offset = circumference - (percentage / 100) * circumference
  const roundedPercentage = Math.round(percentage)

  return (
    <div className="radial-score">
      <svg
        className="radial-score-ring"
        width="100"
        height="100"
        viewBox="0 0 100 100"
        aria-hidden="true"
      >
        <circle cx="50" cy="50" r={radius} fill="none" stroke="#e0e0e0" strokeWidth="8" />
        <circle
          cx="50"
          cy="50"
          r={radius}
          fill="none"
          stroke="var(--accent)"
          strokeWidth="8"
          strokeLinecap="round"
          strokeDasharray={circumference}
          strokeDashoffset={offset}
          transform="rotate(-90 50 50)"
        />
        <text
          x="50"
          y="50"
          textAnchor="middle"
          dominantBaseline="central"
          className="radial-score-text"
        >
          {roundedPercentage}%
        </text>
      </svg>
      <span className="radial-score-copy">
        <span className="radial-label">{label}</span>
        <span className="radial-score-meta">
          {recommended ? 'Recommended process' : `${roundedPercentage}/100`}
        </span>
      </span>
      {recommended && <span className="radial-recommended">Best fit</span>}
    </div>
  )
}
