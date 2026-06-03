import { createContext, useContext, useEffect, useMemo, useState } from 'react'
import PropTypes from 'prop-types'
import {
  createUserWithEmailAndPassword,
  onAuthStateChanged,
  signInWithEmailAndPassword,
  signOut,
} from 'firebase/auth'

import {
  firebaseAuth,
  getFirebaseConfigError,
  isFirebaseConfigured,
} from '../services/firebase.js'
import { ENV } from '../config/env.js'

const AuthContext = createContext(null)
const DEV_AUTH_STORAGE_KEY = 'resumai_dev_auth_user'

const isDevAuthConfigured = Boolean(
  ENV.DEV_AUTH_EMAIL && ENV.DEV_AUTH_PASSWORD && ENV.DEV_AUTH_TOKEN,
)

function buildDevUser(email = ENV.DEV_AUTH_EMAIL) {
  return {
    uid: 'local-test-user',
    email,
    displayName: ENV.DEV_AUTH_DISPLAY_NAME,
    emailVerified: true,
    isDevUser: true,
  }
}

function getInitialUser() {
  if (!isFirebaseConfigured && isDevAuthConfigured) {
    return localStorage.getItem(DEV_AUTH_STORAGE_KEY) ? buildDevUser() : null
  }

  return null
}

function normalizeAuthError(error) {
  if (!error) return 'Authentication failed'

  const code = error.code || ''

  switch (code) {
    case 'auth/email-already-in-use':
      return 'This email is already in use.'
    case 'auth/invalid-email':
      return 'Please enter a valid email address.'
    case 'auth/user-not-found':
    case 'auth/wrong-password':
    case 'auth/invalid-credential':
      return 'Incorrect email or password.'
    case 'auth/weak-password':
      return 'Password should be at least 6 characters.'
    default:
      return error.message || 'Authentication failed'
  }
}

function ensureFirebaseAuth() {
  if (!isFirebaseConfigured || !firebaseAuth) {
    throw new Error(getFirebaseConfigError() || 'Firebase Auth is not configured.')
  }

  return firebaseAuth
}

export function AuthProvider({ children }) {
  const [user, setUser] = useState(getInitialUser)
  const [loading, setLoading] = useState(isFirebaseConfigured && Boolean(firebaseAuth))

  useEffect(() => {
    if (!isFirebaseConfigured || !firebaseAuth) {
      return undefined
    }

    const unsubscribe = onAuthStateChanged(firebaseAuth, (nextUser) => {
      setUser(nextUser)
      setLoading(false)
    })

    return unsubscribe
  }, [])

  const value = useMemo(() => ({
    user,
    loading,
    isAuthenticated: Boolean(user),
    isConfigured: isFirebaseConfigured || isDevAuthConfigured,
    configError: isDevAuthConfigured ? null : getFirebaseConfigError(),
    isDevAuth: !isFirebaseConfigured && isDevAuthConfigured,
    async login(email, password) {
      if (!isFirebaseConfigured && isDevAuthConfigured) {
        if (email.trim() === ENV.DEV_AUTH_EMAIL && password === ENV.DEV_AUTH_PASSWORD) {
          const devUser = buildDevUser(email.trim())
          localStorage.setItem(DEV_AUTH_STORAGE_KEY, 'true')
          setUser(devUser)
          return devUser
        }

        throw new Error('Incorrect email or password.')
      }

      try {
        const auth = ensureFirebaseAuth()
        const credentials = await signInWithEmailAndPassword(auth, email, password)
        return credentials.user
      } catch (error) {
        throw new Error(normalizeAuthError(error))
      }
    },
    async register(email, password) {
      if (!isFirebaseConfigured && isDevAuthConfigured) {
        throw new Error('Registration is disabled for the local test account.')
      }

      try {
        const auth = ensureFirebaseAuth()
        const credentials = await createUserWithEmailAndPassword(auth, email, password)
        return credentials.user
      } catch (error) {
        throw new Error(normalizeAuthError(error))
      }
    },
    async logout() {
      if (!isFirebaseConfigured && isDevAuthConfigured) {
        localStorage.removeItem(DEV_AUTH_STORAGE_KEY)
        setUser(null)
        return
      }

      try {
        const auth = ensureFirebaseAuth()
        await signOut(auth)
      } catch (error) {
        throw new Error(normalizeAuthError(error))
      }
    },
  }), [loading, user])

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>
}

AuthProvider.propTypes = {
  children: PropTypes.node.isRequired,
}

export function useAuth() {
  const context = useContext(AuthContext)

  if (!context) {
    throw new Error('useAuth must be used within an AuthProvider')
  }

  return context
}
