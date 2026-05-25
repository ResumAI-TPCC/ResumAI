import PropTypes from 'prop-types'
import { QUESTION_TYPE_META } from '../../mocks/interviewFixtures'

const ACCENT_STYLES = {
  blue: 'bg-blue-100 text-blue-700 border-blue-200',
  emerald: 'bg-emerald-100 text-emerald-700 border-emerald-200',
  amber: 'bg-amber-100 text-amber-700 border-amber-200',
  violet: 'bg-violet-100 text-violet-700 border-violet-200',
  rose: 'bg-rose-100 text-rose-700 border-rose-200',
}

function QuestionTypeBadge({ type, label }) {
  const config = QUESTION_TYPE_META[type] || {}
  const accentClass = ACCENT_STYLES[config.accent] || ACCENT_STYLES.blue

  return (
    <span className={`inline-flex items-center rounded-full border px-3 py-1 text-xs font-medium ${accentClass}`}>
      {label || config.label || type}
    </span>
  )
}

QuestionTypeBadge.propTypes = {
  type: PropTypes.string.isRequired,
  label: PropTypes.string,
}

export default QuestionTypeBadge
