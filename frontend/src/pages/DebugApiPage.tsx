import { useState, useRef } from 'react'
import {
  getHealthCheck,
  uploadFile,
  getTaskStatus,
  getMockAnalysis,
  createAnalysis,
} from '../lib/api'

interface EndpointResult {
  status: number | null
  ms: number | null
  body: unknown
  error: string | null
}

type Results = Record<string, EndpointResult>

function EndpointCard({
  name,
  method,
  result,
  onRun,
  loading,
  children,
}: {
  name: string
  method: string
  result: EndpointResult | null
  onRun: () => void
  loading: boolean
  children?: React.ReactNode
}) {
  const pass = result && !result.error && result.status !== null

  return (
    <div className="debug-card">
      <div className="debug-card-header">
        <span className="debug-method">{method}</span>
        <span className="debug-endpoint-name">{name}</span>
        {result && (
          <span className={`debug-badge ${pass ? 'pass' : 'fail'}`}>{pass ? 'PASS' : 'FAIL'}</span>
        )}
      </div>

      <div className="debug-card-controls">
        <button type="button" onClick={onRun} disabled={loading}>
          {loading ? 'Running...' : 'Run'}
        </button>
        {children}
      </div>

      {result && (
        <div className="debug-card-result">
          {result.status !== null && (
            <div className="debug-meta">
              <span>Status: {result.status}</span>
              {result.ms !== null && <span>{result.ms}ms</span>}
            </div>
          )}
          {result.error && <pre className="debug-json debug-error">{result.error}</pre>}
          {result.body != null && (
            <pre className="debug-json">{JSON.stringify(result.body, null, 2)}</pre>
          )}
        </div>
      )}
    </div>
  )
}

export default function DebugApiPage() {
  const [results, setResults] = useState<Results>({})
  const [loading, setLoading] = useState<string | null>(null)
  const [taskId, setTaskId] = useState('')
  const [uploadFile_, setUploadFile] = useState<File | null>(null)
  const fileRef = useRef<HTMLInputElement>(null)

  async function run(name: string, fn: () => Promise<unknown>) {
    setLoading(name)
    const start = performance.now()
    try {
      const body = await fn()
      setResults((prev) => ({
        ...prev,
        [name]: {
          status: 200,
          ms: Math.round(performance.now() - start),
          body,
          error: null,
        },
      }))
    } catch (err) {
      setResults((prev) => ({
        ...prev,
        [name]: {
          status: null,
          ms: Math.round(performance.now() - start),
          body: null,
          error: err instanceof Error ? err.message : String(err),
        },
      }))
    } finally {
      setLoading(null)
    }
  }

  async function handleUpload() {
    const file = uploadFile_
    if (!file) return
    await run('upload', async () => {
      const res = await uploadFile(file)
      setTaskId(res.task_id)
      return res
    })
  }

  return (
    <div className="debug-page">
      <h1>API Debug</h1>
      <p className="debug-subtitle">
        Verify all 5 backend endpoints are live and returning correct shapes.
      </p>

      <EndpointCard
        name="/"
        method="GET"
        result={results['health'] ?? null}
        onRun={() => run('health', getHealthCheck)}
        loading={loading === 'health'}
      />

      <EndpointCard
        name="/upload/"
        method="POST"
        result={results['upload'] ?? null}
        onRun={handleUpload}
        loading={loading === 'upload'}
      >
        <input
          ref={fileRef}
          type="file"
          accept=".step,.stp,.stl"
          className="debug-file-input"
          onChange={(e) => setUploadFile(e.target.files?.[0] ?? null)}
        />
        {uploadFile_ && <span className="debug-file-name">{uploadFile_.name}</span>}
      </EndpointCard>

      <EndpointCard
        name="/tasks/{task_id}"
        method="GET"
        result={results['task'] ?? null}
        onRun={() => {
          if (taskId) run('task', () => getTaskStatus(taskId))
        }}
        loading={loading === 'task'}
      >
        <input
          className="debug-task-input"
          type="text"
          placeholder="task_id (auto-filled after upload)"
          value={taskId}
          onChange={(e) => setTaskId(e.target.value)}
        />
      </EndpointCard>

      <EndpointCard
        name="/analyze-mock"
        method="POST"
        result={results['mock'] ?? null}
        onRun={() => run('mock', getMockAnalysis)}
        loading={loading === 'mock'}
      />

      <EndpointCard
        name="/analysis/"
        method="POST"
        result={results['analysis'] ?? null}
        onRun={() =>
          run('analysis', () =>
            createAnalysis({
              filename: 'debug-test.stl',
              status: 'completed',
              manufacturability_score: 90,
              summary: 'Test analysis from debug page.',
              issues: [],
            }),
          )
        }
        loading={loading === 'analysis'}
      />
    </div>
  )
}
