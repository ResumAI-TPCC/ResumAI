import PropTypes from 'prop-types'

function AuthPageShell({ title, subtitle, children, footer }) {
  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-100 via-white to-blue-50 flex items-center justify-center px-4 py-10">
      <div className="w-full max-w-md">
        <div className="mb-8 text-center">
          <p className="text-sm font-semibold tracking-[0.2em] text-blue-600 uppercase">ResumAI</p>
          <h1 className="mt-3 text-3xl font-bold text-gray-900">{title}</h1>
          <p className="mt-3 text-sm text-gray-600">{subtitle}</p>
        </div>

        <div className="bg-white shadow-xl rounded-2xl border border-gray-100 p-6 sm:p-8">
          {children}
        </div>

        {footer && (
          <div className="mt-6 text-center text-sm text-gray-600">
            {footer}
          </div>
        )}
      </div>
    </div>
  )
}

AuthPageShell.propTypes = {
  title: PropTypes.string.isRequired,
  subtitle: PropTypes.string.isRequired,
  children: PropTypes.node.isRequired,
  footer: PropTypes.node,
}

AuthPageShell.defaultProps = {
  footer: null,
}

export default AuthPageShell
