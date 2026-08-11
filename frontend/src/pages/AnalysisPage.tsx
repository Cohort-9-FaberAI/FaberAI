import { useEffect, useRef } from 'react'
import { useNavigate } from 'react-router-dom'
import WizardNav from '../components/layout/WizardNav'
import WorkspaceTabs from '../components/workspace/WorkspaceTabs'
import FileSubNav, { type WorkspaceStep } from '../components/workspace/FileSubNav'
import SetupStep from '../components/workspace/steps/SetupStep'
import InspectionStep from '../components/workspace/steps/InspectionStep'
import VerdictStep from '../components/workspace/steps/VerdictStep'
import ExportStep from '../components/workspace/steps/ExportStep'
import { useStore } from '../store'
import { useTaskPolling } from '../lib/useTaskPolling'
import { analyzeFile } from '../lib/useSequentialFileProcessor'
import { asAnalysisResult, hasCompletedReport } from '../lib/analysisView'

function FilePoller({
  file,
}: {
  file: { id: string; taskId: string | null; analysisId: string | null; status: string }
}) {
  const updateFile = useStore((s) => s.updateFile)
  const setAnalysisResult = useStore((s) => s.setAnalysisResult)
  const syncProjectFile = useStore((s) => s.syncProjectFile)

  useTaskPolling(
    file.status === 'processing' && file.taskId && file.taskId !== 'dev-manual'
      ? file.taskId
      : null,
    file.analysisId,
    (data) => {
      const status = typeof data?.status === 'string' ? data.status : null
      const result = data?.result as Record<string, unknown> | undefined
      if (status === 'SUCCESS') {
        updateFile(file.id, { status: 'completed', analysisResult: result ?? null })
        if (result) {
          setAnalysisResult(file.id, result)
        }
        syncProjectFile(file.id)
      }
      if (status === 'FAILED' || status === 'FAILURE') {
        const errorMsg =
          typeof data?.error === 'string'
            ? data.error
            : typeof data?.message === 'string'
              ? data.message
              : 'DFM inspection failed during background processing.'
        updateFile(file.id, { status: 'failed', errorMessage: errorMsg })
        syncProjectFile(file.id)
      }
    },
    () => {
      updateFile(file.id, {
        status: 'failed',
        errorMessage: 'Network timeout or server connection error while checking task status.',
      })
      syncProjectFile(file.id)
    },
  )
  return null
}

export default function AnalysisPage() {
  const navigate = useNavigate()
  const files = useStore((s) => s.files)
  const openTabIds = useStore((s) => s.openTabIds)
  const openTab = useStore((s) => s.openTab)
  const activeFileId = useStore((s) => s.activeFileId)
  const updateFile = useStore((s) => s.updateFile)

  const uploadedFiles = files.filter((f) => f.taskId !== 'dev-manual')
  const activeFile =
    files.find((f) => f.id === activeFileId) ?? uploadedFiles[uploadedFiles.length - 1] ?? null
  const activeId = activeFile?.id ?? ''
  const analysisResult = useStore((s) => s.analysisResults[activeId] ?? null)
  const requestedStep = useStore((s) => s.requestedStep)
  const setRequestedStep = useStore((s) => s.setRequestedStep)
  const storedStepByFile = useStore((s) => s.stepByFile)
  const setStoredStepByFile = useStore((s) => s.setStepByFile)
  const process = useStore((s) => s.process)
  const material = useStore((s) => s.material)
  const tolerance = useStore((s) => s.tolerance)

  // Jump to a requested workspace step (e.g. "inspection" from a project's View Analysis)
  useEffect(() => {
    if (!requestedStep) return
    if (requestedStep.fileId !== activeId) return
    setStoredStepByFile(activeId, requestedStep.step)
    setRequestedStep(null)
  }, [requestedStep, activeId, setStoredStepByFile, setRequestedStep])

  // Auto-open last file tab on first mount if no tabs are open and files exist
  const didInitialOpen = useRef(false)
  useEffect(() => {
    if (didInitialOpen.current) return
    if (uploadedFiles.length > 0 && openTabIds.length === 0) {
      didInitialOpen.current = true
      const lastFile = uploadedFiles[uploadedFiles.length - 1]
      if (lastFile) {
        openTab(lastFile.id)
      }
    }
  }, [uploadedFiles, openTabIds.length, openTab])

  if (uploadedFiles.length === 0) {
    return (
      <div className="workspace-empty-state">
        <svg
          width="56"
          height="56"
          viewBox="0 0 56 56"
          fill="none"
          xmlns="http://www.w3.org/2000/svg"
        >
          <rect x="12" y="14" width="32" height="32" rx="4" stroke="currentColor" strokeWidth="2" />
          <path
            d="M28 22V34M22 28H34"
            stroke="currentColor"
            strokeWidth="2"
            strokeLinecap="round"
          />
        </svg>
        <h2>No CAD Files In Workspace</h2>
        <p>
          Upload one or more 3D CAD geometries (STEP or STL) to launch automated DFM rule inspection
          and supplier scoring.
        </p>
        <button type="button" className="workspace-empty-btn" onClick={() => navigate('/home')}>
          Go to Upload
        </button>
      </div>
    )
  }

  const currentStep: WorkspaceStep = activeFile
    ? (storedStepByFile[activeFile.id] ?? 'setup')
    : 'setup'

  function handleSetStep(newStep: WorkspaceStep) {
    if (activeFile) {
      setStoredStepByFile(activeFile.id, newStep)
    }
  }

  const analysis = asAnalysisResult(analysisResult)
  const canProceedToVerdict = hasCompletedReport(analysis)

  const canAnalyze =
    !!activeFile &&
    activeFile.file !== null &&
    activeFile.status === 'pending' &&
    !activeFile.taskId

  const canViewAnalysis = canProceedToVerdict

  // Configure WizardNav internal transitions
  const stepOrder: WorkspaceStep[] = ['setup', 'inspection', 'verdict', 'export']
  const currentIndex = stepOrder.indexOf(currentStep)

  const handlePrev = () => {
    if (currentIndex === 0) {
      navigate('/home')
    } else {
      handleSetStep(stepOrder[currentIndex - 1])
    }
  }

  const handleNext = () => {
    if (currentIndex < stepOrder.length - 1) {
      if (currentStep === 'setup' && activeFile && canAnalyze) {
        updateFile(activeFile.id, {
          analysisResult: {
            ...activeFile.analysisResult,
            inputs: { process, material, tolerance },
          },
        })
        void analyzeFile(activeFile.id)
      }
      handleSetStep(stepOrder[currentIndex + 1])
    }
  }

  const setupNextDisabled = !canAnalyze && !canViewAnalysis
  const isNextDisabled =
    (currentStep === 'setup' && setupNextDisabled) ||
    (currentStep === 'inspection' && !canProceedToVerdict)
  const hint =
    currentStep === 'setup' && setupNextDisabled
      ? activeFile
        ? activeFile.status === 'processing'
          ? 'This CAD file is currently being analyzed. Results will appear in the DFM Analysis step.'
          : activeFile.status === 'failed'
            ? 'Analysis failed for this file. Re-upload it to retry.'
            : 'This CAD file has already been analyzed.'
        : 'Upload a CAD file in the Uploads step, then run the DFM inspection.'
      : currentStep === 'inspection' && !canProceedToVerdict
        ? 'A completed DFM report is required before proceeding to Conclusion.'
        : null

  return (
    <>
      {files.map((f) =>
        f.taskId !== 'dev-manual' && (f.status === 'processing' || f.status === 'pending') ? (
          <FilePoller key={f.id} file={f} />
        ) : null,
      )}
      <div className="workspace-shell-container">
        <div className="workspace-tabs-header">
          <WorkspaceTabs />
        </div>
        <div className="workspace-content-body">
          <FileSubNav currentStep={currentStep} onSelectStep={handleSetStep} />

          {currentStep === 'setup' && <SetupStep activeFile={activeFile} />}
          {currentStep === 'inspection' && <InspectionStep activeFile={activeFile} />}
          {currentStep === 'verdict' && <VerdictStep activeFile={activeFile} />}
          {currentStep === 'export' && <ExportStep activeFile={activeFile} />}

          <WizardNav
            hint={hint}
            previous={{
              label: currentIndex === 0 ? 'Uploads' : 'Previous',
              onClick: handlePrev,
            }}
            extra={
              currentStep === 'export' ? (
                <button
                  type="button"
                  className="wizard-nav-btn wizard-nav-prev"
                  onClick={() => navigate('/home')}
                >
                  Back to Home
                </button>
              ) : undefined
            }
            next={
              currentIndex < stepOrder.length - 1
                ? {
                    label:
                      currentStep === 'setup'
                        ? canViewAnalysis
                          ? 'View Analysis'
                          : 'Analyze'
                        : 'Next Step',
                    onClick: handleNext,
                    disabled: isNextDisabled,
                    title: hint ?? undefined,
                  }
                : undefined
            }
          />
        </div>
      </div>
    </>
  )
}
