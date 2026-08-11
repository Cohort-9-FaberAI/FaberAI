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
import AppShell from './components/layout/AppShell'
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
      <Route element={<AppShell />}>
        <Route path="/home" element={<HomePage />} />
        <Route path="/upload" element={<Navigate to="/home" replace />} />
        <Route path="/extra-info" element={<Navigate to="/analysis" replace />} />
        <Route path="/analysis" element={<AnalysisPage />} />
        <Route path="/conclusion" element={<Navigate to="/analysis" replace />} />
        <Route path="/download" element={<Navigate to="/analysis" replace />} />
        <Route path="/projects" element={<ProjectsPage />} />
        <Route path="/projects/:id" element={<ProjectDetailPage />} />
        <Route path="/settings" element={<SettingsPage />} />
        <Route path="/library" element={<Navigate to="/projects" replace />} />
        <Route path="/history" element={<Navigate to="/projects" replace />} />
        <Route path="/debug" element={<DebugApiPage />} />
      </Route>
      <Route path="*" element={<Navigate to="/landing" replace />} />
    </Routes>
  )
}

export default App
