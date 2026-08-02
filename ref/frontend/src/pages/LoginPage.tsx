import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { motion } from 'framer-motion'

export default function LoginPage() {
  const navigate = useNavigate()
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')

  function handleSubmit(e: React.FormEvent) {
    e.preventDefault()
    navigate('/home')
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
        <h1>FaberAI</h1>
        <p style={{ color: 'var(--text-muted)', fontSize: 14, margin: 0 }}>
          AI-powered manufacturability analysis
        </p>
        <label className="login-field">
          <span>Username or Email</span>
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
          Login
        </motion.button>
        <div className="login-links">
          <span>Forgot Password?</span>
          <span>Haven't made an account? Register</span>
        </div>
      </motion.form>
    </motion.div>
  )
}
