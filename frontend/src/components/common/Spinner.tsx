interface SpinnerProps {
  size?: number
  label?: string
}

export default function Spinner({ size = 32, label }: SpinnerProps) {
  return (
    <div
      style={{
        display: 'flex',
        flexDirection: 'column',
        alignItems: 'center',
        gap: 12,
        padding: 24,
      }}
    >
      <div
        style={{
          width: size,
          height: size,
          border: '3px solid rgba(255,255,255,0.15)',
          borderTopColor: 'var(--primary-light)',
          borderRadius: '50%',
          animation: 'spin 0.8s linear infinite',
        }}
      />
      {label && <span style={{ fontSize: 13, color: 'var(--text-muted)' }}>{label}</span>}
    </div>
  )
}
