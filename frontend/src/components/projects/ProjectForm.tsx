import { useLayoutEffect, useRef, useState } from 'react'
import FileDropzone from '../common/FileDropzone'

const MAX_NAME = 50
const MAX_DESC = 250

interface ProjectFormProps {
  mode?: 'create' | 'edit'
  initialName?: string
  initialDescription?: string
  onSubmit: (data: { name: string; description: string; files: File[] }) => void
  onCancel: () => void
}

export default function ProjectForm({
  mode = 'create',
  initialName = '',
  initialDescription = '',
  onSubmit,
  onCancel,
}: ProjectFormProps) {
  const [name, setName] = useState(initialName)
  const [description, setDescription] = useState(initialDescription)
  const [files, setFiles] = useState<File[]>([])
  const [error, setError] = useState<string | null>(null)
  const descRef = useRef<HTMLTextAreaElement>(null)

  useLayoutEffect(() => {
    const el = descRef.current
    if (!el) return
    el.style.height = 'auto'
    el.style.height = `${el.scrollHeight}px`
  }, [description])

  function handleSubmit(e: React.FormEvent) {
    e.preventDefault()
    const trimmed = name.trim()
    if (!trimmed) {
      setError('Project name is required.')
      return
    }
    onSubmit({ name: trimmed, description: description.trim(), files })
  }

  return (
    <div className="project-form-panel">
      <h2>{mode === 'edit' ? 'Edit Project' : 'New Project'}</h2>
      <form className="project-form" onSubmit={handleSubmit}>
        <label className="login-field">
          <span>
            Name{' '}
            <span className="char-count">
              {name.length}/{MAX_NAME}
            </span>
          </span>
          <input
            type="text"
            maxLength={MAX_NAME}
            value={name}
            onChange={(e) => setName(e.target.value)}
            required
          />
        </label>
        <label className="login-field">
          <span>
            Description{' '}
            <span className="char-count">
              {description.length}/{MAX_DESC}
            </span>
          </span>
          <textarea
            ref={descRef}
            className="project-desc-input"
            rows={3}
            maxLength={MAX_DESC}
            value={description}
            onChange={(e) => setDescription(e.target.value)}
            placeholder={`Optional (max ${MAX_DESC} characters)`}
          />
        </label>
        {mode === 'create' && (
          <div className="project-form-files">
            <span className="project-form-label">Files (optional)</span>
            <FileDropzone files={files} onChange={setFiles} />
          </div>
        )}
        {error && <p className="form-error">{error}</p>}
        <div className="modal-actions">
          <button type="button" onClick={onCancel}>
            Cancel
          </button>
          <button type="submit">{mode === 'edit' ? 'Save' : 'Create'}</button>
        </div>
      </form>
    </div>
  )
}
