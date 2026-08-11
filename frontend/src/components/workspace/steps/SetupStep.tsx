import WorkflowLayout from '../../layout/WorkflowLayout'
import ProcessToggle from '../../extra-info/ProcessToggle'
import { useStore, DEFAULT_SETTINGS } from '../../../store'
import { asAnalysisResult, hasCompletedReport } from '../../../lib/analysisView'
import type { UploadedFile } from '../../../store'

interface SetupStepProps {
  activeFile: UploadedFile | null
}

export default function SetupStep({ activeFile }: SetupStepProps) {
  const activeId = activeFile?.id ?? ''
  const analysisResult = useStore((s) => s.analysisResults[activeId] ?? null)
  const fileBuffer = useStore((s) => s.fileBuffers[activeId] ?? null)
  const settings = useStore((s) => s.settingsByFile[activeId] ?? DEFAULT_SETTINGS)
  const setSettings = useStore((s) => s.setSettings)
  const { quantity, material, tolerance, process, printingProcess, surfaceFinish } = settings

  const analysis = asAnalysisResult(analysisResult)
  const isLocked = hasCompletedReport(analysis)
  const activeFileIsStl =
    activeFile?.sourceFormat === 'stl' ||
    (!activeFile?.sourceFormat && activeFile?.name.toLowerCase().endsWith('.stl'))
  const livePreviewUrl = activeFileIsStl ? (activeFile?.fileUrl ?? null) : null
  const livePreviewFilename = activeFile?.name ?? null

  const completedPreviewAnalysis = analysis
    ? {
        ...analysis,
        dfm_report: undefined,
        issues: [],
      }
    : null

  return (
    <WorkflowLayout
      eyebrow="Step 01 &bull; Setup"
      title="Confirm manufacturing inputs"
      description="Add the constraints that calibrate DFM evaluation thresholds."
      analysis={completedPreviewAnalysis}
      previewFileUrl={livePreviewUrl}
      previewBuffer={fileBuffer}
      previewSourceFormat={activeFile?.sourceFormat ?? null}
      previewFilename={livePreviewFilename}
    >
      <form className="extra-info-form" onSubmit={(e) => e.preventDefault()}>
        <div className="form-group">
          <label>Process</label>
          <ProcessToggle fileId={activeId} disabled={isLocked} />
        </div>

        <div className="form-group">
          <label htmlFor="quantity">Quantity</label>
          <input
            id="quantity"
            type="number"
            min={1}
            value={quantity}
            disabled={isLocked}
            onChange={(e) => setSettings(activeId, { quantity: Number(e.target.value) })}
          />
        </div>

        <div className="form-group">
          <label htmlFor="material">Material</label>
          <select
            id="material"
            value={material}
            disabled={isLocked}
            onChange={(e) => setSettings(activeId, { material: e.target.value })}
          >
            <option value="">Select material</option>
            <option value="abs">ABS</option>
            <option value="pp">Polypropylene (PP)</option>
            <option value="pc">Polycarbonate (PC)</option>
            <option value="pa66">Nylon PA66</option>
            <option value="pom">POM / Acetal</option>
            <option value="ps">Polystyrene (PS)</option>
            <option value="pbt">PBT</option>
          </select>
        </div>

        {process !== 'printing' && (
          <div className="form-group">
            <label htmlFor="surface-finish">Surface finish</label>
            <select
              id="surface-finish"
              value={surfaceFinish}
              disabled={isLocked}
              onChange={(e) => setSettings(activeId, { surfaceFinish: e.target.value })}
            >
              <option value="">Auto (recommended)</option>
              <option value="semi_gloss">Semi-gloss</option>
              <option value="polished">Polished</option>
              <option value="light_texture">Light texture</option>
              <option value="heavy_texture">Heavy texture</option>
            </select>
          </div>
        )}

        <div className="form-group">
          <label htmlFor="tolerance">Tolerance</label>
          <select
            id="tolerance"
            value={tolerance}
            disabled={isLocked}
            onChange={(e) => setSettings(activeId, { tolerance: e.target.value })}
          >
            <option value="">Select tolerance</option>
            <option value="standard">Standard (&plusmn;0.5mm)</option>
            <option value="tight">Tight (&plusmn;0.2mm)</option>
            <option value="precision">Precision (&plusmn;0.1mm)</option>
          </select>
        </div>

        {process !== 'molding' && (
          <div className="form-group">
            <label htmlFor="printing-process">Printing process</label>
            <select
              id="printing-process"
              value={printingProcess}
              disabled={isLocked}
              onChange={(e) => setSettings(activeId, { printingProcess: e.target.value })}
            >
              <option value="">Auto (recommended)</option>
              <option value="fdm">FDM</option>
              <option value="sla">SLA (resin)</option>
              <option value="sls">SLS</option>
              <option value="mjf">MJF</option>
            </select>
          </div>
        )}
      </form>
    </WorkflowLayout>
  )
}
