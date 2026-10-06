import PropTypes from 'prop-types'
import InterviewScoreCard from './InterviewScoreCard'

function FeedbackSection({ title, items, accentClass = 'text-gray-700' }) {
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

FeedbackSection.propTypes = {
  title: PropTypes.string.isRequired,
  items: PropTypes.arrayOf(PropTypes.string),
  accentClass: PropTypes.string,
}

function InterviewFeedbackPanel({
  currentQuestion,
  currentQuestionIndex,
  totalQuestions,
  feedback,
  isSubmitting,
  isStarting,
  error,
}) {
  if (isStarting) {
    return (
      <div className="space-y-4">
        <InterviewScoreCard
          title="Question Score"
          score={null}
          subtitle="Generating a tailored mock interview for your resume and JD..."
          isLoading
        />
      </div>
    )
  }

  if (isSubmitting) {
    return (
      <div className="space-y-4">
        <InterviewScoreCard
          title="Question Score"
          score={null}
          subtitle="The AI interviewer is evaluating your answer right now."
          isLoading
        />
        <div className="rounded-xl border border-blue-100 bg-blue-50 p-4 text-sm text-blue-700">
          We are reviewing relevance, clarity, JD alignment, and how convincingly you described your impact.
        </div>
      </div>
    )
  }

  if (!feedback) {
    return (
      <div className="rounded-xl border border-dashed border-gray-300 bg-white p-6 text-center shadow-sm">
        <svg className="mx-auto mb-3 h-12 w-12 text-gray-300" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M8 10h.01M12 10h.01M16 10h.01M9 16h6M7 6h10a2 2 0 012 2v8a2 2 0 01-2 2H7a2 2 0 01-2-2V8a2 2 0 012-2z" />
        </svg>
        <h3 className="text-base font-semibold text-gray-800">Feedback Will Appear Here</h3>
        <p className="mt-2 text-sm text-gray-500">
          Submit your answer for question {currentQuestionIndex + 1} of {totalQuestions} to receive score, strengths, weaknesses, and an improved answer.
        </p>
        {error && (
          <div className="mt-4 rounded-lg border border-red-200 bg-red-50 px-3 py-2 text-left text-sm text-red-700">
            {error}
          </div>
        )}
      </div>
    )
  }

  return (
    <div className="space-y-4">
      <InterviewScoreCard
        title={`Question ${currentQuestionIndex + 1} Score`}
        score={feedback.score}
        subtitle={`Feedback for ${currentQuestion?.label || 'this answer'}.`}
      />

      <FeedbackSection title="Strengths" items={feedback.strengths} accentClass="text-emerald-700" />
      <FeedbackSection title="Weaknesses" items={feedback.weaknesses} accentClass="text-rose-700" />
      <FeedbackSection title="Suggestions" items={feedback.suggestions} accentClass="text-amber-700" />

      <div className="rounded-xl border border-indigo-100 bg-indigo-50 p-4 shadow-sm">
        <h3 className="mb-2 text-sm font-semibold text-indigo-800">JD Alignment</h3>
        <p className="text-sm leading-relaxed text-indigo-700">{feedback.jd_alignment}</p>
      </div>

      <div className="rounded-xl border border-gray-200 bg-white p-4 shadow-sm">
        <h3 className="mb-2 text-sm font-semibold text-gray-900">Improved Answer Direction</h3>
        <p className="text-sm leading-relaxed whitespace-pre-line text-gray-600">
          {feedback.improved_answer}
        </p>
      </div>
    </div>
  )
}

InterviewFeedbackPanel.propTypes = {
  currentQuestion: PropTypes.shape({
    label: PropTypes.string,
  }),
  currentQuestionIndex: PropTypes.number.isRequired,
  totalQuestions: PropTypes.number.isRequired,
  feedback: PropTypes.shape({
    score: PropTypes.number,
    strengths: PropTypes.arrayOf(PropTypes.string),
    weaknesses: PropTypes.arrayOf(PropTypes.string),
    suggestions: PropTypes.arrayOf(PropTypes.string),
    improved_answer: PropTypes.string,
    jd_alignment: PropTypes.string,
  }),
  isSubmitting: PropTypes.bool.isRequired,
  isStarting: PropTypes.bool.isRequired,
  error: PropTypes.string,
}

export default InterviewFeedbackPanel
