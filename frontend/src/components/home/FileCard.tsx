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
        <span className="file-card-name">{name}</span>
        {taskId && <span className="file-card-task-id">Task: {taskId}</span>}
      </div>
      <div className="file-card-right">
        {status !== 'stored' && (
          <span className={`file-card-status status-${status}`}>
            {STATUS_LABELS[status] ?? status}
          </span>
        )}
        {onRemove && (
          <button type="button" className="file-card-remove" onClick={onRemove}>
            Remove
          </button>
        )}
      </div>
    </div>
  )
}
