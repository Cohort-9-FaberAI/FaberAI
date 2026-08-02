import { useEffect } from 'react'
import { Routes, Route, Navigate } from 'react-router-dom'
import { useStore } from './store'
import LoginPage from './pages/LoginPage'
import HomePage from './pages/HomePage'
import AnalysisPage from './pages/AnalysisPage'
import UploadPage from './pages/UploadPage'
import ProjectsPage from './pages/ProjectsPage'
import ProjectDetailPage from './pages/ProjectDetailPage'
import LibraryPage from './pages/LibraryPage'
import HistoryPage from './pages/HistoryPage'
import DebugApiPage from './pages/DebugApiPage'
import LandingPage from './pages/LandingPage'

function App() {
  const theme = useStore((s) => s.theme)

  useEffect(() => {
    document.documentElement.setAttribute('data-theme', theme)
  }, [theme])

  return (
    <Routes>
      <Route path="/landing" element={<LandingPage />} />
      <Route path="/login" element={<LoginPage />} />
      <Route path="/home" element={<HomePage />} />
      <Route path="/upload" element={<UploadPage />} />
      <Route path="/extra-info" element={<Navigate to="/analysis" replace />} />
      <Route path="/analysis" element={<AnalysisPage />} />
      <Route path="/conclusion" element={<Navigate to="/analysis" replace />} />
      <Route path="/download" element={<Navigate to="/analysis" replace />} />
      <Route path="/projects" element={<ProjectsPage />} />
      <Route path="/projects/:id" element={<ProjectDetailPage />} />
      <Route path="/library" element={<LibraryPage />} />
      <Route path="/history" element={<HistoryPage />} />
      <Route path="/debug" element={<DebugApiPage />} />
      <Route path="*" element={<Navigate to="/landing" replace />} />
    </Routes>
  )
}

export default App
