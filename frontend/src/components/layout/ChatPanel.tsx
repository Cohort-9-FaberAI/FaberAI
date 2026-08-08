import { type FormEvent, type ReactNode, useEffect, useRef, useState } from 'react'
import { useLocation } from 'react-router-dom'
import { motion, AnimatePresence } from 'framer-motion'
import { askFaberAI } from '../../lib/api'
import { useStore } from '../../store'
import BrandMark from './BrandMark'
import { getPageQuestions, isChatEnabledForRoute } from './chatPresets'

type ChatRole = 'assistant' | 'user'

interface ChatMessage {
  id: string
  role: ChatRole
  content: string
  referencedRules?: string[]
  mode?: 'llm' | 'deterministic'
  degradedReason?: string | null
}

const SUGGESTED_QUESTIONS = [
  'Why is this part not manufacturable?',
  'Which rules failed?',
  'How can I improve the design?',
  'Which manufacturing process is preferred?',
]

const EMPTY_GREETING: ChatMessage = {
  id: 'initial-empty',
  role: 'assistant',
  content:
    'Upload and complete an analysis first. Once a DFM report is ready, I can explain the verdict, failed rules, score, and recommended fixes.',
}

const READY_GREETING: ChatMessage = {
  id: 'initial-ready',
  role: 'assistant',
  content:
    'I can answer from the completed DFM report. Ask about failed rules, score impact, process choice, or specific design changes.',
}

function newId(prefix: string) {
  if (typeof crypto !== 'undefined' && 'randomUUID' in crypto) {
    return `${prefix}-${crypto.randomUUID()}`
  }
  return `${prefix}-${Date.now()}-${Math.random().toString(16).slice(2)}`
}

function getRecord(value: unknown): Record<string, unknown> | null {
  return value && typeof value === 'object' && !Array.isArray(value)
    ? (value as Record<string, unknown>)
    : null
}

function getString(value: unknown): string | null {
  return typeof value === 'string' && value.trim() ? value : null
}

function getChatStorageKey(analysisId: string | null) {
  return `faberai_chat_${analysisId ?? 'no-analysis'}`
}

function formatMessage(content: string) {
  return content
    .split('\n')
    .map((line) => line.replace(/\t/g, '  ').trimEnd())
    .filter((line, index, lines) => line || index < lines.length - 1)
}

function renderInline(text: string, keyPrefix: string) {
  const tokens: ReactNode[] = []
  const pattern = /(\*\*([^*]+)\*\*|`([^`]+)`|_([^_\n]+)_)/g
  let cursor = 0
  let match: RegExpExecArray | null
  let index = 0

  while ((match = pattern.exec(text)) !== null) {
    if (match.index > cursor) {
      tokens.push(<span key={`${keyPrefix}-${index++}`}>{text.slice(cursor, match.index)}</span>)
    }
    if (match[2]) {
      tokens.push(<strong key={`${keyPrefix}-${index++}`}>{match[2]}</strong>)
    } else if (match[3]) {
      tokens.push(<code key={`${keyPrefix}-${index++}`}>{match[3]}</code>)
    } else if (match[4]) {
      tokens.push(<em key={`${keyPrefix}-${index++}`}>{match[4]}</em>)
    }
    cursor = match.index + match[0].length
  }

  if (cursor < text.length) {
    tokens.push(<span key={`${keyPrefix}-${index}`}>{text.slice(cursor)}</span>)
  }

  return tokens.length ? tokens : text
}

function renderLine(line: string, keyPrefix: string) {
  const trimmed = line.trim()
  const bullet = trimmed.match(/^[-*]\s+(.*)$/)
  if (bullet) {
    return (
      <li key={keyPrefix} className="chat-list-item">
        {renderInline(bullet[1], keyPrefix)}
      </li>
    )
  }

  return <p key={keyPrefix}>{renderInline(trimmed, keyPrefix)}</p>
}

function ChatBubble({ message }: { message: ChatMessage }) {
  const isAssistant = message.role === 'assistant'
  const lines = formatMessage(message.content)
  const renderedLines: ReactNode[] = []
  let listItems: ReactNode[] = []

  lines.forEach((line, index) => {
    const key = `${message.id}-${index}`
    const isBullet = /^[-*]\s+/.test(line.trim())
    if (isBullet) {
      listItems.push(renderLine(line, key))
      return
    }
    if (listItems.length) {
      renderedLines.push(<ul key={`${key}-list`}>{listItems}</ul>)
      listItems = []
    }
    renderedLines.push(renderLine(line, key))
  })
  if (listItems.length) {
    renderedLines.push(<ul key={`${message.id}-list-end`}>{listItems}</ul>)
  }

  return (
    <motion.div
      className={`chat-message-row ${isAssistant ? 'assistant' : 'user'}`}
      initial={{ opacity: 0, y: 8 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.18, ease: 'easeOut' }}
    >
      <div className="chat-avatar" aria-hidden="true">
        {isAssistant ? <BrandMark size={20} /> : 'You'}
      </div>
      <div className="chat-message-stack">
        <div className="chat-message-bubble">
          {lines.length > 0 ? (
            renderedLines
          ) : (
            <div className="chat-typing" aria-label="Faber AI is thinking">
              <span />
              <span />
              <span />
            </div>
          )}
        </div>
        {isAssistant && (message.referencedRules?.length || message.mode) ? (
          <div className="chat-message-meta">
            {message.referencedRules?.length ? (
              <span>Rules: {message.referencedRules.join(', ')}</span>
            ) : null}
            {message.mode ? (
              <span>{message.mode === 'llm' ? 'Generated' : 'Report fallback'}</span>
            ) : null}
          </div>
        ) : null}
        {message.degradedReason ? (
          <div className="chat-warning">Model unavailable: {message.degradedReason}</div>
        ) : null}
      </div>
    </motion.div>
  )
}

export default function ChatPanel() {
  const isOpen = useStore((s) => s.isOpen)
  const setOpen = useStore((s) => s.setOpen)
  const location = useLocation()
  const chatEnabled = isChatEnabledForRoute(location.pathname)
  const files = useStore((s) => s.files)
  const activeFileId = useStore((s) => s.activeFileId)
  const latestFile = files.find((f) => f.id === activeFileId) ?? files[files.length - 1]
  const activeId = latestFile?.id ?? ''
  const analysisResult = useStore((s) => s.analysisResults[activeId] ?? null)

  const analysis = getRecord(analysisResult)
  const report = getRecord(analysis?.dfm_report)
  const geometry = getRecord(analysis?.geometry_data)
  const analysisStatus = getString(analysis?.status)
  const analysisId = getString(analysis?.analysis_id) ?? latestFile?.analysisId ?? null
  const hasCompletedReport = Boolean(
    report ||
    (analysisId && (analysisStatus === 'completed' || latestFile?.status === 'completed')),
  )
  const storageKey = getChatStorageKey(analysisId)

  const [messages, setMessages] = useState<ChatMessage[]>(() => [EMPTY_GREETING])
  const [input, setInput] = useState('')
  const [isSending, setIsSending] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const scrollRef = useRef<HTMLDivElement>(null)
  const inputRef = useRef<HTMLTextAreaElement>(null)

  useEffect(() => {
    const fallback = hasCompletedReport ? READY_GREETING : EMPTY_GREETING
    const saved = localStorage.getItem(storageKey)
    let nextMessages = [fallback]

    if (!saved) {
      queueMicrotask(() => setMessages(nextMessages))
      return
    }

    try {
      const parsed = JSON.parse(saved) as ChatMessage[]
      nextMessages = Array.isArray(parsed) && parsed.length ? parsed : [fallback]
    } catch {
      nextMessages = [fallback]
    }
    queueMicrotask(() => setMessages(nextMessages))
  }, [hasCompletedReport, storageKey])

  useEffect(() => {
    localStorage.setItem(storageKey, JSON.stringify(messages))
  }, [messages, storageKey])

  useEffect(() => {
    const node = scrollRef.current
    if (!node) return
    node.scrollTo({ top: node.scrollHeight, behavior: 'smooth' })
  }, [messages, isSending])

  // Chat is only offered on the analysis workspace — force it closed if the
  // user navigates away while it's open, rather than leaving it open behind
  // a hidden panel.
  useEffect(() => {
    if (!chatEnabled && isOpen) setOpen(false)
  }, [chatEnabled, isOpen, setOpen])

  const sendMessage = async (eventOrText?: FormEvent | string) => {
    if (typeof eventOrText !== 'string') eventOrText?.preventDefault()
    const question = typeof eventOrText === 'string' ? eventOrText : input
    const trimmed = question.trim()
    if (!trimmed || isSending || !hasCompletedReport) return

    setInput('')
    setError(null)

    const userMessage: ChatMessage = {
      id: newId('user'),
      role: 'user',
      content: trimmed,
    }
    const pendingMessage: ChatMessage = {
      id: newId('assistant'),
      role: 'assistant',
      content: '',
    }

    setMessages((current) => [...current, userMessage, pendingMessage])
    setIsSending(true)

    try {
      const response = await askFaberAI({
        question: trimmed,
        ...(report ? { report } : { analysis_id: analysisId ?? undefined }),
        ...(geometry ? { geometry } : {}),
      })

      setMessages((current) =>
        current.map((message) =>
          message.id === pendingMessage.id
            ? {
                ...message,
                content: response.answer,
                referencedRules: response.referenced_rules,
                mode: response.mode,
                degradedReason: response.degraded_reason,
              }
            : message,
        ),
      )
    } catch (err) {
      const message = err instanceof Error ? err.message : 'Faber AI could not answer right now.'
      setError(message)
      setMessages((current) =>
        current.map((item) =>
          item.id === pendingMessage.id
            ? {
                ...item,
                content: message,
              }
            : item,
        ),
      )
    } finally {
      setIsSending(false)
    }
  }

  const resetChat = () => {
    const fallback = hasCompletedReport ? READY_GREETING : EMPTY_GREETING
    setMessages([{ ...fallback, id: newId('initial') }])
    setError(null)
  }

  return (
    <AnimatePresence>
      {isOpen && chatEnabled && (
        <>
          <motion.div
            className="chat-overlay"
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            onClick={() => setOpen(false)}
          />
          <motion.aside
            className="chat-panel"
            initial={{ x: '100%' }}
            animate={{ x: 0 }}
            exit={{ x: '100%' }}
            transition={{ type: 'tween', duration: 0.24, ease: 'easeOut' }}
            aria-label="Ask Faber AI"
          >
            <div className="chat-header">
              <div>
                <h2>Ask Faber AI</h2>
                <p>
                  {hasCompletedReport
                    ? `Bound to ${analysisId ? `analysis ${analysisId.slice(0, 8)}` : 'this report'}`
                    : 'Waiting for a completed DFM report'}
                </p>
              </div>
              <div className="chat-header-actions">
                <button className="chat-reset-btn" type="button" onClick={resetChat}>
                  Reset
                </button>
                <button className="chat-close-btn" type="button" onClick={() => setOpen(false)}>
                  Close
                </button>
              </div>
            </div>

            <div className="chat-body" ref={scrollRef}>
              {messages.map((message) => (
                <ChatBubble key={message.id} message={message} />
              ))}
            </div>

            <div className="chat-composer">
              <div className="chat-suggestions" aria-label="Suggested questions">
                {Array.from(
                  new Set([
                    ...getPageQuestions(location.pathname),
                    ...(hasCompletedReport ? SUGGESTED_QUESTIONS : []),
                  ]),
                ).map((question) => (
                  <button
                    key={question}
                    type="button"
                    onClick={() => sendMessage(question)}
                    disabled={isSending}
                  >
                    {question}
                  </button>
                ))}
              </div>

              {error ? <p className="chat-error">{error}</p> : null}

              <form className="chat-input-row" onSubmit={sendMessage}>
                <textarea
                  ref={inputRef}
                  value={input}
                  onChange={(event) => setInput(event.target.value)}
                  onKeyDown={(event) => {
                    if (event.key === 'Enter' && !event.shiftKey) {
                      event.preventDefault()
                      void sendMessage()
                    }
                  }}
                  placeholder={
                    hasCompletedReport
                      ? 'Ask about rules, score, process choice, or fixes...'
                      : 'Ask a question or select a suggestion above...'
                  }
                  disabled={isSending}
                  rows={2}
                />
                <button type="submit" disabled={isSending || !input.trim()}>
                  {isSending ? 'Sending' : 'Send'}
                </button>
              </form>
            </div>
          </motion.aside>
        </>
      )}
    </AnimatePresence>
  )
}
