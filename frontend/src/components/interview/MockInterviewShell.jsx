import PropTypes from 'prop-types'
import InterviewFeedbackPanel from './InterviewFeedbackPanel'
import InterviewFinalReport from './InterviewFinalReport'
import InterviewQuestionPanel from './InterviewQuestionPanel'
import InterviewSidebarSummary from './InterviewSidebarSummary'

function MockInterviewShell({
  uploadedFile,
  companyName,
  jobTitle,
  jobDescription,
  matchScore,
  interview,
  leftSidebarOpen,
  rightSidebarOpen,
  onOpenLeftSidebar,
  onCloseLeftSidebar,
  onOpenRightSidebar,
  onCloseRightSidebar,
  onBackToMatch,
}) {
  const totalQuestions = interview.questions.length || 5

  return (
    <div className={`flex h-screen bg-gray-50 ${leftSidebarOpen || rightSidebarOpen ? 'overflow-hidden' : 'overflow-auto'} md:overflow-hidden`}>
      <button
        className="fixed left-4 top-4 z-10 rounded-md bg-white p-2 shadow md:hidden"
        onClick={onOpenLeftSidebar}
        aria-label="Open interview summary"
      >
        <svg className="h-6 w-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 6h16M4 12h16M4 18h16" />
        </svg>
      </button>

      <button
        className="fixed right-4 top-4 z-10 rounded-md bg-white p-2 shadow md:hidden"
        onClick={onOpenRightSidebar}
        aria-label="Open interview feedback"
      >
        <svg className="h-6 w-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 6h16M4 12h16M4 18h16" />
        </svg>
      </button>

      {leftSidebarOpen && (
        <div className="fixed inset-0 z-30 bg-black/40 md:hidden" onClick={onCloseLeftSidebar} aria-hidden="true" />
      )}

      {rightSidebarOpen && (
        <div className="fixed inset-0 z-30 bg-black/40 md:hidden" onClick={onCloseRightSidebar} aria-hidden="true" />
      )}

      <InterviewSidebarSummary
        uploadedFile={uploadedFile}
        companyName={companyName}
        jobTitle={jobTitle}
        jobDescription={jobDescription}
        matchScore={matchScore}
        currentQuestionIndex={interview.currentQuestionIndex}
        totalQuestions={totalQuestions}
        isOpen={leftSidebarOpen}
        onClose={onCloseLeftSidebar}
        onBackToMatch={onBackToMatch}
        onRestartInterview={interview.restartInterview}
        disableRestart={interview.isStarting || interview.isSubmitting || interview.isGeneratingReport}
      />

      <InterviewQuestionPanel
        currentQuestion={interview.currentQuestion}
        currentQuestionIndex={interview.currentQuestionIndex}
        totalQuestions={totalQuestions}
        draftAnswer={interview.draftAnswer}
        onDraftAnswerChange={interview.updateDraftAnswer}
        onSubmitAnswer={interview.submitCurrentAnswer}
        onNextQuestion={interview.goToNextStep}
        isStarting={interview.isStarting}
        isSubmitting={interview.isSubmitting}
        isGeneratingReport={interview.isGeneratingReport}
        isCompleted={interview.isCompleted}
        currentFeedback={interview.currentFeedback}
        submittedAnswer={interview.submittedAnswer}
        error={interview.error}
        onBackToMatch={onBackToMatch}
        onRestartInterview={interview.restartInterview}
      />

      <aside
        className={`fixed inset-y-0 right-0 z-40 w-80 transform border-l border-gray-200 bg-white transition-transform duration-200 ${rightSidebarOpen ? 'translate-x-0' : 'translate-x-full'} md:relative md:h-screen md:w-80 md:translate-x-0`}
        aria-hidden={rightSidebarOpen ? 'false' : 'true'}
      >
        <div className="flex h-full flex-col">
          <div className="flex items-center gap-3 border-b border-gray-200 p-4">
            <div>
              <h2 className="text-lg font-bold text-gray-800">
                {interview.isCompleted ? 'Interview Report' : 'AI Feedback'}
              </h2>
              <p className="text-xs text-gray-500">
                {interview.isCompleted ? 'Overall coaching summary' : 'Per-question feedback and coaching'}
              </p>
            </div>

            <button
              onClick={onCloseRightSidebar}
              className="ml-auto rounded bg-gray-100 p-2 hover:bg-gray-200 md:hidden"
              aria-label="Close interview feedback"
            >
              <svg className="h-4 w-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
              </svg>
            </button>
          </div>

          <div className="flex-1 overflow-y-auto p-4">
            {interview.isCompleted ? (
              <InterviewFinalReport report={interview.finalReport} />
            ) : (
              <InterviewFeedbackPanel
                currentQuestion={interview.currentQuestion}
                currentQuestionIndex={interview.currentQuestionIndex}
                totalQuestions={totalQuestions}
                feedback={interview.currentFeedback}
                isSubmitting={interview.isSubmitting || interview.isGeneratingReport}
                isStarting={interview.isStarting}
                error={interview.error}
              />
            )}
          </div>
        </div>
      </aside>
    </div>
  )
}

MockInterviewShell.propTypes = {
  uploadedFile: PropTypes.shape({
    name: PropTypes.string,
    size: PropTypes.number,
  }),
  companyName: PropTypes.string,
  jobTitle: PropTypes.string,
  jobDescription: PropTypes.string,
  matchScore: PropTypes.number,
  interview: PropTypes.shape({
    questions: PropTypes.arrayOf(PropTypes.object).isRequired,
    currentQuestionIndex: PropTypes.number.isRequired,
    currentQuestion: PropTypes.object,
    currentFeedback: PropTypes.object,
    submittedAnswer: PropTypes.string,
    draftAnswer: PropTypes.string.isRequired,
    finalReport: PropTypes.object,
    error: PropTypes.string,
    isStarting: PropTypes.bool.isRequired,
    isSubmitting: PropTypes.bool.isRequired,
    isGeneratingReport: PropTypes.bool.isRequired,
    isCompleted: PropTypes.bool.isRequired,
    updateDraftAnswer: PropTypes.func.isRequired,
    submitCurrentAnswer: PropTypes.func.isRequired,
    goToNextStep: PropTypes.func.isRequired,
    restartInterview: PropTypes.func.isRequired,
  }).isRequired,
  leftSidebarOpen: PropTypes.bool.isRequired,
  rightSidebarOpen: PropTypes.bool.isRequired,
  onOpenLeftSidebar: PropTypes.func.isRequired,
  onCloseLeftSidebar: PropTypes.func.isRequired,
  onOpenRightSidebar: PropTypes.func.isRequired,
  onCloseRightSidebar: PropTypes.func.isRequired,
  onBackToMatch: PropTypes.func.isRequired,
}

export default MockInterviewShell
