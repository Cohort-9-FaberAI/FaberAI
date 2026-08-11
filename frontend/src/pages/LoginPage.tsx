import { useEffect, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { AnimatePresence, motion, useReducedMotion } from 'framer-motion'
import BrandMark from '../components/layout/BrandMark'
import ModelPreview from '../components/ModelPreview/ModelPreview'
import { loginPreviewSamples } from '../components/landing/sampleAnalyses'

export default function LoginPage() {
  const navigate = useNavigate()
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [sampleIndex, setSampleIndex] = useState(0)
  const reduceMotion = useReducedMotion()
  const activeSample = loginPreviewSamples[sampleIndex]

  useEffect(() => {
    if (reduceMotion) return

    const interval = window.setInterval(() => {
      setSampleIndex((current) => (current + 1) % loginPreviewSamples.length)
    }, 7200)

    return () => window.clearInterval(interval)
  }, [reduceMotion])

  function handleSubmit(e: React.FormEvent) {
    e.preventDefault()
    navigate('/projects')
  }

  return (
    <motion.div
      className="login-page"
      initial={{ opacity: 0 }}
      animate={{ opacity: 1 }}
      transition={{ duration: 0.5 }}
    >
      <motion.form
        className="login-card"
        onSubmit={handleSubmit}
        initial={{ opacity: 0, y: 20, scale: 0.95 }}
        animate={{ opacity: 1, y: 0, scale: 1 }}
        transition={{ duration: 0.4, delay: 0.1 }}
      >
        <div className="login-brand">
          <BrandMark />
          <span>FaberAI</span>
        </div>
        <p className="auth-eyebrow">AI-powered manufacturability analysis</p>
        <h1>Sign in to FaberAI</h1>
        <p className="login-sub">
          Upload a CAD file and get a scored read on how it molds or prints before it reaches a shop
          floor.
        </p>
        <label className="login-field">
          <span>Username or email</span>
          <input type="text" value={email} onChange={(e) => setEmail(e.target.value)} required />
        </label>
        <label className="login-field">
          <span>Password</span>
          <input
            type="password"
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            required
          />
        </label>
        <motion.button
          className="login-submit"
          type="submit"
          whileHover={{ scale: 1.02 }}
          whileTap={{ scale: 0.98 }}
        >
          Sign in
        </motion.button>
        <div className="login-links">
          <span>Forgot password?</span>
          <span>Create account</span>
        </div>
      </motion.form>
      <aside className="login-visual" aria-label="FaberAI live inspection preview">
        <div className="login-preview-shell">
          <div className="login-preview-status">
            <i />
            Live sample analysis
          </div>

          <div className="login-model-stage" aria-live="polite">
            {loginPreviewSamples.map((sample, index) => {
              const isActive = index === sampleIndex

              return (
                <motion.div
                  className={`login-model-layer ${isActive ? 'is-active' : ''}`}
                  key={sample.id}
                  initial={false}
                  animate={{
                    opacity: isActive ? 1 : 0,
                    scale: isActive ? 1 : 0.96,
                    filter: isActive ? 'blur(0px)' : 'blur(8px)',
                  }}
                  transition={{ duration: reduceMotion ? 0 : 0.9, ease: [0.16, 1, 0.3, 1] }}
                  aria-hidden={!isActive}
                >
                  <ModelPreview
                    analysis={sample.analysis}
                    height="100%"
                    autoRotate
                    markerRadius={sample.markerRadius}
                    fitToViewport
                  />
                </motion.div>
              )
            })}
          </div>

          <AnimatePresence mode="wait" initial={false}>
            <motion.div
              className="login-preview-data"
              key={activeSample.id}
              initial={reduceMotion ? false : { opacity: 0, y: 10, filter: 'blur(6px)' }}
              animate={{ opacity: 1, y: 0, filter: 'blur(0px)' }}
              exit={reduceMotion ? undefined : { opacity: 0, y: -8, filter: 'blur(6px)' }}
              transition={{ duration: reduceMotion ? 0 : 0.42 }}
            >
              <div className="login-preview-heading">
                <span>{activeSample.process}</span>
                <strong>{activeSample.name}</strong>
              </div>

              <div className="login-preview-score">
                <span>DFM score</span>
                <strong>{activeSample.score}</strong>
                <small>/100</small>
              </div>

              {activeSample.readouts.map((readout, index) => (
                <div
                  className={`login-preview-readout login-preview-readout-${index + 1} is-${readout.tone}`}
                  key={readout.label}
                >
                  <span>{readout.label}</span>
                  <strong>{readout.value}</strong>
                  <small>{readout.detail}</small>
                </div>
              ))}
            </motion.div>
          </AnimatePresence>

          <div className="login-preview-switcher" role="tablist" aria-label="Preview sample">
            {loginPreviewSamples.map((sample, index) => (
              <button
                type="button"
                role="tab"
                aria-selected={index === sampleIndex}
                className={index === sampleIndex ? 'is-active' : ''}
                key={sample.id}
                onClick={() => setSampleIndex(index)}
              >
                <i />
                {sample.name}
              </button>
            ))}
          </div>
        </div>
      </aside>
    </motion.div>
  )
}
