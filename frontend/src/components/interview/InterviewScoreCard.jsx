import PropTypes from 'prop-types'

function InterviewScoreCard({ title, score, subtitle, isLoading = false }) {
  return (
    <div className="rounded-xl bg-gradient-to-r from-indigo-500 via-blue-600 to-cyan-500 p-4 text-white shadow-md">
      <div className="flex items-center justify-between">
        <div>
          <p className="text-xs font-medium uppercase tracking-wide text-white/85">{title}</p>
          {isLoading ? (
            <div className="mt-2 flex items-center gap-2">
              <div className="h-5 w-5 animate-spin rounded-full border-2 border-white/40 border-t-white" />
              <span className="text-sm text-white/85">Calculating...</span>
            </div>
          ) : (
            <div className="mt-1 flex items-baseline gap-1">
              <span className="text-3xl font-bold">{score ?? '--'}</span>
              <span className="text-sm font-medium">/100</span>
            </div>
          )}
        </div>
        <svg className="h-10 w-10 opacity-70" fill="currentColor" viewBox="0 0 20 20" aria-hidden="true">
          <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z" clipRule="evenodd" />
        </svg>
      </div>

      <p className="mt-3 text-xs text-white/90">{subtitle}</p>
    </div>
  )
}

InterviewScoreCard.propTypes = {
  title: PropTypes.string.isRequired,
  score: PropTypes.number,
  subtitle: PropTypes.string.isRequired,
  isLoading: PropTypes.bool,
}

export default InterviewScoreCard
