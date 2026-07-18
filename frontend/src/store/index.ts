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

interface UploadedFile {
  id: string
  name: string
  taskId: string | null
  status: 'pending' | 'processing' | 'completed' | 'failed'
}

interface FileSlice {
  files: UploadedFile[]
  addFile: (f: UploadedFile) => void
  updateFile: (id: string, patch: Partial<UploadedFile>) => void
}

interface AnalysisSlice {
  analysisResult: unknown | null
  setAnalysisResult: (r: unknown | null) => void
}

interface ChatSlice {
  isOpen: boolean
  toggle: () => void
  setOpen: (v: boolean) => void
}

type StoreState = ProjectSlice & FileSlice & AnalysisSlice & ChatSlice

export const useStore = create<StoreState>((set) => ({
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
  addFile: (f) => set((s) => ({ files: [...s.files, f] })),
  updateFile: (id, patch) =>
    set((s) => ({
      files: s.files.map((f) => (f.id === id ? { ...f, ...patch } : f)),
    })),

  // Analysis slice
  analysisResult: null,
  setAnalysisResult: (r) => set({ analysisResult: r }),

  // Chat slice
  isOpen: false,
  toggle: () => set((s) => ({ isOpen: !s.isOpen })),
  setOpen: (v) => set({ isOpen: v }),
}))
