import PropTypes from 'prop-types'
import InterviewAnswerComposer from './InterviewAnswerComposer'
import InterviewProgressBar from './InterviewProgressBar'
import QuestionTypeBadge from './QuestionTypeBadge'

function InterviewQuestionPanel({
  currentQuestion,
  currentQuestionIndex,
  totalQuestions,
  draftAnswer,
  onDraftAnswerChange,
  onSubmitAnswer,
  onNextQuestion,
  isStarting,
  isSubmitting,
  isGeneratingReport,
  isCompleted,
  currentFeedback,
  submittedAnswer,
  error,
  onBackToMatch,
  onRestartInterview,
}) {
  if (isStarting) {
    return (
      <main className="flex-1 overflow-y-auto bg-gray-50 p-6">
        <div className="mx-auto flex max-w-3xl items-center justify-center">
          <div className="w-full rounded-2xl bg-white p-10 text-center shadow-sm">
            <div className="mx-auto mb-4 h-16 w-16 animate-spin rounded-full border-4 border-blue-200 border-t-blue-600" />
            <h2 className="text-xl font-semibold text-gray-900">Generating Your Mock Interview</h2>
            <p className="mt-2 text-sm text-gray-500">
              We are building a five-question interview based on your resume, JD, and latest match analysis.
            </p>
          </div>
        </div>
      </main>
    )
  }

  if (isCompleted) {
    return (
      <main className="flex-1 overflow-y-auto bg-gray-50 p-6">
        <div className="mx-auto max-w-3xl space-y-6">
          <div className="rounded-2xl bg-white p-8 text-center shadow-sm">
            <div className="mx-auto mb-4 flex h-14 w-14 items-center justify-center rounded-full bg-emerald-100 text-emerald-600">
              <svg className="h-7 w-7" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
              </svg>
            </div>
            <h2 className="text-2xl font-semibold text-gray-900">Interview Complete</h2>
            <p className="mt-2 text-sm leading-relaxed text-gray-500">
              Your final report is ready on the right. Review the strengths and recommended actions, then decide whether you want another round.
            </p>

            <div className="mt-6 flex flex-col justify-center gap-3 sm:flex-row">
              <button
                onClick={onBackToMatch}
                className="rounded-lg border border-gray-300 px-4 py-2.5 text-sm font-medium text-gray-700 transition-colors hover:bg-gray-50"
              >
                Back to Match
              </button>
              <button
                onClick={onRestartInterview}
                className="rounded-lg bg-blue-600 px-4 py-2.5 text-sm font-medium text-white transition-colors hover:bg-blue-700"
              >
                Start Another Round
              </button>
            </div>
          </div>
        </div>
      </main>
    )
  }

  if (!currentQuestion) {
    return (
      <main className="flex-1 overflow-y-auto bg-gray-50 p-6">
        <div className="mx-auto max-w-3xl">
          <div className="rounded-2xl bg-white p-8 text-center shadow-sm">
            <h2 className="text-xl font-semibold text-gray-900">No Interview Question Available</h2>
            <p className="mt-2 text-sm text-gray-500">
              We could not load the interview question set. Please restart the mock interview from the match view.
            </p>
            {error && (
              <div className="mx-auto mt-4 max-w-xl rounded-lg border border-red-200 bg-red-50 px-4 py-3 text-left text-sm text-red-700">
                {error}
              </div>
            )}
          </div>
        </div>
      </main>
    )
  }

  const isLastQuestion = currentQuestionIndex >= totalQuestions - 1

  return (
    <main className="flex-1 overflow-y-auto bg-gray-50 p-6">
      <div className="mx-auto max-w-3xl space-y-5">
        <div className="rounded-2xl bg-white p-6 shadow-sm">
          <div className="mb-5">
            <InterviewProgressBar current={currentQuestionIndex + 1} total={totalQuestions} />
          </div>

          <div className="mb-4 flex items-center gap-3">
            <QuestionTypeBadge type={currentQuestion.type} label={currentQuestion.label} />
            <span className="text-xs font-medium uppercase tracking-wide text-gray-400">
              Question {currentQuestionIndex + 1}
            </span>
          </div>

          <h2 className="text-2xl font-semibold leading-snug text-gray-900">
            {currentQuestion.prompt}
          </h2>

          <div className="mt-5 rounded-xl border border-gray-200 bg-gray-50 p-4">
            <h3 className="mb-2 text-sm font-semibold text-gray-900">What the interviewer is listening for</h3>
            <div className="flex flex-wrap gap-2">
              {currentQuestion.focus_areas?.map((area) => (
                <span
                  key={area}
                  className="rounded-full bg-white px-3 py-1 text-xs font-medium text-gray-600 shadow-sm"
                >
                  {area}
                </span>
              ))}
            </div>
          </div>
        </div>

        <InterviewAnswerComposer
          answer={draftAnswer}
          onAnswerChange={onDraftAnswerChange}
          onSubmit={onSubmitAnswer}
          isSubmitting={isSubmitting}
          canSubmit={Boolean(draftAnswer.trim()) && !isGeneratingReport}
          hasFeedback={Boolean(currentFeedback)}
        />

        {submittedAnswer && (
          <div className="rounded-2xl border border-gray-200 bg-white p-5 shadow-sm">
            <div className="mb-2 flex items-center justify-between">
              <h3 className="text-sm font-semibold text-gray-900">Latest Submitted Answer</h3>
              {currentFeedback && (
                <span className="rounded-full bg-emerald-100 px-3 py-1 text-xs font-medium text-emerald-700">
                  Feedback ready
                </span>
              )}
            </div>
            <p className="text-sm leading-relaxed whitespace-pre-line text-gray-600">
              {submittedAnswer}
            </p>
          </div>
        )}

        {error && (
          <div className="rounded-xl border border-red-200 bg-red-50 px-4 py-3 text-sm text-red-700 shadow-sm">
            {error}
          </div>
        )}

        {currentFeedback && (
          <div className="rounded-2xl border border-blue-100 bg-blue-50 p-5 shadow-sm">
            <div className="flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between">
              <div>
                <h3 className="text-base font-semibold text-blue-900">Feedback Ready</h3>
                <p className="mt-1 text-sm text-blue-700">
                  Review the score and coaching notes on the right, then continue when you are ready.
                </p>
              </div>

              <button
                onClick={onNextQuestion}
                disabled={isGeneratingReport}
                className="inline-flex items-center justify-center rounded-lg bg-blue-600 px-4 py-2.5 text-sm font-medium text-white transition-colors hover:bg-blue-700 disabled:cursor-not-allowed disabled:opacity-50"
              >
                {isGeneratingReport
                  ? 'Building Final Report...'
                  : isLastQuestion
                    ? 'Finish Interview'
                    : 'Next Question'}
              </button>
            </div>
          </div>
        )}
      </div>
    </main>
  )
}

InterviewQuestionPanel.propTypes = {
  currentQuestion: PropTypes.shape({
    id: PropTypes.string,
    type: PropTypes.string,
    label: PropTypes.string,
    prompt: PropTypes.string,
    focus_areas: PropTypes.arrayOf(PropTypes.string),
  }),
  currentQuestionIndex: PropTypes.number.isRequired,
  totalQuestions: PropTypes.number.isRequired,
  draftAnswer: PropTypes.string.isRequired,
  onDraftAnswerChange: PropTypes.func.isRequired,
  onSubmitAnswer: PropTypes.func.isRequired,
  onNextQuestion: PropTypes.func.isRequired,
  isStarting: PropTypes.bool.isRequired,
  isSubmitting: PropTypes.bool.isRequired,
  isGeneratingReport: PropTypes.bool.isRequired,
  isCompleted: PropTypes.bool.isRequired,
  currentFeedback: PropTypes.shape({
    score: PropTypes.number,
  }),
  submittedAnswer: PropTypes.string,
  error: PropTypes.string,
  onBackToMatch: PropTypes.func.isRequired,
  onRestartInterview: PropTypes.func.isRequired,
}

export default InterviewQuestionPanel
