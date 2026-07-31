import { useRef } from 'react'

interface FileDropzoneProps {
  files: File[]
  onChange: (files: File[]) => void
  accept?: string
}

export default function FileDropzone({
  files,
  onChange,
  accept = '.step,.stp,.stl',
}: FileDropzoneProps) {
  const inputRef = useRef<HTMLInputElement>(null)

  function addFiles(incoming: FileList | File[]) {
    const next = Array.from(incoming)
    if (next.length === 0) return
    onChange([...files, ...next])
  }

  function onDrop(e: React.DragEvent) {
    e.preventDefault()
    addFiles(e.dataTransfer.files)
  }

  function onChangeInput(e: React.ChangeEvent<HTMLInputElement>) {
    if (e.target.files) addFiles(e.target.files)
    e.target.value = ''
  }

  return (
    <div className="file-dropzone">
      <div className="file-dropzone-area" onDragOver={(e) => e.preventDefault()} onDrop={onDrop}>
        <p>Drag and drop CAD files here</p>
        <p className="upload-formats">{accept.split(',').join(' ').trim()}</p>
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
          accept={accept}
          multiple
          className="sr-only"
          onChange={onChangeInput}
        />
      </div>
      {files.length > 0 && (
        <ul className="file-dropzone-list">
          {files.map((f, i) => (
            <li key={`${f.name}-${i}`} className="file-dropzone-item">
              <span className="file-dropzone-name">{f.name}</span>
              <button
                type="button"
                className="file-dropzone-remove"
                onClick={() => onChange(files.filter((_, j) => j !== i))}
              >
                Remove
              </button>
            </li>
          ))}
        </ul>
      )}
    </div>
  )
}
