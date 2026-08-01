import { useState, useEffect, useRef } from 'react'
import { useStore } from '../../store'
import AddTabModal from './AddTabModal'

export default function WorkspaceTabs() {
  const files = useStore((s) => s.files)
  const openTabIds = useStore((s) => s.openTabIds)
  const activeFileId = useStore((s) => s.activeFileId)
  const setActiveFileId = useStore((s) => s.setActiveFileId)
  const closeTab = useStore((s) => s.closeTab)
  const setAnalysisResult = useStore((s) => s.setAnalysisResult)
  const [modalOpen, setModalOpen] = useState(false)
  const tabsRef = useRef<HTMLDivElement>(null)

  useEffect(() => {
    const el = tabsRef.current
    if (!el) return
    const onWheel = (e: WheelEvent) => {
      if (e.deltaY !== 0) {
        e.preventDefault()
        el.scrollLeft += e.deltaY
      }
    }
    el.addEventListener('wheel', onWheel, { passive: false })
    return () => el.removeEventListener('wheel', onWheel)
  }, [openTabIds.length])

  return (
    <>
      <div
        ref={tabsRef}
        className="browser-tabs-nav full-width-tabs"
        aria-label="Open CAD file tabs"
      >
        {openTabIds.map((tabId) => {
          const file = files.find((f) => f.id === tabId)
          if (!file) return null

          const isActive = file.id === activeFileId
          const isProcessing = file.status === 'processing' || file.status === 'pending'

          return (
            <div
              key={file.id}
              role="tab"
              aria-selected={isActive}
              tabIndex={0}
              className={`browser-tab${isActive ? ' active' : ''}`}
              onClick={() => {
                if (file.id !== activeFileId) {
                  setActiveFileId(file.id)
                  setAnalysisResult(null)
                }
              }}
              onKeyDown={(e) => {
                if (e.key === 'Enter' || e.key === ' ') {
                  e.preventDefault()
                  if (file.id !== activeFileId) {
                    setActiveFileId(file.id)
                    setAnalysisResult(null)
                  }
                }
              }}
            >
              <span className="browser-tab-label" title={file.name}>
                {file.name}
              </span>
              {isProcessing && (
                <span className="browser-tab-icon" style={{ marginLeft: '6px' }}>
                  <span className="status-spinner" title="Processing..." />
                </span>
              )}
              <button
                type="button"
                className="browser-tab-close"
                title="Close tab"
                onClick={(e) => {
                  e.stopPropagation()
                  closeTab(file.id)
                }}
              >
                &times;
              </button>
            </div>
          )
        })}

        <button
          type="button"
          className="browser-tab-add"
          title="Open file tab"
          onClick={() => setModalOpen(true)}
        >
          +
        </button>
      </div>

      <AddTabModal isOpen={modalOpen} onClose={() => setModalOpen(false)} />
    </>
  )
}
