import WorkflowLayout from '../../layout/WorkflowLayout'
import ProcessToggle from '../../extra-info/ProcessToggle'
import { useStore } from '../../../store'
import { asAnalysisResult } from '../../../lib/analysisView'
import type { UploadedFile } from '../../../store'

interface SetupStepProps {
  activeFile: UploadedFile | null
}

export default function SetupStep({ activeFile }: SetupStepProps) {
  const activeId = activeFile?.id ?? ''
  const analysisResult = useStore((s) => s.analysisResults[activeId] ?? null)
  const fileBuffer = useStore((s) => s.fileBuffers[activeId] ?? null)
  const quantity = useStore((s) => (activeId ? (s.quantityByFile[activeId] ?? 1) : s.quantity))
  const material = useStore((s) => (activeId ? (s.materialByFile[activeId] ?? '') : s.material))
  const process = useStore((s) => (activeId ? (s.processByFile[activeId] ?? null) : s.process))
  const printingProcess = useStore((s) =>
    activeId ? (s.printingProcessByFile[activeId] ?? '') : s.printingProcess,
  )
  const tolerance = useStore((s) => (activeId ? (s.toleranceByFile[activeId] ?? '') : s.tolerance))
  const setFileQuantity = useStore((s) => s.setFileQuantity)
  const setFileMaterial = useStore((s) => s.setFileMaterial)
  const setFilePrintingProcess = useStore((s) => s.setFilePrintingProcess)
  const setFileTolerance = useStore((s) => s.setFileTolerance)

  const analysis = asAnalysisResult(analysisResult)
  const analysisStarted =
    activeFile?.status === 'processing' ||
    activeFile?.status === 'completed' ||
    Boolean(activeFile?.taskId)
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
      <form
        className={`extra-info-form${analysisStarted ? ' is-locked' : ''}`}
        onSubmit={(e) => e.preventDefault()}
      >
        <div className="form-group">
          <label>Process</label>
          <ProcessToggle disabled={analysisStarted} fileId={activeId} />
        </div>

        <div className="form-group">
          <label htmlFor="quantity">Quantity</label>
          <input
            id="quantity"
            type="number"
            min={1}
            value={quantity}
            disabled={analysisStarted}
            onChange={(e) => setFileQuantity(activeId, Number(e.target.value))}
          />
        </div>

        <div className="form-group">
          <label htmlFor="material">Material</label>
          <select
            id="material"
            value={material}
            disabled={analysisStarted}
            onChange={(e) => setFileMaterial(activeId, e.target.value)}
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

        {process === 'printing' && (
          <div className="form-group">
            <label htmlFor="printing_process">Printing process</label>
            <select
              id="printing_process"
              value={printingProcess || ''}
              disabled={analysisStarted}
              onChange={(e) => setFilePrintingProcess(activeId, e.target.value)}
            >
              <option value="">Select process</option>
              <option value="fdm">FDM</option>
              <option value="sla">SLA / resin</option>
              <option value="sls">SLS</option>
              <option value="mjf">MJF</option>
            </select>
          </div>
        )}

        <div className="form-group">
          <label htmlFor="tolerance">Tolerance</label>
          <select
            id="tolerance"
            value={tolerance}
            disabled={analysisStarted}
            onChange={(e) => setFileTolerance(activeId, e.target.value)}
          >
            <option value="">Select tolerance</option>
            <option value="standard">Standard (&plusmn;0.5mm)</option>
            <option value="tight">Tight (&plusmn;0.2mm)</option>
            <option value="precision">Precision (&plusmn;0.1mm)</option>
          </select>
        </div>
      </form>
    </WorkflowLayout>
  )
}
