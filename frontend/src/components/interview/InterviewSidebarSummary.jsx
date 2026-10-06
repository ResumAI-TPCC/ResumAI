import PropTypes from 'prop-types'
import InterviewProgressBar from './InterviewProgressBar'

function formatFileSize(bytes) {
  if (!bytes) return '0 KB'
  return `${(bytes / 1024).toFixed(1)} KB`
}

function summarizeText(value, limit = 180) {
  if (!value) return 'No job description provided.'
  if (value.length <= limit) return value
  return `${value.slice(0, limit).trim()}...`
}

function InterviewSidebarSummary({
  uploadedFile,
  companyName,
  jobTitle,
  jobDescription,
  matchScore,
  currentQuestionIndex,
  totalQuestions,
  isOpen,
  onClose,
  onBackToMatch,
  onRestartInterview,
  disableRestart = false,
}) {
  return (
    <aside
      className={`fixed inset-y-0 left-0 z-40 w-80 transform border-r border-gray-200 bg-white transition-transform duration-200 ${isOpen ? 'translate-x-0' : '-translate-x-full'} md:relative md:h-screen md:w-96 md:translate-x-0`}
      aria-hidden={isOpen ? 'false' : 'true'}
    >
      <div className="flex h-full flex-col overflow-y-auto">
        <div className="border-b border-gray-200 p-5">
          <div className="flex items-center gap-3">
            <div className="flex h-10 w-10 items-center justify-center rounded-lg bg-gradient-to-br from-blue-600 to-cyan-500 text-white shadow-sm">
              <svg className="h-5 w-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8 10h.01M12 10h.01M16 10h.01M9 16h6M7 6h10a2 2 0 012 2v8a2 2 0 01-2 2H7a2 2 0 01-2-2V8a2 2 0 012-2z" />
              </svg>
            </div>
            <div>
              <h1 className="text-xl font-bold text-gray-900">Mock Interview</h1>
              <p className="text-xs text-gray-500">AI-guided practice session</p>
            </div>

            <button
              onClick={onClose}
              className="ml-auto rounded bg-gray-100 p-2 hover:bg-gray-200 md:hidden"
              aria-label="Close interview summary"
            >
              <svg className="h-4 w-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
              </svg>
            </button>
          </div>
        </div>

        <div className="space-y-4 p-5">
          <div className="rounded-xl border border-blue-100 bg-blue-50 p-4">
            <p className="text-xs font-medium uppercase tracking-wide text-blue-700">Match Score</p>
            <div className="mt-2 flex items-baseline gap-1">
              <span className="text-3xl font-bold text-blue-900">{matchScore ?? '--'}</span>
              <span className="text-sm font-medium text-blue-800">/100</span>
            </div>
            <p className="mt-2 text-xs text-blue-700">Interview questions are grounded in the role fit context from your latest match analysis.</p>
          </div>

          <div className="rounded-xl border border-gray-200 bg-white p-4 shadow-sm">
            <h2 className="mb-3 text-sm font-semibold text-gray-900">Interview Context</h2>
            <div className="space-y-3 text-sm text-gray-600">
              <div>
                <p className="text-xs font-medium uppercase tracking-wide text-gray-400">Resume</p>
                <p className="mt-1 font-medium text-gray-800">{uploadedFile?.name || 'No file uploaded'}</p>
                {uploadedFile && (
                  <p className="text-xs text-gray-500">File size: {formatFileSize(uploadedFile.size)}</p>
                )}
              </div>

              <div>
                <p className="text-xs font-medium uppercase tracking-wide text-gray-400">Company</p>
                <p className="mt-1 text-gray-800">{companyName || 'Not provided'}</p>
              </div>

              <div>
                <p className="text-xs font-medium uppercase tracking-wide text-gray-400">Job Title</p>
                <p className="mt-1 text-gray-800">{jobTitle || 'Not provided'}</p>
              </div>

              <div>
                <p className="text-xs font-medium uppercase tracking-wide text-gray-400">JD Summary</p>
                <p className="mt-1 leading-relaxed text-gray-600">{summarizeText(jobDescription)}</p>
              </div>
            </div>
          </div>

          <div className="rounded-xl border border-gray-200 bg-white p-4 shadow-sm">
            <InterviewProgressBar
              current={Math.min(totalQuestions, currentQuestionIndex + 1)}
              total={totalQuestions}
            />
          </div>

          <div className="space-y-3 pt-2">
            <button
              onClick={onBackToMatch}
              className="w-full rounded-lg border border-gray-300 px-4 py-2.5 text-sm font-medium text-gray-700 transition-colors hover:bg-gray-50"
            >
              Back to Match
            </button>

            <button
              onClick={onRestartInterview}
              disabled={disableRestart}
              className="w-full rounded-lg bg-blue-600 px-4 py-2.5 text-sm font-medium text-white transition-colors hover:bg-blue-700 disabled:cursor-not-allowed disabled:opacity-50"
            >
              Restart Interview
            </button>
          </div>
        </div>
      </div>
    </aside>
  )
}

InterviewSidebarSummary.propTypes = {
  uploadedFile: PropTypes.shape({
    name: PropTypes.string,
    size: PropTypes.number,
  }),
  companyName: PropTypes.string,
  jobTitle: PropTypes.string,
  jobDescription: PropTypes.string,
  matchScore: PropTypes.number,
  currentQuestionIndex: PropTypes.number.isRequired,
  totalQuestions: PropTypes.number.isRequired,
  isOpen: PropTypes.bool.isRequired,
  onClose: PropTypes.func.isRequired,
  onBackToMatch: PropTypes.func.isRequired,
  onRestartInterview: PropTypes.func.isRequired,
  disableRestart: PropTypes.bool,
}

export default InterviewSidebarSummary
