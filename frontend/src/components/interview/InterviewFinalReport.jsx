import PropTypes from 'prop-types'
import InterviewScoreCard from './InterviewScoreCard'

function ReportList({ title, items, accentClass }) {
  if (!items || items.length === 0) return null

  return (
    <div className="rounded-xl border border-gray-200 bg-white p-4 shadow-sm">
      <h3 className={`mb-3 text-sm font-semibold ${accentClass}`}>{title}</h3>
      <ul className="space-y-2 text-sm text-gray-600">
        {items.map((item) => (
          <li key={item} className="flex gap-2">
            <span className="mt-1 h-1.5 w-1.5 rounded-full bg-current opacity-70" />
            <span>{item}</span>
          </li>
        ))}
      </ul>
    </div>
  )
}

ReportList.propTypes = {
  title: PropTypes.string.isRequired,
  items: PropTypes.arrayOf(PropTypes.string),
  accentClass: PropTypes.string.isRequired,
}

function InterviewFinalReport({ report }) {
  if (!report) {
    return null
  }

  return (
    <div className="space-y-4">
      <InterviewScoreCard
        title="Overall Interview Score"
        score={report.overall_score}
        subtitle="This report summarizes your answers across the full mock interview."
      />

      <div className="rounded-xl border border-gray-200 bg-white p-4 shadow-sm">
        <h3 className="mb-2 text-sm font-semibold text-gray-900">Summary</h3>
        <p className="text-sm leading-relaxed text-gray-600">{report.summary}</p>
      </div>

      <ReportList title="Strengths" items={report.strengths} accentClass="text-emerald-700" />
      <ReportList title="Areas for Improvement" items={report.areas_for_improvement} accentClass="text-rose-700" />
      <ReportList title="Recommended Actions" items={report.recommended_actions} accentClass="text-blue-700" />
    </div>
  )
}

InterviewFinalReport.propTypes = {
  report: PropTypes.shape({
    overall_score: PropTypes.number,
    summary: PropTypes.string,
    strengths: PropTypes.arrayOf(PropTypes.string),
    areas_for_improvement: PropTypes.arrayOf(PropTypes.string),
    recommended_actions: PropTypes.arrayOf(PropTypes.string),
  }),
}

export default InterviewFinalReport
