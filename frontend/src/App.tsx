import { Routes, Route, Navigate } from 'react-router-dom'
import LoginPage from './pages/LoginPage'
import UploadPage from './pages/UploadPage'
import ExtraInfoPage from './pages/ExtraInfoPage'
import ConclusionPage from './pages/ConclusionPage'
import DownloadPage from './pages/DownloadPage'
import ProjectsPage from './pages/ProjectsPage'
import ProjectDetailPage from './pages/ProjectDetailPage'
import LibraryPage from './pages/LibraryPage'
import HistoryPage from './pages/HistoryPage'
import DebugApiPage from './pages/DebugApiPage'

function App() {
  return (
    <Routes>
      <Route path="/login" element={<LoginPage />} />
      <Route path="/upload" element={<UploadPage />} />
      <Route path="/extra-info" element={<ExtraInfoPage />} />
      <Route path="/conclusion" element={<ConclusionPage />} />
      <Route path="/download" element={<DownloadPage />} />
      <Route path="/projects" element={<ProjectsPage />} />
      <Route path="/projects/:id" element={<ProjectDetailPage />} />
      <Route path="/library" element={<LibraryPage />} />
      <Route path="/history" element={<HistoryPage />} />
      <Route path="/debug" element={<DebugApiPage />} />
      <Route path="*" element={<Navigate to="/login" replace />} />
    </Routes>
  )
}

export default App
