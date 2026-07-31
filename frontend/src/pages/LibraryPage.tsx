import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import AppShell from '../components/layout/AppShell'
import SearchBar from '../components/common/SearchBar'
import ListRow from '../components/common/ListRow'
import Modal from '../components/common/Modal'
import { useStore } from '../store'

export default function LibraryPage() {
  const navigate = useNavigate()
  const items = useStore((s) => s.libraryItems)
  const projects = useStore((s) => s.projects)
  const deleteLibraryItem = useStore((s) => s.deleteLibraryItem)
  const linkLibraryItemToProject = useStore((s) => s.linkLibraryItemToProject)
  const [query, setQuery] = useState('')
  const [pickerOpen, setPickerOpen] = useState(false)
  const [pickerTarget, setPickerTarget] = useState<string | null>(null)

  const filtered = items.filter(
    (e) =>
      e.fileName.toLowerCase().includes(query.toLowerCase()) ||
      e.diagnosis.toLowerCase().includes(query.toLowerCase()),
  )

  function openPicker(itemId: string) {
    setPickerTarget(itemId)
    setPickerOpen(true)
  }

  return (
    <AppShell>
      <h1>Library</h1>

      <div className="list-header">
        <SearchBar value={query} onChange={setQuery} />
        <button type="button" onClick={() => navigate('/upload')}>
          Add New 3D Model
        </button>
      </div>

      <Modal open={pickerOpen} onClose={() => setPickerOpen(false)}>
        <h2>Save to Project</h2>
        <div className="picker-list">
          {projects.map((p) => (
            <button
              key={p.id}
              type="button"
              className="picker-item"
              onClick={() => {
                if (pickerTarget) {
                  linkLibraryItemToProject(pickerTarget, p.id)
                }
                setPickerOpen(false)
                setPickerTarget(null)
              }}
            >
              {p.name}
            </button>
          ))}
          {projects.length === 0 && <p className="list-empty">No projects yet.</p>}
        </div>
      </Modal>

      <div className="list-container">
        {filtered.map((item) => {
          const linkedProject = item.projectId
            ? projects.find((p) => p.id === item.projectId)
            : null
          return (
            <ListRow
              key={item.id}
              fields={[
                { label: 'File Name', value: item.fileName },
                { label: 'Diagnosis', value: item.diagnosis },
                {
                  label: 'Project',
                  value: linkedProject ? linkedProject.name : 'None',
                },
              ]}
              actions={[
                { label: 'Save to Project', onClick: () => openPicker(item.id) },
                { label: 'Delete', onClick: () => deleteLibraryItem(item.id) },
              ]}
            />
          )
        })}
        {filtered.length === 0 && <p className="list-empty">No library items found.</p>}
      </div>
    </AppShell>
  )
}
