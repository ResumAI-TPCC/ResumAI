import PropTypes from 'prop-types'
import { Navigate } from 'react-router-dom'

import { useAuth } from '../contexts/AuthContext.jsx'

function PublicOnlyRoute({ children }) {
  const { loading, isAuthenticated } = useAuth()

  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-gray-50">
        <div className="bg-white rounded-xl shadow p-8 text-center">
          <div className="w-10 h-10 mx-auto border-4 border-blue-200 border-t-blue-500 rounded-full animate-spin" />
          <p className="mt-4 text-sm text-gray-600">Checking your session...</p>
        </div>
      </div>
    )
  }

  if (isAuthenticated) {
    return <Navigate to="/" replace />
  }

  return children
}

PublicOnlyRoute.propTypes = {
  children: PropTypes.node.isRequired,
}

export default PublicOnlyRoute
