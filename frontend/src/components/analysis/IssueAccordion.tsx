import { useEffect, useRef, useState } from 'react'
import { useStore } from '../../store/responsiveStore'
interface Issue {
  issue_id?: string
  message: string
  recommendation: string
}

interface IssueAccordionProps {
  title: string
  count: number
  color: string
  items: Issue[]
  emptyLabel?: string
}

export default function IssueAccordion({
  title,
  count,
  color,
  items,
  emptyLabel,
}: IssueAccordionProps) {
  const [open, setOpen] = useState(false)
  const [flashId, setFlashId] = useState<string | null>(null)
  const listRef = useRef<HTMLUListElement>(null)
  const preview = items[0]?.message ?? emptyLabel ?? 'No findings in this category yet.'
  const highlightedIssue = useStore((s) => s.highlightedIssue)
  const setHighlightedIssue = useStore((s) => s.setHighlightedIssue)
  const focusedIssueId = useStore((s) => s.focusedIssueId)
  const focusNonce = useStore((s) => s.focusNonce)

  const itemIdsKey = items
    .map((i) => i.issue_id)
    .filter(Boolean)
    .join('|')

  const hasFocusedIssue = !!focusedIssueId && itemIdsKey.split('|').includes(focusedIssueId)

  useEffect(() => {
    if (!hasFocusedIssue) return

    const raf = requestAnimationFrame(() => {
      setOpen(true)
      setFlashId(focusedIssueId)
    })

    const timer = window.setTimeout(() => setFlashId(null), 1600)
    return () => {
      cancelAnimationFrame(raf)
      window.clearTimeout(timer)
    }
  }, [hasFocusedIssue, focusedIssueId, focusNonce])

  useEffect(() => {
    if (!open || !focusedIssueId) return
    const el = listRef.current?.querySelector(
      `[data-issue-id="${CSS.escape(focusedIssueId)}"]`,
    ) as HTMLElement | null
    el?.scrollIntoView({ behavior: 'smooth', block: 'nearest' })
  }, [open, focusedIssueId, focusNonce])

  return (
    <div className={`issue-accordion${open ? ' is-open' : ''}`}>
      <button
        type="button"
        className="issue-accordion-header"
        onClick={() => setOpen(!open)}
        aria-expanded={open}
      >
        <span className="issue-accordion-dot" style={{ background: color }} />
        <span className="issue-accordion-title">{title}</span>
        <span className="issue-accordion-count">{count}</span>
        <span className="issue-accordion-chevron">&#9662;</span>
      </button>
      {!open && <p className="issue-accordion-preview">{preview}</p>}
      {open && (
        <ul ref={listRef} className="issue-accordion-list">
          {items.length === 0 && emptyLabel && (
            <li className="issue-accordion-item issue-accordion-empty">
              <p>{emptyLabel}</p>
            </li>
          )}
          {items.map((item, i) => (
            <li
              key={i}
              data-issue-id={item.issue_id ?? undefined}
              className={`issue-accordion-item${flashId === item.issue_id ? ' is-flashing' : ''}`}
              onMouseOver={() => item.issue_id && setHighlightedIssue(item.issue_id)}
              onMouseLeave={() => setHighlightedIssue(null)}
            >
              {highlightedIssue != null && highlightedIssue === item.issue_id ? (
                <strong>
                  <p className="issue-message">{item.message}</p>
                </strong>
              ) : (
                <p className="issue-message">{item.message}</p>
              )}
              <p className="issue-recommendation">{item.recommendation}</p>
            </li>
          ))}
        </ul>
      )}
    </div>
  )
}
