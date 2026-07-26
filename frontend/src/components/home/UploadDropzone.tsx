import { useRef, useState } from 'react'
import { uploadFile } from '../../lib/api'
import { useStore } from '../../store'

export default function UploadDropzone() {
  const inputRef = useRef<HTMLInputElement>(null)
  const addFile = useStore((s) => s.addFile)
  const updateFile = useStore((s) => s.updateFile)
  const setCurrentFileBuffer = useStore((s) => s.setCurrentFileBuffer)
  const [uploading, setUploading] = useState(false)
  const [error, setError] = useState<string | null>(null)

  async function handleFile(file: File) {
    const id = crypto.randomUUID()
    addFile({ id, name: file.name, taskId: null, analysisId: null, status: 'pending' })
    setUploading(true)
    setError(null)

    try {
      const buffer = await file.arrayBuffer()
      setCurrentFileBuffer(buffer)
    } catch {
      // buffer read failed, preview won't work but upload can still proceed
    }

    try {
      const res = await uploadFile(file)
      updateFile(id, {
        taskId: res.task_id,
        analysisId: res.analysis_id ?? null,
        status: 'processing',
      })
    } catch (err) {
      updateFile(id, { status: 'failed' })
      setError(err instanceof Error ? err.message : 'Upload failed')
    } finally {
      setUploading(false)
    }
  }

  function onDrop(e: React.DragEvent) {
    e.preventDefault()
    const file = e.dataTransfer.files[0]
    if (file) handleFile(file)
  }

  function onChange(e: React.ChangeEvent<HTMLInputElement>) {
    const file = e.target.files?.[0]
    if (file) handleFile(file)
    e.target.value = ''
  }

  return (
    <div>
      <div
        className={`upload-dropzone${uploading ? ' uploading' : ''}`}
        onDragOver={(e) => e.preventDefault()}
        onDrop={onDrop}
      >
        {uploading ? (
          <p>Uploading...</p>
        ) : (
          <>
            <p>Drag and drop a CAD file here</p>
            <p className="upload-formats">.step, .stp, .stl</p>
            <button
              className="upload-browse-btn"
              type="button"
              onClick={() => inputRef.current?.click()}
            >
              Browse Files
            </button>
          </>
        )}
        <input
          ref={inputRef}
          type="file"
          accept=".step,.stp,.stl"
          className="sr-only"
          onChange={onChange}
          disabled={uploading}
        />
      </div>
      {error && <p className="upload-error">{error}</p>}
    </div>
  )
}
