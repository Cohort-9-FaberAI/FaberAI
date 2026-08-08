import { create } from 'zustand'
import { persist } from 'zustand/middleware'

export type FileStatus = 'stored' | 'pending' | 'processing' | 'completed' | 'failed'

export interface ProjectFile {
  id: string
  name: string
  file: File | null
  taskId: string | null
  analysisId: string | null
  status: FileStatus
  errorMessage?: string | null
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

export interface UploadedFile {
  id: string
  name: string
  file: File | null
  taskId: string | null
  analysisId: string | null
  fileUrl?: string | null
  sourceFormat?: 'stl' | 'step' | null
  status: FileStatus
  errorMessage?: string | null
  analysisResult: Record<string, unknown> | null
}

interface FileSlice {
  files: UploadedFile[]
  activeFileId: string | null
  openTabIds: string[]
  addFile: (f: UploadedFile) => void
  updateFile: (id: string, patch: Partial<UploadedFile>) => void
  clearFiles: () => void
  setActiveFileId: (id: string | null) => void
  openTab: (id: string) => void
  closeTab: (id: string) => void
}

interface AnalysisSlice {
  analysisResults: Record<string, Record<string, unknown>>
  setAnalysisResult: (fileId: string, r: Record<string, unknown> | null) => void
}

interface ChatMessage {
  id: string
  role: 'user' | 'assistant'
  text: string
  mode?: 'llm' | 'deterministic'
  referencedRules?: string[]
  degradedReason?: string | null
}

interface ChatSlice {
  isOpen: boolean
  toggle: () => void
  setOpen: (v: boolean) => void
  messages: ChatMessage[]
  addMessage: (m: ChatMessage) => void
  clearMessages: () => void
}

interface ModelSlice {
  currentFileBuffer: ArrayBuffer | null
  setCurrentFileBuffer: (buf: ArrayBuffer | null) => void
  fileBuffers: Record<string, ArrayBuffer>
  setFileBuffer: (fileId: string, buf: ArrayBuffer | null) => void
}

export type ThemeMode = 'dark' | 'light'

interface ThemeSlice {
  theme: ThemeMode
  toggleTheme: () => void
  setTheme: (t: ThemeMode) => void
}

interface SelectedIssueSlice {
  highlightedIssue: string | null
  setHighlightedIssue: (issue: string | null) => void
}

type StoreState = ProjectSettingsSlice &
  WizardSlice &
  ProjectSlice &
  FileSlice &
  AnalysisSlice &
  ChatSlice &
  ModelSlice &
  ThemeSlice &
  SelectedIssueSlice

const EMPTY_WIZARD = { source: 'quick' as WizardSource, projectId: null, fileId: null, file: null }

export const useStore = create<StoreState>()(
  persist(
    (set) => ({
      // Theme slice
      theme: (localStorage.getItem('faberai_theme') as ThemeMode) || 'dark',
      toggleTheme: () =>
        set((s) => {
          const next: ThemeMode = s.theme === 'dark' ? 'light' : 'dark'
          localStorage.setItem('faberai_theme', next)
          document.documentElement.setAttribute('data-theme', next)
          return { theme: next }
        }),
      setTheme: (t: ThemeMode) => {
        localStorage.setItem('faberai_theme', t)
        document.documentElement.setAttribute('data-theme', t)
        set({ theme: t })
      },

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

      // File slice
      files: [],
      activeFileId: null,
      openTabIds: [],
      addFile: (f) =>
        set((s) => ({
          files: [...s.files, f],
          activeFileId: f.id,
          openTabIds: s.openTabIds.includes(f.id) ? s.openTabIds : [...s.openTabIds, f.id],
        })),
      updateFile: (id, patch) =>
        set((s) => ({
          files: s.files.map((f) => (f.id === id ? { ...f, ...patch } : f)),
        })),
      clearFiles: () =>
        set({
          files: [],
          activeFileId: null,
          openTabIds: [],
          analysisResults: {},
          currentFileBuffer: null,
          fileBuffers: {},
        }),
      setActiveFileId: (id) => set({ activeFileId: id }),
      openTab: (id) =>
        set((s) => ({
          openTabIds: s.openTabIds.includes(id) ? s.openTabIds : [...s.openTabIds, id],
          activeFileId: id,
        })),
      closeTab: (id) =>
        set((s) => {
          const filtered = s.openTabIds.filter((tid) => tid !== id)
          const nextActive =
            s.activeFileId === id
              ? filtered.length > 0
                ? filtered[filtered.length - 1]
                : null
              : s.activeFileId
          return {
            openTabIds: filtered,
            activeFileId: nextActive,
          }
        }),

      // Analysis slice – keyed by file ID so each tab has its own result
      analysisResults: {},
      setAnalysisResult: (fileId, r) =>
        set((s) => {
          if (r === null) {
            const rest = { ...s.analysisResults }
            delete rest[fileId]
            return { analysisResults: rest }
          }
          return { analysisResults: { ...s.analysisResults, [fileId]: r } }
        }),

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

      // Model slice
      currentFileBuffer: null,
      setCurrentFileBuffer: (buf) => set({ currentFileBuffer: buf }),
      fileBuffers: {},
      setFileBuffer: (fileId, buf) =>
        set((s) => {
          if (buf === null) {
            const rest = { ...s.fileBuffers }
            delete rest[fileId]
            return { fileBuffers: rest }
          }
          return { fileBuffers: { ...s.fileBuffers, [fileId]: buf } }
        }),

      // Chat slice
      isOpen: false,
      toggle: () => set((s) => ({ isOpen: !s.isOpen })),
      setOpen: (v) => set({ isOpen: v }),
      messages: [],
      addMessage: (m) => set((s) => ({ messages: [...s.messages, m] })),
      clearMessages: () => set({ messages: [] }),

      // SelectedIssue Slice
      highlightedIssue: null,
      setHighlightedIssue: (issue) => set({ highlightedIssue: issue }),
    }),
    {
      name: 'faberai-store',
      partialize: (state) => ({
        ...state,
        currentFileBuffer: null,
        fileBuffers: {},
        projects: state.projects.map((p) => ({
          ...p,
          files: p.files.map((f) => ({ ...f, file: null })),
        })),
        files: state.files.map((f) => ({ ...f, file: null })),
      }),
    },
  ),
)
