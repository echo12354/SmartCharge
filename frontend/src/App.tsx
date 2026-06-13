import { Navigate, Route, Routes } from 'react-router-dom'
import { AuthProvider, useAuth } from './contexts/AuthContext'
import Layout from './components/Layout'
import LoginPage from './pages/LoginPage'
import RegisterPage from './pages/RegisterPage'
import UserHome from './pages/user/UserHome'
import BillsPage from './pages/user/BillsPage'
import AdminHome from './pages/admin/AdminHome'
import PilesPage from './pages/admin/PilesPage'
import QueuePage from './pages/admin/QueuePage'
import MonitorPage from './pages/admin/MonitorPage'
import AcceptancePage from './pages/admin/AcceptancePage'
import ReportsPage from './pages/admin/ReportsPage'

function ProtectedRoute({
  children,
  adminOnly = false,
}: {
  children: React.ReactNode
  adminOnly?: boolean
}) {
  const { user, isAdmin } = useAuth()
  if (!user) return <Navigate to="/login" replace />
  if (adminOnly && !isAdmin) return <Navigate to="/user" replace />
  if (!adminOnly && isAdmin) return <Navigate to="/admin" replace />
  return <>{children}</>
}

function AppRoutes() {
  const { user, isAdmin } = useAuth()

  return (
    <Routes>
      <Route path="/login" element={user ? <Navigate to={isAdmin ? '/admin' : '/user'} replace /> : <LoginPage />} />
      <Route path="/register" element={user ? <Navigate to="/user" replace /> : <RegisterPage />} />

      <Route
        path="/user"
        element={(
          <ProtectedRoute>
            <Layout variant="user" />
          </ProtectedRoute>
        )}
      >
        <Route index element={<UserHome />} />
        <Route path="bills" element={<BillsPage />} />
      </Route>

      <Route
        path="/admin"
        element={(
          <ProtectedRoute adminOnly>
            <Layout variant="admin" />
          </ProtectedRoute>
        )}
      >
        <Route index element={<AdminHome />} />
        <Route path="monitor" element={<MonitorPage />} />
        <Route path="piles" element={<PilesPage />} />
        <Route path="queue" element={<QueuePage />} />
        <Route path="acceptance" element={<AcceptancePage />} />
        <Route path="reports" element={<ReportsPage />} />
      </Route>

      <Route path="*" element={<Navigate to={user ? (isAdmin ? '/admin' : '/user') : '/login'} replace />} />
    </Routes>
  )
}

export default function App() {
  return (
    <AuthProvider>
      <AppRoutes />
    </AuthProvider>
  )
}
