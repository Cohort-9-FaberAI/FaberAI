import { useEffect } from 'react'
import { Routes, Route, Navigate } from 'react-router-dom'
import { useStore } from './store'
import LoginPage from './pages/LoginPage'
import HomePage from './pages/HomePage'
import AnalysisPage from './pages/AnalysisPage'
import ProjectsPage from './pages/ProjectsPage'
import LibraryPage from './pages/LibraryPage'
import HistoryPage from './pages/HistoryPage'
import DebugApiPage from './pages/DebugApiPage'

function App() {
  const theme = useStore((s) => s.theme)

  useEffect(() => {
    document.documentElement.setAttribute('data-theme', theme)
  }, [theme])

  return (
    <Routes>
      <Route path="/login" element={<LoginPage />} />
      <Route path="/home" element={<HomePage />} />
      <Route path="/extra-info" element={<Navigate to="/analysis" replace />} />
      <Route path="/analysis" element={<AnalysisPage />} />
      <Route path="/conclusion" element={<Navigate to="/analysis" replace />} />
      <Route path="/download" element={<Navigate to="/analysis" replace />} />
      <Route path="/projects" element={<ProjectsPage />} />
      <Route path="/library" element={<LibraryPage />} />
      <Route path="/history" element={<HistoryPage />} />
      <Route path="/debug" element={<DebugApiPage />} />
      <Route path="*" element={<Navigate to="/login" replace />} />
    </Routes>
  )
}

export default App
