import PropTypes from 'prop-types'

function InterviewProgressBar({ current, total }) {
  const safeTotal = total > 0 ? total : 1
  const safeCurrent = Math.min(safeTotal, Math.max(0, current))
  const progress = Math.round((safeCurrent / safeTotal) * 100)

  return (
    <div>
      <div className="mb-2 flex items-center justify-between text-xs text-gray-500">
        <span>Interview Progress</span>
        <span>{safeCurrent} / {safeTotal}</span>
      </div>
      <div className="h-2 w-full rounded-full bg-gray-200">
        <div
          className="h-2 rounded-full bg-gradient-to-r from-blue-500 to-indigo-600 transition-all duration-300"
          style={{ width: `${progress}%` }}
        />
      </div>
    </div>
  )
}

InterviewProgressBar.propTypes = {
  current: PropTypes.number.isRequired,
  total: PropTypes.number.isRequired,
}

export default InterviewProgressBar
