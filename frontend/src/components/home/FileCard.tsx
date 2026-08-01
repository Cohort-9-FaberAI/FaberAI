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
  onRemove?: () => void
}

export default function FileCard({ name, status, taskId, onRemove }: FileCardProps) {
  return (
    <div className="file-card">
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
  )
}
