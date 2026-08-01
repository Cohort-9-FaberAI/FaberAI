import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import AppShell from '../components/layout/AppShell'
import SearchBar from '../components/common/SearchBar'
import ListRow from '../components/common/ListRow'
import Modal from '../components/common/Modal'
import { useStore } from '../store'

export default function ProjectsPage() {
  const navigate = useNavigate()
  const projects = useStore((s) => s.projects)
  const updateProject = useStore((s) => s.updateProject)
  const deleteProject = useStore((s) => s.deleteProject)
  const [query, setQuery] = useState('')
  const [editTarget, setEditTarget] = useState<string | null>(null)
  const [editName, setEditName] = useState('')
  const [editDesc, setEditDesc] = useState('')

  const filtered = projects.filter(
    (e) =>
      e.fileName.toLowerCase().includes(query.toLowerCase()) ||
      e.description.toLowerCase().includes(query.toLowerCase()),
  )

  function openEdit(id: string) {
    const p = projects.find((proj) => proj.id === id)
    if (!p) return
    setEditTarget(id)
    setEditName(p.fileName)
    setEditDesc(p.description)
  }

  function saveEdit() {
    if (!editTarget) return
    updateProject(editTarget, { fileName: editName, description: editDesc })
    setEditTarget(null)
  }

  return (
    <AppShell>
      <h1>Projects</h1>

      <div className="list-header">
        <SearchBar value={query} onChange={setQuery} />
        <button type="button" className="list-add-btn" onClick={() => navigate('/home')}>
          New Project
        </button>
      </div>

      <Modal open={editTarget !== null} onClose={() => setEditTarget(null)}>
        <h2>Edit Project</h2>
        <div className="edit-form">
          <label className="login-field">
            <span>File Name</span>
            <input type="text" value={editName} onChange={(e) => setEditName(e.target.value)} />
          </label>
          <label className="login-field">
            <span>Description</span>
            <input type="text" value={editDesc} onChange={(e) => setEditDesc(e.target.value)} />
          </label>
          <div className="modal-actions">
            <button type="button" onClick={() => setEditTarget(null)}>
              Cancel
            </button>
            <button type="button" onClick={saveEdit}>
              Save
            </button>
          </div>
        </div>
      </Modal>

      <div className="list-container">
        {filtered.map((p) => (
          <ListRow
            key={p.id}
            fields={[
              { label: 'File Name', value: p.fileName },
              { label: 'Description', value: p.description },
            ]}
            actions={[
              { label: 'Edit', onClick: () => openEdit(p.id) },
              { label: 'Delete', onClick: () => deleteProject(p.id) },
            ]}
          />
        ))}
        {filtered.length === 0 && <p className="list-empty">No projects found.</p>}
      </div>
    </AppShell>
  )
}
