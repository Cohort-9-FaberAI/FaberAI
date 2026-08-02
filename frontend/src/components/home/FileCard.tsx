const STATUS_LABELS: Record<string, string> = {
  stored: 'Ready',
  processing: 'Processing',
  completed: 'Completed',
  failed: 'Failed',
  pending: 'Pending',
}

interface FileCardProps {
  name: string
  status: string
  taskId?: string | null
  errorMessage?: string | null
  onRemove?: () => void
}

export default function FileCard({ name, status, taskId, errorMessage, onRemove }: FileCardProps) {
  return (
    <div className="file-card" style={{ flexDirection: 'column', alignItems: 'stretch' }}>
      <div
        style={{
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'space-between',
          width: '100%',
        }}
      >
        <div className="file-card-info">
          <span className="file-thumbnail" aria-hidden="true">
            <svg viewBox="0 0 18 18" fill="none">
              <path d="M3 15V3L9 1L15 3V15L11 13V7.5L9 6.2L7 7.5V13L3 15Z" fill="var(--ferrule)" />
            </svg>
          </span>
          <span>
            <span className="file-card-name">{name}</span>
            {taskId && <span className="file-card-task-id">Task: {taskId}</span>}
          </span>
        </div>
        <div
          className="file-card-right"
          style={{ display: 'flex', alignItems: 'center', gap: '12px' }}
        >
          <span className={`file-card-status status-${status}`}>
            {status === 'processing' ? <span className="status-spinner" /> : null}
            {STATUS_LABELS[status] ?? status}
          </span>
          {onRemove && (
            <button type="button" className="file-card-remove" onClick={onRemove}>
              Remove
            </button>
          )}
        </div>
      </div>
      {(status === 'failed' || errorMessage) && (
        <div
          style={{
            marginTop: '10px',
            padding: '10px 14px',
            borderRadius: '8px',
            background: 'rgba(232, 93, 93, 0.15)',
            border: '1px solid rgba(232, 93, 93, 0.45)',
            color: '#ff6b6b',
            fontSize: '13px',
            fontWeight: 600,
            display: 'flex',
            alignItems: 'center',
            gap: '8px',
            lineHeight: 1.4,
          }}
        >
          <span style={{ fontSize: '16px', flexShrink: 0 }}>⚠️</span>
          <span>
            {errorMessage ||
              'DFM Analysis failed to process. Please verify the CAD file geometry or try re-uploading.'}
          </span>
        </div>
      )}
    </div>
  )
}
