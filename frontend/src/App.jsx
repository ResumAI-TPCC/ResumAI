import { Navigate, Route, Routes } from 'react-router-dom'

import { ENV } from './config/env'
import ProtectedRoute from './components/ProtectedRoute.jsx'
import PublicOnlyRoute from './components/PublicOnlyRoute.jsx'
import AccountPage from './pages/AccountPage.jsx'
import LoginPage from './pages/LoginPage.jsx'
import RegisterPage from './pages/RegisterPage.jsx'
import WorkspacePage from './pages/WorkspacePage.jsx'

function App() {
  return (
    <div className="min-h-screen flex flex-col">
      <Routes>
        <Route
          path="/login"
          element={(
            <PublicOnlyRoute>
              <LoginPage />
            </PublicOnlyRoute>
          )}
        />
        <Route
          path="/register"
          element={(
            <PublicOnlyRoute>
              <RegisterPage />
            </PublicOnlyRoute>
          )}
        />
        <Route
          path="/"
          element={(
            <ProtectedRoute>
              <WorkspacePage />
            </ProtectedRoute>
          )}
        />
        <Route
          path="/account"
          element={(
            <ProtectedRoute>
              <AccountPage />
            </ProtectedRoute>
          )}
        />
        <Route path="*" element={<Navigate to="/" replace />} />
      </Routes>

      <footer className="fixed bottom-2 right-4 z-20 pointer-events-none">
        <span className="text-xs text-gray-400 bg-white/80 backdrop-blur px-2 py-1 rounded-full shadow-sm">
          v{ENV.APP_VERSION}
        </span>
      </footer>
    </div>
  )
}

export default App
