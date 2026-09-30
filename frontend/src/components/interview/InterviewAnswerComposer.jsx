import PropTypes from 'prop-types'

function InterviewAnswerComposer({
  answer,
  onAnswerChange,
  onSubmit,
  isSubmitting,
  canSubmit,
  hasFeedback,
}) {
  const buttonLabel = isSubmitting
    ? 'Evaluating Answer...'
    : hasFeedback
      ? 'Resubmit Answer'
      : 'Submit Answer'

  return (
    <div className="rounded-xl bg-white p-6 shadow-sm">
      <div className="mb-3 flex items-center justify-between">
        <div>
          <h3 className="text-base font-semibold text-gray-900">Your Answer</h3>
          <p className="text-sm text-gray-500">Aim for a clear, structured answer with a concrete result.</p>
        </div>
        <span className="text-xs font-medium text-gray-400">{answer.trim().split(/\s+/).filter(Boolean).length} words</span>
      </div>

      <textarea
        value={answer}
        onChange={(event) => onAnswerChange(event.target.value)}
        placeholder="Type your answer here..."
        rows={10}
        className="w-full resize-none rounded-xl border border-gray-300 px-4 py-3 text-sm text-gray-700 shadow-inner focus:border-blue-500 focus:outline-none focus:ring-2 focus:ring-blue-500/20"
      />

      <div className="mt-4 flex items-center justify-between gap-3">
        <p className="text-xs text-gray-500">
          Tip: Use context, your action, and the final outcome to make your answer stronger.
        </p>

        <button
          onClick={onSubmit}
          disabled={!canSubmit || isSubmitting}
          className="inline-flex items-center justify-center rounded-lg bg-blue-600 px-4 py-2.5 text-sm font-medium text-white transition-colors hover:bg-blue-700 disabled:cursor-not-allowed disabled:opacity-50"
        >
          {buttonLabel}
        </button>
      </div>
    </div>
  )
}

InterviewAnswerComposer.propTypes = {
  answer: PropTypes.string.isRequired,
  onAnswerChange: PropTypes.func.isRequired,
  onSubmit: PropTypes.func.isRequired,
  isSubmitting: PropTypes.bool.isRequired,
  canSubmit: PropTypes.bool.isRequired,
  hasFeedback: PropTypes.bool.isRequired,
}

export default InterviewAnswerComposer
