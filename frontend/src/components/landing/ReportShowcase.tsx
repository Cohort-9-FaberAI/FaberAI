import { useEffect, useState, type CSSProperties } from 'react'
import { LuArrowRight, LuChevronLeft, LuChevronRight, LuFileCheck2, LuX } from 'react-icons/lu'

const reportContents = [
  'Executive summary and overall score',
  '3D model views with mapped findings',
  'Molding and printing comparison',
  'Rule-level evidence and penalties',
  'Ranked findings and recommendations',
  'Supplier-ready PDF documentation',
]

const totalPages = 6

export function ReportShowcase() {
  const [isOpen, setIsOpen] = useState(false)
  const [page, setPage] = useState(0)
  const [loadedMainPage, setLoadedMainPage] = useState<number | null>(null)
  const [loadedThumbnails, setLoadedThumbnails] = useState<Record<number, boolean>>({})

  useEffect(() => {
    if (!isOpen) return

    const handleKeyDown = (event: KeyboardEvent) => {
      if (event.key === 'Escape') setIsOpen(false)
      if (event.key === 'ArrowRight') setPage((current) => Math.min(totalPages - 1, current + 1))
      if (event.key === 'ArrowLeft') setPage((current) => Math.max(0, current - 1))
    }

    window.addEventListener('keydown', handleKeyDown)
    return () => window.removeEventListener('keydown', handleKeyDown)
  }, [isOpen])

  const openReport = (nextPage = 0) => {
    setPage(nextPage)
    setIsOpen(true)
  }

  return (
    <section className="landing-report-section" id="report">
      <div className="landing-report-grid-bg" aria-hidden="true" />
      <div className="landing-wrap landing-report-grid">
        <div className="landing-report-copy reveal is-visible">
          <span className="landing-kicker landing-kicker-on-dark">The output</span>
          <h2>A report your supplier will actually read.</h2>
          <p>
            Clear, professional evidence for manufacturing decisions, with every score tied back to
            geometry and a process-specific rule.
          </p>
          <ul>
            {reportContents.map((item) => (
              <li key={item}>
                <LuFileCheck2 />
                {item}
              </li>
            ))}
          </ul>
          <button
            className="landing-button landing-button-primary"
            type="button"
            onClick={() => openReport()}
          >
            Open sample report <LuArrowRight />
          </button>
        </div>

        <div className="landing-report-visual reveal is-visible">
          <button
            className="landing-paper-stack"
            type="button"
            onClick={() => openReport()}
            aria-label="Open the six-page sample report"
          >
            {[5, 4, 3, 2, 1, 0].map((index) => (
              <span
                className="landing-paper-page"
                key={index}
                style={{ '--paper-index': index } as CSSProperties}
              >
                <img src={`/report/page-${index}.jpg`} alt={`Sample report page ${index + 1}`} />
              </span>
            ))}
          </button>
        </div>
      </div>

      {isOpen && (
        <div
          className="landing-pdf-modal"
          role="dialog"
          aria-modal="true"
          aria-label="Sample PDF report"
        >
          <button
            className="landing-pdf-backdrop"
            type="button"
            aria-label="Close report"
            onClick={() => setIsOpen(false)}
          />
          <div className="landing-pdf-modal-panel">
            <header>
              <div>
                <strong>FaberAI / sample-dfm-report.pdf</strong>
                <span>
                  Page {page + 1} of {totalPages}
                </span>
              </div>
              <button type="button" aria-label="Close report" onClick={() => setIsOpen(false)}>
                <LuX />
              </button>
            </header>
            <main>
              <button
                type="button"
                aria-label="Previous page"
                disabled={page === 0}
                onClick={() => setPage((current) => Math.max(0, current - 1))}
              >
                <LuChevronLeft />
              </button>
              <div
                className={`landing-pdf-document ${loadedMainPage === page ? 'is-loaded' : ''}`}
                aria-busy={loadedMainPage !== page}
              >
                <div className="landing-pdf-page-skeleton" aria-hidden="true">
                  <span className="landing-pdf-skeleton-brand" />
                  <span className="landing-pdf-skeleton-title" />
                  <span className="landing-pdf-skeleton-copy" />
                  <div className="landing-pdf-skeleton-fields">
                    <i />
                    <i />
                    <i />
                    <i />
                  </div>
                  <div className="landing-pdf-skeleton-preview">
                    <i />
                    <i />
                    <i />
                    <i />
                  </div>
                </div>
                <img
                  src={`/report/page-${page}.jpg`}
                  alt={`Sample report page ${page + 1}`}
                  onLoad={() => setLoadedMainPage(page)}
                  onError={() => setLoadedMainPage(page)}
                />
              </div>
              <button
                type="button"
                aria-label="Next page"
                disabled={page === totalPages - 1}
                onClick={() => setPage((current) => Math.min(totalPages - 1, current + 1))}
              >
                <LuChevronRight />
              </button>
            </main>
            <nav aria-label="Report pages">
              {Array.from({ length: totalPages }, (_, index) => (
                <button
                  type="button"
                  className={`${index === page ? 'is-active' : ''} ${loadedThumbnails[index] ? 'is-loaded' : ''}`}
                  key={index}
                  onClick={() => setPage(index)}
                  aria-label={`Open page ${index + 1}`}
                  aria-current={index === page ? 'page' : undefined}
                  aria-busy={!loadedThumbnails[index]}
                >
                  <span className="landing-pdf-thumbnail-skeleton" aria-hidden="true" />
                  <img
                    className={loadedThumbnails[index] ? 'is-loaded' : ''}
                    src={`/report/page-${index}.jpg`}
                    alt=""
                    loading="eager"
                    onLoad={() => setLoadedThumbnails((current) => ({ ...current, [index]: true }))}
                    onError={() =>
                      setLoadedThumbnails((current) => ({ ...current, [index]: true }))
                    }
                  />
                </button>
              ))}
            </nav>
          </div>
        </div>
      )}
    </section>
  )
}
