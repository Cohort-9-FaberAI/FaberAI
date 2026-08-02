import { useRef, useState } from 'react'
import { useStore } from '../../store'

export default function UploadDropzone() {
  const inputRef = useRef<HTMLInputElement>(null)
  const addFile = useStore((s) => s.addFile)
  const setCurrentFileBuffer = useStore((s) => s.setCurrentFileBuffer)
  const setFileBuffer = useStore((s) => s.setFileBuffer)
  const [uploading, setUploading] = useState(false)
  const [error, setError] = useState<string | null>(null)

  async function handleSingleFile(file: File) {
    const id = crypto.randomUUID()
    const lowerName = file.name.toLowerCase()
    const sourceFormat = lowerName.endsWith('.stl')
      ? 'stl'
      : lowerName.endsWith('.step') || lowerName.endsWith('.stp')
        ? 'step'
        : null

    addFile({
      id,
      name: file.name,
      file,
      taskId: null,
      analysisId: null,
      fileUrl: null,
      sourceFormat,
      status: 'pending',
      analysisResult: null,
    })

    if (sourceFormat === 'stl') {
      try {
        const buffer = await file.arrayBuffer()
        setFileBuffer(id, buffer)
        setCurrentFileBuffer(buffer)
      } catch {
        // buffer read failed, preview won't work immediately but upload proceeds
      }
    } else {
      setFileBuffer(id, null)
      setCurrentFileBuffer(null)
    }
  }

  async function handleFiles(fileList: FileList | File[] | null | undefined) {
    if (!fileList || fileList.length === 0) return
    const files = Array.from(fileList).filter((f) => {
      const name = f.name.toLowerCase()
      return name.endsWith('.stl') || name.endsWith('.step') || name.endsWith('.stp')
    })
    if (files.length === 0) {
      setError('Please upload valid CAD files (.STEP, .STP, .STL)')
      return
    }

    setUploading(true)
    setError(null)
    try {
      for (const file of files) {
        await handleSingleFile(file)
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to process files')
    } finally {
      setUploading(false)
    }
  }

  function onDrop(e: React.DragEvent) {
    e.preventDefault()
    handleFiles(e.dataTransfer.files)
  }

  function onChange(e: React.ChangeEvent<HTMLInputElement>) {
    handleFiles(e.target.files)
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
          <div className="scan-loading">
            <span className="scan-line-inline" />
            <p>Uploading CAD files</p>
            <small>Creating analysis jobs</small>
          </div>
        ) : (
          <>
            <svg className="upload-glyph" viewBox="0 0 52 52" fill="none" aria-hidden="true">
              <path
                d="M26 6L44 16V36L26 46L8 36V16L26 6Z"
                stroke="currentColor"
                strokeWidth="1.6"
              />
              <path d="M26 26L44 16M26 26V46M26 26L8 16" stroke="currentColor" strokeWidth="1.6" />
              <circle cx="26" cy="26" r="3" fill="var(--toolpath)" />
            </svg>
            <h2>Drag and drop CAD files here</h2>
            <p className="upload-formats">.STEP · .STP · .STL (Multiple files allowed)</p>
            {error ? (
              <p className="chat-error" style={{ margin: '8px 0 0' }}>
                {error}
              </p>
            ) : null}
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
          multiple={true}
          className="sr-only"
          onChange={onChange}
        />
      </div>
    </div>
  )
}
