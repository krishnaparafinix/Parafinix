import { createContext, useCallback, useContext, useEffect, useState } from 'react'
import { getMe, login as apiLogin, logout as apiLogout } from '../api/auth'
import { clearSession, getAccessToken, getStoredUser, setSession } from '../api/client'

const AuthContext = createContext(null)

export function AuthProvider({ children }) {
  const [user, setUser] = useState(() => getStoredUser())
  const [loading, setLoading] = useState(!!getAccessToken())

  useEffect(() => {
    if (!getAccessToken()) {
      setLoading(false)
      return
    }
    getMe()
      .then((profile) => {
        setUser((prev) => ({ ...prev, ...profile }))
      })
      .catch(() => {
        clearSession()
        setUser(null)
      })
      .finally(() => setLoading(false))
  }, [])

  const login = useCallback(async (email, password) => {
    const res = await apiLogin(email, password)
    setSession(res)
    setUser(res.user)
    return res.user
  }, [])

  const logout = useCallback(() => {
    apiLogout().catch(() => {})
    clearSession()
    setUser(null)
  }, [])

  return (
    <AuthContext.Provider value={{ user, loading, login, logout }}>
      {children}
    </AuthContext.Provider>
  )
}

export function useAuth() {
  const ctx = useContext(AuthContext)
  if (!ctx) throw new Error('useAuth must be used within AuthProvider')
  return ctx
}
