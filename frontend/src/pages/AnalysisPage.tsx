import { useState, useEffect } from 'react'
import { useNavigate } from 'react-router-dom'
import AppShell from '../components/layout/AppShell'
import WizardNav from '../components/layout/WizardNav'
import WorkspaceTabs from '../components/workspace/WorkspaceTabs'
import FileSubNav, { type WorkspaceStep } from '../components/workspace/FileSubNav'
import SetupStep from '../components/workspace/steps/SetupStep'
import InspectionStep from '../components/workspace/steps/InspectionStep'
import VerdictStep from '../components/workspace/steps/VerdictStep'
import ExportStep from '../components/workspace/steps/ExportStep'
import { useStore } from '../store'
import { useTaskPolling } from '../lib/useTaskPolling'
import { asAnalysisResult, hasCompletedReport } from '../lib/analysisView'

export default function AnalysisPage() {
  const navigate = useNavigate()
  const files = useStore((s) => s.files)
  const openTabIds = useStore((s) => s.openTabIds)
  const openTab = useStore((s) => s.openTab)
  const activeFileId = useStore((s) => s.activeFileId)
  const updateFile = useStore((s) => s.updateFile)
  const analysisResult = useStore((s) => s.analysisResult)
  const setAnalysisResult = useStore((s) => s.setAnalysisResult)

  const [stepByFile, setStepByFile] = useState<Record<string, WorkspaceStep>>({})

  const uploadedFiles = files.filter((f) => f.taskId !== 'dev-manual')
  const activeFile =
    files.find((f) => f.id === activeFileId) ?? uploadedFiles[uploadedFiles.length - 1] ?? null

  // Auto-open last file tab if no tabs are open and files exist
  useEffect(() => {
    if (uploadedFiles.length > 0 && openTabIds.length === 0) {
      const lastFile = uploadedFiles[uploadedFiles.length - 1]
      if (lastFile) {
        openTab(lastFile.id)
      }
    }
  }, [uploadedFiles, openTabIds.length, openTab])

  // Real-time task polling for active file tab
  const taskId = activeFile?.taskId ?? null
  const isDevManual = taskId === 'dev-manual'
  useTaskPolling(
    isDevManual ? null : taskId,
    activeFile?.analysisId,
    (data) => {
      const status = typeof data?.status === 'string' ? data.status : null
      if (status === 'SUCCESS' && activeFile) {
        updateFile(activeFile.id, { status: 'completed' })
      }
      if ((status === 'FAILED' || status === 'FAILURE') && activeFile) {
        updateFile(activeFile.id, { status: 'failed' })
      }
      const result = data?.result as Record<string, unknown> | undefined
      if (result) {
        setAnalysisResult(result)
      }
    },
    () => {
      if (activeFile) {
        updateFile(activeFile.id, { status: 'failed' })
      }
    },
  )

  if (uploadedFiles.length === 0) {
    return (
      <AppShell>
        <div className="workspace-empty-state">
          <svg
            width="56"
            height="56"
            viewBox="0 0 56 56"
            fill="none"
            xmlns="http://www.w3.org/2000/svg"
          >
            <rect
              x="12"
              y="14"
              width="32"
              height="32"
              rx="4"
              stroke="currentColor"
              strokeWidth="2"
            />
            <path
              d="M28 22V34M22 28H34"
              stroke="currentColor"
              strokeWidth="2"
              strokeLinecap="round"
            />
          </svg>
          <h2>No CAD Files In Workspace</h2>
          <p>
            Upload one or more 3D CAD geometries (STEP or STL) to launch automated DFM rule
            inspection and supplier scoring.
          </p>
          <button type="button" className="workspace-empty-btn" onClick={() => navigate('/home')}>
            Go to Upload
          </button>
        </div>
      </AppShell>
    )
  }

  const currentStep: WorkspaceStep = activeFile ? (stepByFile[activeFile.id] ?? 'setup') : 'setup'

  function handleSetStep(newStep: WorkspaceStep) {
    if (activeFile) {
      setStepByFile((prev) => ({ ...prev, [activeFile.id]: newStep }))
    }
  }

  const analysis = asAnalysisResult(analysisResult)
  const canProceedToVerdict = hasCompletedReport(analysis)

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
      handleSetStep(stepOrder[currentIndex + 1])
    }
  }

  const isNextDisabled = currentStep === 'inspection' && !canProceedToVerdict
  const hint =
    currentStep === 'inspection' && !canProceedToVerdict
      ? 'A completed DFM report is required before proceeding to Conclusion.'
      : null

  return (
    <AppShell>
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
            next={
              currentIndex < stepOrder.length - 1
                ? {
                    label: 'Next Step',
                    onClick: handleNext,
                    disabled: isNextDisabled,
                    title: hint ?? undefined,
                  }
                : undefined
            }
          />
        </div>
      </div>
    </AppShell>
  )
}
