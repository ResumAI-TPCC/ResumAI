import { useEffect, useState } from 'react'

import AppHeader from '../components/AppHeader.jsx'
import { useAuth } from '../contexts/AuthContext.jsx'
import { getCurrentUser } from '../utils/api.js'

function AccountPage() {
  const { user, configError } = useAuth()
  const [backendUser, setBackendUser] = useState(null)
  const [backendError, setBackendError] = useState('')
  const [backendLoading, setBackendLoading] = useState(false)

  useEffect(() => {
    let isMounted = true

    async function loadBackendUser() {
      if (!user) return

      setBackendLoading(true)
      setBackendError('')

      try {
        const response = await getCurrentUser()
        if (isMounted) {
          setBackendUser(response.data)
        }
      } catch (error) {
        if (isMounted) {
          setBackendUser(null)
          setBackendError(error.message || 'Unable to verify backend session.')
        }
      } finally {
        if (isMounted) {
          setBackendLoading(false)
        }
      }
    }

    loadBackendUser()

    return () => {
      isMounted = false
    }
  }, [user])

  return (
    <div className="min-h-screen bg-gray-50">
      <AppHeader />
      <main className="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        <div className="bg-white rounded-2xl border border-gray-200 shadow-sm p-6">
          <div className="mb-6">
            <p className="text-sm font-semibold tracking-[0.2em] text-blue-600 uppercase">Account</p>
            <h1 className="mt-2 text-2xl font-bold text-gray-900">Your authenticated session</h1>
            <p className="mt-2 text-sm text-gray-600">
              This Phase 1 page confirms that frontend authentication is working before we add persisted product data.
            </p>
          </div>

          <div className="grid sm:grid-cols-2 gap-4">
            <div className="rounded-xl border border-gray-200 p-4">
              <p className="text-xs uppercase tracking-wide text-gray-500">Client email</p>
              <p className="mt-2 text-sm font-medium text-gray-900 break-all">{user?.email || 'N/A'}</p>
            </div>
            <div className="rounded-xl border border-gray-200 p-4">
              <p className="text-xs uppercase tracking-wide text-gray-500">Email verified</p>
              <p className="mt-2 text-sm font-medium text-gray-900">{user?.emailVerified ? 'Yes' : 'No'}</p>
            </div>
            <div className="rounded-xl border border-gray-200 p-4 sm:col-span-2">
              <p className="text-xs uppercase tracking-wide text-gray-500">Firebase UID</p>
              <p className="mt-2 text-sm font-medium text-gray-900 break-all">{user?.uid || 'N/A'}</p>
            </div>
          </div>

          <div className="mt-6 rounded-xl border border-gray-200 p-4">
            <div className="flex items-center justify-between gap-3">
              <div>
                <p className="text-xs uppercase tracking-wide text-gray-500">Backend verification</p>
                <p className="mt-1 text-sm text-gray-600">
                  {backendLoading ? 'Checking backend session...' : 'FastAPI recognition of the Firebase ID token'}
                </p>
              </div>
              <span
                className={`rounded-full px-3 py-1 text-xs font-medium ${
                  backendUser
                    ? 'bg-green-100 text-green-700'
                    : 'bg-amber-100 text-amber-700'
                }`}
              >
                {backendUser ? 'Verified' : 'Pending'}
              </span>
            </div>

            {backendUser && (
              <div className="mt-4 grid sm:grid-cols-2 gap-4">
                <div className="rounded-lg bg-gray-50 p-3">
                  <p className="text-xs uppercase tracking-wide text-gray-500">Backend email</p>
                  <p className="mt-2 text-sm font-medium text-gray-900 break-all">{backendUser.email || 'N/A'}</p>
                </div>
                <div className="rounded-lg bg-gray-50 p-3">
                  <p className="text-xs uppercase tracking-wide text-gray-500">Backend UID</p>
                  <p className="mt-2 text-sm font-medium text-gray-900 break-all">{backendUser.firebase_uid}</p>
                </div>
              </div>
            )}

            {backendError && (
              <div className="mt-4 rounded-lg border border-amber-200 bg-amber-50 px-4 py-3 text-sm text-amber-800">
                {backendError}
              </div>
            )}
          </div>

          {configError && (
            <div className="mt-6 rounded-lg border border-amber-200 bg-amber-50 px-4 py-3 text-sm text-amber-800">
              {configError}
            </div>
          )}
        </div>
      </main>
    </div>
  )
}

export default AccountPage
