import { useState } from 'react'
import { useNavigate } from 'react-router-dom'

export default function LoginPage() {
  const navigate = useNavigate()
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')

  function handleSubmit(e: React.FormEvent) {
    e.preventDefault()
    // TODO: wire to real auth once login flow is confirmed with backend
    navigate('/home')
  }

  return (
    <div className="login-page">
      <form className="login-card" onSubmit={handleSubmit}>
        <h1>FaberAI</h1>
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
        <button className="login-submit" type="submit">
          Login
        </button>
        <div className="login-links">
          <span>Forgot Password?</span>
          <span>Haven't made an account? Register</span>
        </div>
      </form>
    </div>
  )
}
