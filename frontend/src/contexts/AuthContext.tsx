import { createContext, useContext, useEffect, useMemo, useState, type ReactNode } from 'react'
import { setApiUsername } from '../api/client'
import type { User } from '../api/types'

interface AuthContextValue {
  user: User | null
  login: (user: User) => void
  logout: () => void
  isAdmin: boolean
}

const STORAGE_KEY = 'smartcharge_user'

const AuthContext = createContext<AuthContextValue | null>(null)

function loadStoredUser(): User | null {
  const raw = localStorage.getItem(STORAGE_KEY)
  if (!raw) return null
  try {
    return JSON.parse(raw) as User
  } catch {
    return null
  }
}

export function AuthProvider({ children }: { children: ReactNode }) {
  const [user, setUser] = useState<User | null>(() => loadStoredUser())

  useEffect(() => {
    setApiUsername(user?.username ?? null)
  }, [user])

  const value = useMemo<AuthContextValue>(() => ({
    user,
    login(nextUser) {
      setUser(nextUser)
      localStorage.setItem(STORAGE_KEY, JSON.stringify(nextUser))
    },
    logout() {
      setUser(null)
      localStorage.removeItem(STORAGE_KEY)
    },
    isAdmin: user?.role === 'admin',
  }), [user])

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>
}

export function useAuth() {
  const context = useContext(AuthContext)
  if (!context) {
    throw new Error('useAuth must be used within AuthProvider')
  }
  return context
}
