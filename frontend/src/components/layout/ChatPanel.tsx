import { useState } from 'react'
import { useLocation } from 'react-router-dom'
import { motion, AnimatePresence } from 'framer-motion'
import { useStore } from '../../store'
import { askAI } from '../../lib/api'
import { getPageQuestions } from './chatPresets'

export default function ChatPanel() {
  const isOpen = useStore((s) => s.isOpen)
  const setOpen = useStore((s) => s.setOpen)
  const messages = useStore((s) => s.messages)
  const addMessage = useStore((s) => s.addMessage)
  const analysisResult = useStore((s) => s.analysisResult)
  const files = useStore((s) => s.files)

  const location = useLocation()
  const [input, setInput] = useState('')
  const [sending, setSending] = useState(false)

  const latestFile = files[files.length - 1]
  const analysisId =
    (analysisResult?.analysis_id as string | undefined) ?? latestFile?.analysisId ?? null

  async function sendQuestion(question: string) {
    const trimmed = question.trim()
    if (!trimmed || sending) return

    addMessage({ id: crypto.randomUUID(), role: 'user', text: trimmed })
    setInput('')

    if (!analysisId) {
      // /ai/ask requires either analysis_id or an inline DFMReport (from
      // /dfm/evaluate) — the frontend never has the latter shape on hand, so
      // without a persisted analysis_id there is nothing valid to send.
      addMessage({
        id: crypto.randomUUID(),
        role: 'assistant',
        text: 'Run an analysis first — I can only answer questions about a finished report.',
      })
      return
    }

    setSending(true)

    try {
      const result = await askAI({
        question: trimmed,
        analysis_id: analysisId,
      })
      addMessage({
        id: crypto.randomUUID(),
        role: 'assistant',
        text: result.answer,
        mode: result.mode,
        referencedRules: result.referenced_rules,
        degradedReason: result.degraded_reason,
      })
    } catch (err) {
      addMessage({
        id: crypto.randomUUID(),
        role: 'assistant',
        text: err instanceof Error ? err.message : 'Something went wrong. Please try again.',
      })
    } finally {
      setSending(false)
    }
  }

  function handleSubmit(e: React.FormEvent) {
    e.preventDefault()
    sendQuestion(input)
  }

  const presetQuestions = getPageQuestions(location.pathname)

  return (
    <AnimatePresence>
      {isOpen && (
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
            transition={{ type: 'tween', duration: 0.3, ease: 'easeOut' }}
          >
            <div className="chat-header">
              <h2>Ask Faber AI</h2>
              <button className="chat-close-btn" type="button" onClick={() => setOpen(false)}>
                &times;
              </button>
            </div>

            <div className="chat-body">
              {messages.length === 0 && (
                <p className="chat-empty">
                  {analysisId
                    ? 'Ask a question about this analysis.'
                    : 'Run an analysis first to ask questions about it.'}
                </p>
              )}

              {messages.map((m) => (
                <div key={m.id} className={`chat-message chat-message-${m.role}`}>
                  {m.mode && (
                    <span className={`chat-mode-badge chat-mode-badge-${m.mode}`}>
                      {m.mode === 'llm' ? 'AI-generated' : 'Deterministic'}
                    </span>
                  )}
                  <p>{m.text}</p>
                  {!!m.referencedRules?.length && (
                    <p className="chat-message-rules">Based on: {m.referencedRules.join(', ')}</p>
                  )}
                  {m.degradedReason && (
                    <p className="chat-message-note">Note: {m.degradedReason}</p>
                  )}
                </div>
              ))}

              {sending && <p className="chat-message chat-message-assistant chat-typing">…</p>}
            </div>

            {presetQuestions.length > 0 && (
              <div className="chat-presets">
                {presetQuestions.map((q) => (
                  <button
                    key={q}
                    type="button"
                    className="chat-preset-chip"
                    onClick={() => sendQuestion(q)}
                    disabled={sending}
                  >
                    {q}
                  </button>
                ))}
              </div>
            )}

            <form className="chat-input-row" onSubmit={handleSubmit}>
              <input
                type="text"
                value={input}
                onChange={(e) => setInput(e.target.value)}
                placeholder="Ask a question..."
                disabled={sending}
              />
              <button type="submit" disabled={sending || !input.trim()}>
                Send
              </button>
            </form>
          </motion.aside>
        </>
      )}
    </AnimatePresence>
  )
}
