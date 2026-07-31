import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import AppShell from '../components/layout/AppShell'
import SearchBar from '../components/common/SearchBar'
import ProjectForm from '../components/projects/ProjectForm'
import { useStore } from '../store'

export default function ProjectsPage() {
  const navigate = useNavigate()
  const projects = useStore((s) => s.projects)
  const addProject = useStore((s) => s.addProject)
  const updateProject = useStore((s) => s.updateProject)
  const deleteProject = useStore((s) => s.deleteProject)
  const [query, setQuery] = useState('')
  const [showCreate, setShowCreate] = useState(false)
  const [editTarget, setEditTarget] = useState<string | null>(null)

  const filtered = projects.filter(
    (p) =>
      p.name.toLowerCase().includes(query.toLowerCase()) ||
      p.description.toLowerCase().includes(query.toLowerCase()),
  )

  const editProject = editTarget ? projects.find((p) => p.id === editTarget) : null

  function handleCreate(data: { name: string; description: string; files: File[] }) {
    const projectId = crypto.randomUUID()
    addProject({
      id: projectId,
      name: data.name,
      description: data.description,
      files: data.files.map((f) => ({
        id: crypto.randomUUID(),
        name: f.name,
        file: f,
        taskId: null,
        analysisId: null,
        status: 'stored' as const,
        analysisResult: null,
      })),
    })
    setShowCreate(false)
    navigate(`/projects/${projectId}`)
  }

  function handleEdit(data: { name: string; description: string; files: File[] }) {
    if (!editTarget) return
    updateProject(editTarget, { name: data.name, description: data.description })
    setEditTarget(null)
  }

  function formatDate(iso: string) {
    return new Date(iso).toLocaleDateString(undefined, {
      year: 'numeric',
      month: 'short',
      day: 'numeric',
    })
  }

  return (
    <AppShell>
      <h1>Projects</h1>
      <p className="page-note">Organize CAD files into projects and analyze them on demand.</p>

      <div className="list-header">
        <SearchBar value={query} onChange={setQuery} placeholder="Search projects..." />
        <button
          type="button"
          onClick={() => {
            setEditTarget(null)
            setShowCreate(true)
          }}
        >
          New Project
        </button>
      </div>

      {showCreate && (
        <ProjectForm mode="create" onSubmit={handleCreate} onCancel={() => setShowCreate(false)} />
      )}

      {editTarget && (
        <ProjectForm
          key={editTarget}
          mode="edit"
          initialName={editProject?.name ?? ''}
          initialDescription={editProject?.description ?? ''}
          onSubmit={handleEdit}
          onCancel={() => setEditTarget(null)}
        />
      )}

      {!showCreate &&
        !editTarget &&
        (filtered.length === 0 ? (
          <p className="list-empty">No projects found.</p>
        ) : (
          <div className="project-list">
            {filtered.map((p) => (
              <div key={p.id} className="project-row">
                <div className="project-row-main">
                  <div className="project-row-title">
                    <h3>{p.name}</h3>
                    <span className="project-file-count">
                      {p.files.length} file{p.files.length === 1 ? '' : 's'}
                    </span>
                  </div>
                  <p className="project-row-desc">{p.description || 'No description'}</p>
                  <div className="project-row-meta">
                    <span>Created {formatDate(p.createdAt)}</span>
                  </div>
                </div>
                <div className="project-row-actions">
                  <button
                    type="button"
                    className="project-open-btn"
                    onClick={() => navigate(`/projects/${p.id}`)}
                  >
                    Open
                  </button>
                  <button
                    type="button"
                    onClick={() => {
                      setShowCreate(false)
                      setEditTarget(p.id)
                    }}
                  >
                    Edit
                  </button>
                  <button type="button" onClick={() => deleteProject(p.id)}>
                    Delete
                  </button>
                </div>
              </div>
            ))}
          </div>
        ))}
    </AppShell>
  )
}
