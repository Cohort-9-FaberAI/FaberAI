import { useState } from 'react'

interface Issue {
  message: string
  recommendation: string
}

interface IssueAccordionProps {
  title: string
  count: number
  color: string
  items: Issue[]
}

export default function IssueAccordion({ title, count, color, items }: IssueAccordionProps) {
  const [open, setOpen] = useState(false)

  return (
    <div className="issue-accordion">
      <button type="button" className="issue-accordion-header" onClick={() => setOpen(!open)}>
        <span className="issue-accordion-dot" style={{ background: color }} />
        <span className="issue-accordion-title">{title}</span>
        <span className="issue-accordion-count">{count}</span>
        <span className="issue-accordion-chevron">{open ? '▲' : '▼'}</span>
      </button>
      {open && (
        <ul className="issue-accordion-list">
          {items.map((item, i) => (
            <li key={i} className="issue-accordion-item">
              <p className="issue-message">{item.message}</p>
              <p className="issue-recommendation">{item.recommendation}</p>
            </li>
          ))}
        </ul>
      )}
    </div>
  )
}
