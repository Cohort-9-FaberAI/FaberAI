interface FileCardProps {
  name: string
  status: string
}

export default function FileCard({ name, status }: FileCardProps) {
  return (
    <div className="file-card">
      <span className="file-card-name">{name}</span>
      <span className={`file-card-status status-${status}`}>{status}</span>
    </div>
  )
}
