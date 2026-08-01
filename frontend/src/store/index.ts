import { create } from 'zustand'

interface ProjectSlice {
  isProject: boolean
  process: 'molding' | 'printing' | null
  quantity: number
  material: string
  tolerance: string
  notes: string
  setProject: (v: boolean) => void
  setProcess: (v: 'molding' | 'printing' | null) => void
  setQuantity: (v: number) => void
  setMaterial: (v: string) => void
  setTolerance: (v: string) => void
  setNotes: (v: string) => void
}

export interface UploadedFile {
  id: string
  name: string
  taskId: string | null
  analysisId: string | null
  fileUrl?: string | null
  sourceFormat?: 'stl' | 'step' | null
  status: 'pending' | 'processing' | 'completed' | 'failed'
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
  analysisResult: Record<string, unknown> | null
  setAnalysisResult: (r: Record<string, unknown> | null) => void
}

interface ChatSlice {
  isOpen: boolean
  toggle: () => void
  setOpen: (v: boolean) => void
}

interface ModelSlice {
  currentFileBuffer: ArrayBuffer | null
  setCurrentFileBuffer: (buf: ArrayBuffer | null) => void
}

interface ProjectRecord {
  id: string
  fileName: string
  description: string
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
  projects: ProjectRecord[]
  libraryItems: LibraryRecord[]
  historyEntries: HistoryRecord[]
  addProject: (p: ProjectRecord) => void
  updateProject: (id: string, patch: Partial<ProjectRecord>) => void
  deleteProject: (id: string) => void
  deleteLibraryItem: (id: string) => void
  addLibraryItem: (l: LibraryRecord) => void
  linkLibraryItemToProject: (itemId: string, projectId: string) => void
}

export type ThemeMode = 'dark' | 'light'

interface ThemeSlice {
  theme: ThemeMode
  toggleTheme: () => void
  setTheme: (t: ThemeMode) => void
}

type StoreState = ProjectSlice &
  FileSlice &
  AnalysisSlice &
  ChatSlice &
  ModelSlice &
  RecordsSlice &
  ThemeSlice

export const useStore = create<StoreState>((set) => ({
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

  // Project slice
  isProject: false,
  process: null,
  quantity: 1,
  material: '',
  tolerance: '',
  notes: '',
  setProject: (v) => set({ isProject: v }),
  setProcess: (v) => set({ process: v }),
  setQuantity: (v) => set({ quantity: v }),
  setMaterial: (v) => set({ material: v }),
  setTolerance: (v) => set({ tolerance: v }),
  setNotes: (v) => set({ notes: v }),

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
      analysisResult: null,
      currentFileBuffer: null,
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

  // Analysis slice
  analysisResult: null,
  setAnalysisResult: (r) => set({ analysisResult: r }),

  // Chat slice
  isOpen: false,
  toggle: () => set((s) => ({ isOpen: !s.isOpen })),
  setOpen: (v) => set({ isOpen: v }),

  // Model slice
  currentFileBuffer: null,
  setCurrentFileBuffer: (buf) => set({ currentFileBuffer: buf }),

  // Records slice
  projects: [],
  libraryItems: [],
  historyEntries: [],
  addProject: (p) => set((s) => ({ projects: [...s.projects, p] })),
  updateProject: (id, patch) =>
    set((s) => ({
      projects: s.projects.map((p) => (p.id === id ? { ...p, ...patch } : p)),
    })),
  deleteProject: (id) => set((s) => ({ projects: s.projects.filter((p) => p.id !== id) })),
  deleteLibraryItem: (id) =>
    set((s) => ({ libraryItems: s.libraryItems.filter((l) => l.id !== id) })),
  addLibraryItem: (l) => set((s) => ({ libraryItems: [...s.libraryItems, l] })),
  linkLibraryItemToProject: (itemId, projectId) =>
    set((s) => ({
      libraryItems: s.libraryItems.map((l) => (l.id === itemId ? { ...l, projectId } : l)),
    })),
}))
