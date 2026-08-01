import { useNavigate } from 'react-router-dom'
import { useStore } from '../../store'

interface AddTabModalProps {
  isOpen: boolean
  onClose: () => void
}

export default function AddTabModal({ isOpen, onClose }: AddTabModalProps) {
  const navigate = useNavigate()
  const files = useStore((s) => s.files)
  const openTab = useStore((s) => s.openTab)
  const openTabIds = useStore((s) => s.openTabIds)
  const setAnalysisResult = useStore((s) => s.setAnalysisResult)
  const activeFileId = useStore((s) => s.activeFileId)

  if (!isOpen) return null

  const sessionFiles = files.filter((f) => f.taskId !== 'dev-manual')

  return (
    <div className="workspace-modal-overlay" onClick={onClose}>
      <div className="workspace-modal-card" onClick={(e) => e.stopPropagation()}>
        <div className="workspace-modal-header">
          <h2>Select CAD File to Open</h2>
          <button
            type="button"
            className="workspace-modal-close"
            onClick={onClose}
            aria-label="Close modal"
          >
            &times;
          </button>
        </div>

        <div className="workspace-modal-body">
          <section>
            <span className="modal-section-title">Current Session Uploads</span>
            {sessionFiles.length > 0 ? (
              <div className="modal-file-list">
                {sessionFiles.map((file) => {
                  const isAlreadyOpen = openTabIds.includes(file.id)
                  return (
                    <button
                      key={file.id}
                      type="button"
                      disabled={isAlreadyOpen}
                      title={
                        isAlreadyOpen
                          ? 'This CAD file is already open in a workspace tab'
                          : undefined
                      }
                      className={`modal-file-item${isAlreadyOpen ? ' disabled-open' : ''}`}
                      onClick={() => {
                        if (isAlreadyOpen) return
                        if (file.id !== activeFileId) {
                          setAnalysisResult(null)
                        }
                        openTab(file.id)
                        onClose()
                      }}
                    >
                      <span className="modal-file-name">{file.name}</span>
                      <span
                        className={`modal-file-status ${isAlreadyOpen ? 'already-open' : file.status}`}
                      >
                        {isAlreadyOpen ? 'ALREADY OPEN' : file.status.toUpperCase()}
                      </span>
                    </button>
                  )
                })}
              </div>
            ) : (
              <p className="modal-empty-text">No CAD files have been uploaded in this session.</p>
            )}
          </section>

          <section>
            <span className="modal-section-title">Previous Uploads</span>
            <p className="modal-empty-text">No previous files found in account history.</p>
          </section>
        </div>

        <div
          className="workspace-modal-footer"
          style={{
            marginTop: '24px',
            paddingTop: '20px',
            borderTop: '1px solid var(--line, #233027)',
            display: 'flex',
            justifyContent: 'flex-end',
            alignItems: 'center',
            gap: '12px',
          }}
        >
          <span style={{ fontSize: '13px', color: 'var(--text-secondary)', marginRight: 'auto' }}>
            Need to analyze another part?
          </span>
          <button
            type="button"
            className="workspace-empty-btn"
            style={{ padding: '9px 18px', fontSize: '14px' }}
            onClick={() => {
              onClose()
              navigate('/home')
            }}
          >
            + Upload New CAD File
          </button>
        </div>
      </div>
    </div>
  )
}
