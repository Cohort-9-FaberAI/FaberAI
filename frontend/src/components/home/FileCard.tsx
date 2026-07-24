interface FileCardProps {
  name: string
  status: string
  taskId?: string | null
}

export default function FileCard({ name, status, taskId }: FileCardProps) {
  return (
    <div className="file-card">
      <div className="file-card-info">
        <span className="file-card-name">{name}</span>
        {taskId && <span className="file-card-task-id">Task: {taskId}</span>}
      </div>
      <span className={`file-card-status status-${status}`}>{status}</span>
    </div>
  )
}
