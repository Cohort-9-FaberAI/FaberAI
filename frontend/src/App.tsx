import { useEffect } from 'react'
import { Routes, Route, Navigate } from 'react-router-dom'
import { useStore } from './store'
import { applyAccentHue } from './lib/theme'
import LoginPage from './pages/LoginPage'
import HomePage from './pages/HomePage'
import AnalysisPage from './pages/AnalysisPage'
import ProjectsPage from './pages/ProjectsPage'
import ProjectDetailPage from './pages/ProjectDetailPage'
import DebugApiPage from './pages/DebugApiPage'
import LandingPage from './pages/LandingPage'
import SettingsPage from './pages/SettingsPage'

function App() {
  const theme = useStore((s) => s.theme)
  const accentHue = useStore((s) => s.accentHue)

  useEffect(() => {
    document.documentElement.setAttribute('data-theme', theme)
  }, [theme])

  useEffect(() => {
    applyAccentHue(accentHue)
  }, [accentHue])

  return (
    <Routes>
      <Route path="/landing" element={<LandingPage />} />
      <Route path="/login" element={<LoginPage />} />
      <Route path="/home" element={<HomePage />} />
      <Route path="/analysis" element={<AnalysisPage />} />
      <Route path="/projects" element={<ProjectsPage />} />
      <Route path="/projects/:id" element={<ProjectDetailPage />} />
      <Route path="/settings" element={<SettingsPage />} />
      <Route path="/debug" element={<DebugApiPage />} />
      <Route path="*" element={<Navigate to="/landing" replace />} />
    </Routes>
  )
}

export default App
