import { useState } from 'react'
import { Navigate, Outlet, useLocation } from 'react-router-dom'
import { useAuth } from '../context/useAuth'

export function ProtectedRoute() {
  const { isAuthenticated, logoutReason } = useAuth()
  const location = useLocation()
  if (!isAuthenticated) {
    if (logoutReason === 'user') return <Navigate to="/" replace />
    return <Navigate to="/login" replace state={{ from: location.pathname }} />
  }
  return <Outlet />
}

export function GuestRoute() {
  const { isAuthenticated } = useAuth()
  const [signedInOnArrival] = useState(isAuthenticated)
  if (signedInOnArrival) return <Navigate to="/app" replace />
  return <Outlet />
}
