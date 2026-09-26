import { useCallback, useEffect, useMemo, useState } from 'react'
import * as authApi from '../api/auth'
import { tokenStore } from '../api/client'
import { AuthContext } from './auth-context'

const EMAIL_KEY = 'bomwatcher.email'

function tokenExpiry(token) {
  try {
    const payload = JSON.parse(atob(token.split('.')[1].replace(/-/g, '+').replace(/_/g, '/')))
    return payload.exp ? payload.exp * 1000 : null
  } catch {
    return null
  }
}

export function AuthProvider({ children }) {
  const [token, setToken] = useState(() => tokenStore.get())
  const [email, setEmail] = useState(() => localStorage.getItem(EMAIL_KEY))
  const [logoutReason, setLogoutReason] = useState(null)

  const logout = useCallback((expired = false) => {
    tokenStore.clear()
    setToken(null)
    setLogoutReason(expired ? 'expired' : 'user')
  }, [])

  const login = useCallback(async (email, password) => {
    const { access_token } = await authApi.login(email, password)
    tokenStore.set(access_token)
    localStorage.setItem(EMAIL_KEY, email)
    setEmail(email)
    setToken(access_token)
    setLogoutReason(null)
  }, [])

  const signup = useCallback(
    async (email, password) => {
      await authApi.signup(email, password)
      await login(email, password)
    },
    [login],
  )

  useEffect(() => {
    const onUnauthorized = () => logout(true)
    window.addEventListener('bomwatcher:unauthorized', onUnauthorized)
    return () => window.removeEventListener('bomwatcher:unauthorized', onUnauthorized)
  }, [logout])

  useEffect(() => {
    if (!token) return
    const exp = tokenExpiry(token)
    if (!exp) return
    const ms = exp - Date.now()
    if (ms <= 0) {
      logout(true)
      return
    }
    const t = setTimeout(() => logout(true), ms)
    return () => clearTimeout(t)
  }, [token, logout])

  const value = useMemo(
    () => ({ token, email, isAuthenticated: !!token, sessionExpired: logoutReason === 'expired', logoutReason, login, signup, logout }),
    [token, email, logoutReason, login, signup, logout],
  )
  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>
}
