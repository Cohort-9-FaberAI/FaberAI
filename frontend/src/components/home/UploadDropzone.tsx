import { useRef } from 'react'
import { uploadFile } from '../../lib/api'
import { useStore } from '../../store'

export default function UploadDropzone() {
  const inputRef = useRef<HTMLInputElement>(null)
  const addFile = useStore((s) => s.addFile)
  const updateFile = useStore((s) => s.updateFile)

  async function handleFile(file: File) {
    const id = crypto.randomUUID()
    addFile({ id, name: file.name, taskId: null, status: 'pending' })
    try {
      const res = await uploadFile(file)
      updateFile(id, { taskId: res.task_id, status: 'processing' })
    } catch {
      updateFile(id, { status: 'failed' })
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
    <div className="upload-dropzone" onDragOver={(e) => e.preventDefault()} onDrop={onDrop}>
      <p>Drag and drop a CAD file here</p>
      <p className="upload-formats">.step, .stp, .stl</p>
      <button className="upload-browse-btn" type="button" onClick={() => inputRef.current?.click()}>
        Browse Files
      </button>
      <input
        ref={inputRef}
        type="file"
        accept=".step,.stp,.stl"
        className="sr-only"
        onChange={onChange}
      />
    </div>
  )
}
