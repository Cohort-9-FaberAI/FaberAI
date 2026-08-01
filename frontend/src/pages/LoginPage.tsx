import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { motion } from 'framer-motion'
import BrandMark from '../components/layout/BrandMark'
import ModelPreview from '../components/ModelPreview/ModelPreview'
import type { AnalysisResult } from '../types/analysis'

const demoAnalysis: AnalysisResult = {
  analysis_id: 'demo',
  filename: 'faberai-sample-part.stl',
  status: 'completed',
  manufacturability_score: 87,
  summary: 'Representative inspection sample.',
  file_url: '/faberai-sample-part.stl',
  part_metadata: {
    units: 'mm',
    volume: 0,
    surface_area: 0,
    bounding_box: {
      min: { x: 0, y: 0, z: 0 },
      max: { x: 0, y: 0, z: 0 },
    },
  },
  geometry_data: {
    source_format: 'stl',
    bounding_box: {
      min: { x: 0, y: 0, z: 0 },
      max: { x: 0, y: 0, z: 0 },
    },
    volume_mm3: 0,
    surface_area_mm2: 0,
    measurements_reliable: true,
    center_mass: { x: 0, y: 0, z: 0 },
  },
  issues: [],
}

export default function LoginPage() {
  const navigate = useNavigate()
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')

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
        <div className="inspection-readout inspection-readout-a">
          <span className="readout-dot" />
          <span>draft</span>
          <strong>2.3 deg</strong>
        </div>
        <div className="inspection-readout inspection-readout-b">
          <span className="readout-dot" />
          <span>wall</span>
          <strong>1.8 mm</strong>
        </div>
        <div className="login-score">
          <strong>87</strong>
          <span>manufacturability</span>
        </div>
        <ModelPreview analysis={demoAnalysis} />
      </aside>
    </motion.div>
  )
}
