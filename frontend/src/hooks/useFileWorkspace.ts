import { DEFAULT_SETTINGS, useStore, type UploadedFile } from '../store'
import { asAnalysisResult } from '../lib/analysisView'

/** Read the active file's analysis, settings, and preview consistently across wizard steps. */
export function useFileWorkspace(activeFile: UploadedFile | null) {
  const activeId = activeFile?.id ?? ''
  const analysisResult = useStore((s) => s.analysisResults[activeId] ?? null)
  const fileBuffer = useStore((s) => s.fileBuffers[activeId] ?? null)
  const settings = useStore((s) => s.settingsByFile[activeId] ?? DEFAULT_SETTINGS)
  const isStl =
    activeFile?.sourceFormat === 'stl' ||
    (!activeFile?.sourceFormat && activeFile?.name.toLowerCase().endsWith('.stl'))

  return {
    activeId,
    analysisResult,
    analysis: asAnalysisResult(analysisResult),
    settings,
    previewProps: {
      previewFileUrl: isStl ? (activeFile?.fileUrl ?? null) : null,
      previewBuffer: fileBuffer,
      previewSourceFormat: activeFile?.sourceFormat ?? null,
      previewFilename: activeFile?.name ?? null,
    },
  }
}
