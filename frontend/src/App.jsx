import { BrowserRouter, Route, Routes } from 'react-router-dom'
import AppLayout from './components/AppLayout'
import { GuestRoute, ProtectedRoute } from './components/ProtectedRoute'
import { AuthProvider } from './context/AuthContext'
import Landing from './pages/Landing'
import { Login, Signup } from './pages/Auth'
import NotFound from './pages/NotFound'
import Dashboard from './pages/app/Dashboard'
import GitHub from './pages/app/GitHub'
import GitHubCallback from './pages/app/GitHubCallback'
import Repos from './pages/app/Repos'
import RepoDetail from './pages/app/RepoDetail'
import Settings from './pages/app/Settings'

export default function App() {
  return (
    <AuthProvider>
      <BrowserRouter>
        <Routes>
          <Route path="/" element={<Landing />} />
          <Route element={<GuestRoute />}>
            <Route path="/login" element={<Login />} />
            <Route path="/signup" element={<Signup />} />
          </Route>
          <Route element={<ProtectedRoute />}>
            <Route path="/app" element={<AppLayout />}>
              <Route index element={<Dashboard />} />
              <Route path="repos" element={<Repos />} />
              <Route path="repos/:id" element={<RepoDetail />} />
              <Route path="github" element={<GitHub />} />
              <Route path="github/callback" element={<GitHubCallback />} />
              <Route path="settings" element={<Settings />} />
            </Route>
          </Route>
          <Route path="*" element={<NotFound />} />
        </Routes>
      </BrowserRouter>
    </AuthProvider>
  )
}
