import { create } from 'zustand'
import { persist } from 'zustand/middleware'

export type FileStatus = 'stored' | 'processing' | 'completed' | 'failed'

export interface ProjectFile {
  id: string
  name: string
  file: File | null
  taskId: string | null
  analysisId: string | null
  status: FileStatus
  analysisResult: Record<string, unknown> | null
}

export interface Project {
  id: string
  name: string
  description: string
  files: ProjectFile[]
  createdAt: string
}

export type WizardSource = 'quick' | 'project' | 'view'

interface ProjectSettingsSlice {
  isProject: boolean
  process: 'molding' | 'printing' | null
  quantity: number
  material: string
  tolerance: string
  setProject: (v: boolean) => void
  setProcess: (v: 'molding' | 'printing' | null) => void
  setQuantity: (v: number) => void
  setMaterial: (v: string) => void
  setTolerance: (v: string) => void
}

interface WizardSlice {
  source: WizardSource
  projectId: string | null
  fileId: string | null
  file: File | null
  setWizard: (patch: Partial<Omit<WizardSlice, 'file'>> & { file?: File | null }) => void
  resetWizard: () => void
}

interface ProjectSlice {
  projects: Project[]
  addProject: (p: Omit<Project, 'id' | 'createdAt'> & { id?: string; createdAt?: string }) => void
  updateProject: (id: string, patch: Partial<Pick<Project, 'name' | 'description'>>) => void
  deleteProject: (id: string) => void
  addProjectFiles: (projectId: string, files: ProjectFile[]) => void
  removeProjectFile: (projectId: string, fileId: string) => void
  updateProjectFile: (projectId: string, fileId: string, patch: Partial<ProjectFile>) => void
}

interface UploadedFile {
  id: string
  name: string
  file: File | null
  taskId: string | null
  analysisId: string | null
  status: FileStatus
  analysisResult: Record<string, unknown> | null
}

interface FileSlice {
  files: UploadedFile[]
  addFile: (f: UploadedFile) => void
  updateFile: (id: string, patch: Partial<UploadedFile>) => void
  clearFiles: () => void
}

interface AnalysisSlice {
  analysisResult: Record<string, unknown> | null
  setAnalysisResult: (r: Record<string, unknown> | null) => void
}

interface ChatSlice {
  isOpen: boolean
  toggle: () => void
  setOpen: (v: boolean) => void
}

interface LibraryRecord {
  id: string
  fileName: string
  diagnosis: string
  projectId?: string | null
}

interface HistoryRecord {
  id: string
  fileName: string
  diagnosis: string
  date: string
}

interface RecordsSlice {
  libraryItems: LibraryRecord[]
  historyEntries: HistoryRecord[]
  deleteLibraryItem: (id: string) => void
  addLibraryItem: (l: LibraryRecord) => void
  linkLibraryItemToProject: (itemId: string, projectId: string) => void
}

type StoreState = ProjectSettingsSlice &
  WizardSlice &
  ProjectSlice &
  FileSlice &
  AnalysisSlice &
  ChatSlice &
  RecordsSlice

const EMPTY_WIZARD = { source: 'quick' as WizardSource, projectId: null, fileId: null, file: null }

export const useStore = create<StoreState>()(
  persist(
    (set) => ({
      // Project settings slice
      isProject: false,
      process: null,
      quantity: 1,
      material: '',
      tolerance: '',
      setProject: (v) => set({ isProject: v }),
      setProcess: (v) => set({ process: v }),
      setQuantity: (v) => set({ quantity: v }),
      setMaterial: (v) => set({ material: v }),
      setTolerance: (v) => set({ tolerance: v }),

      // Wizard slice
      ...EMPTY_WIZARD,
      setWizard: (patch) => set((s) => ({ ...s, ...patch })),
      resetWizard: () => set(EMPTY_WIZARD),

      // Project slice
      projects: [],
      addProject: (p) =>
        set((s) => ({
          projects: [
            ...s.projects,
            {
              ...p,
              id: p.id ?? crypto.randomUUID(),
              createdAt: p.createdAt ?? new Date().toISOString(),
            },
          ],
        })),
      updateProject: (id, patch) =>
        set((s) => ({
          projects: s.projects.map((p) => (p.id === id ? { ...p, ...patch } : p)),
        })),
      deleteProject: (id) => set((s) => ({ projects: s.projects.filter((p) => p.id !== id) })),
      addProjectFiles: (projectId, files) =>
        set((s) => ({
          projects: s.projects.map((p) =>
            p.id === projectId ? { ...p, files: [...p.files, ...files] } : p,
          ),
        })),
      removeProjectFile: (projectId, fileId) =>
        set((s) => ({
          projects: s.projects.map((p) =>
            p.id === projectId ? { ...p, files: p.files.filter((f) => f.id !== fileId) } : p,
          ),
        })),
      updateProjectFile: (projectId, fileId, patch) =>
        set((s) => ({
          projects: s.projects.map((p) =>
            p.id === projectId
              ? {
                  ...p,
                  files: p.files.map((f) => (f.id === fileId ? { ...f, ...patch } : f)),
                }
              : p,
          ),
        })),

      // File slice
      files: [],
      addFile: (f) => set((s) => ({ files: [...s.files, f] })),
      updateFile: (id, patch) =>
        set((s) => ({
          files: s.files.map((f) => (f.id === id ? { ...f, ...patch } : f)),
        })),
      clearFiles: () => set({ files: [] }),

      // Analysis slice
      analysisResult: null,
      setAnalysisResult: (r) => set({ analysisResult: r }),

      // Chat slice
      isOpen: false,
      toggle: () => set((s) => ({ isOpen: !s.isOpen })),
      setOpen: (v) => set({ isOpen: v }),

      // Records slice
      libraryItems: [],
      historyEntries: [],
      deleteLibraryItem: (id) =>
        set((s) => ({ libraryItems: s.libraryItems.filter((l) => l.id !== id) })),
      addLibraryItem: (l) => set((s) => ({ libraryItems: [...s.libraryItems, l] })),
      linkLibraryItemToProject: (itemId, projectId) =>
        set((s) => ({
          libraryItems: s.libraryItems.map((l) => (l.id === itemId ? { ...l, projectId } : l)),
        })),
    }),
    {
      name: 'faberai-store',
      partialize: (state) => ({
        projects: state.projects.map((p) => ({
          ...p,
          files: p.files.map((f) => ({ ...f, file: null })),
        })),
        files: state.files.map((f) => ({ ...f, file: null })),
      }),
    },
  ),
)
