import { useRef } from 'react'
import { useStore } from '../../store'

export default function UploadDropzone() {
  const inputRef = useRef<HTMLInputElement>(null)
  const clearFiles = useStore((s) => s.clearFiles)
  const addFile = useStore((s) => s.addFile)

  function handleFile(file: File) {
    clearFiles()
    addFile({
      id: crypto.randomUUID(),
      name: file.name,
      file,
      taskId: null,
      analysisId: null,
      status: 'stored',
      analysisResult: null,
    })
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
      <div className="upload-dropzone" onDragOver={(e) => e.preventDefault()} onDrop={onDrop}>
        <p>Drag and drop a CAD file here</p>
        <p className="upload-formats">.step, .stp, .stl</p>
        <button
          className="upload-browse-btn"
          type="button"
          onClick={() => inputRef.current?.click()}
        >
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
    </div>
  )
}
