import { useState } from 'react'
import SearchBar from '../components/common/SearchBar'
import ListRow from '../components/common/ListRow'
import { useStore } from '../store'

export default function HistoryPage() {
  const entries = useStore((s) => s.historyEntries)
  const [query, setQuery] = useState('')

  const filtered = entries.filter(
    (e) =>
      e.fileName.toLowerCase().includes(query.toLowerCase()) ||
      e.diagnosis.toLowerCase().includes(query.toLowerCase()),
  )

  return (
    <>
      <section className="history-header">
        <h1>History</h1>
        <p className="page-note">
          Diagnosis inside history will be deleted at the end of every month.
        </p>
      </section>

      <SearchBar value={query} onChange={setQuery} />

      <div className="list-container">
        {filtered.map((e) => (
          <ListRow
            key={e.id}
            fields={[
              { label: 'File Name', value: e.fileName },
              { label: 'Diagnosis', value: e.diagnosis },
              { label: 'Date', value: e.date },
            ]}
            actions={[]}
          />
        ))}
        {filtered.length === 0 && <p className="list-empty">No history entries found.</p>}
      </div>
    </>
  )
}
