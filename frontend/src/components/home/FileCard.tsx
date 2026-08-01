interface FileCardProps {
  name: string
  status: string
  taskId?: string | null
}

export default function FileCard({ name, status, taskId }: FileCardProps) {
  const label =
    status === 'completed' ? 'Completed' : status === 'processing' ? 'Processing' : status

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
      <span className={`file-card-status status-${status}`}>
        {status === 'processing' ? <span className="status-spinner" /> : null}
        {label}
      </span>
    </div>
  )
}
