import { useStore } from '../../store'
import { motion, AnimatePresence } from 'framer-motion'

export default function ChatPanel() {
  const isOpen = useStore((s) => s.isOpen)
  const setOpen = useStore((s) => s.setOpen)

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
              <p>Chat will be available soon.</p>
            </div>
          </motion.aside>
        </>
      )}
    </AnimatePresence>
  )
}
