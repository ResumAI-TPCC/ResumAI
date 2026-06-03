import { Link, useLocation } from 'react-router-dom'

import { useAuth } from '../contexts/AuthContext.jsx'

function AppHeader() {
  const { user, logout } = useAuth()
  const location = useLocation()

  const linkClass = (path) => (
    location.pathname === path
      ? 'text-blue-600 font-medium'
      : 'text-gray-600 hover:text-gray-900'
  )

  return (
    <header className="border-b border-gray-200 bg-white">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 h-16 flex items-center justify-between gap-4">
        <div className="flex items-center gap-6">
          <Link to="/" className="text-lg font-semibold text-gray-900">
            ResumAI
          </Link>
          <nav className="flex items-center gap-4 text-sm">
            <Link to="/" className={linkClass('/')}>
              Workspace
            </Link>
            <Link to="/account" className={linkClass('/account')}>
              Account
            </Link>
          </nav>
        </div>

        <div className="flex items-center gap-3">
          <div className="hidden sm:block text-right">
            <p className="text-sm font-medium text-gray-900">{user?.email || 'Signed in'}</p>
            <p className="text-xs text-gray-500">Firebase Auth</p>
          </div>
          <button
            type="button"
            onClick={logout}
            className="inline-flex items-center px-3 py-2 rounded-md text-sm font-medium bg-gray-900 text-white hover:bg-gray-800 transition-colors"
          >
            Log out
          </button>
        </div>
      </div>
    </header>
  )
}

export default AppHeader
