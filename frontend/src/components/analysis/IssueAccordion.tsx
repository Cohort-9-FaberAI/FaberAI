import { useState } from 'react'
import { useStore } from '../../store'
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
  const preview = items[0]?.message ?? emptyLabel ?? 'No findings in this category yet.'
  const highlightedIssue = useStore((s) => s.highlightedIssue)
  const setHighlightedIssue = useStore((s) => s.setHighlightedIssue)

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
        <ul className="issue-accordion-list">
          {items.length === 0 && emptyLabel && (
            <li className="issue-accordion-item issue-accordion-empty">
              <p>{emptyLabel}</p>
            </li>
          )}
          {items.map((item, i) => (
            <li
              key={i}
              className="issue-accordion-item"
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
