/* eslint-disable react/prop-types, react-hooks/exhaustive-deps */
import { fireEvent, render, screen, waitFor } from '@testing-library/react'
import '@testing-library/jest-dom'
import ResumeAnalysisPage from '../pages/ResumeAnalysisPage'

const mockUploadResume = jest.fn()
const mockAnalysisRequest = jest.fn()
const mockStartInterviewSession = jest.fn()
const mockResetInterview = jest.fn()

jest.mock('../utils/api', () => ({
  uploadResume: (...args) => mockUploadResume(...args),
  optimizeResume: jest.fn(),
}))

jest.mock('../hooks/useMockInterview', () => ({
  useMockInterview: () => ({
    hasActiveInterview: false,
    error: null,
    isCompleted: false,
    isStarting: false,
    startInterviewSession: mockStartInterviewSession,
    resetInterview: mockResetInterview,
  }),
}))

jest.mock('../components/Sidebar', () => function MockSidebar({
  onFileSelect,
  onUpload,
  onJobDescriptionChange,
  onAnalyze,
  canAnalyze,
}) {
  return (
    <div>
      <button onClick={() => onFileSelect(new File(['resume'], 'resume.pdf'))}>Select resume</button>
      <button onClick={onUpload}>Upload resume</button>
      <label htmlFor="test-job-description">Job Description</label>
      <textarea
        id="test-job-description"
        onChange={(event) => onJobDescriptionChange(event.target.value)}
      />
      <button onClick={onAnalyze} disabled={!canAnalyze}>Match Resume</button>
    </div>
  )
})

jest.mock('../components/AnalysisOutput', () => {
  const React = jest.requireActual('react')

  return function MockAnalysisOutput({ analyzeSignal, onMatchScoreUpdate }) {
    const [hasResult, setHasResult] = React.useState(false)

    React.useEffect(() => {
      if (analyzeSignal > 0) {
        mockAnalysisRequest()
        setHasResult(true)
        onMatchScoreUpdate(82)
      }
    }, [analyzeSignal])

    return <div>{hasResult ? 'Persisted match result' : 'No result'}</div>
  }
})

jest.mock('../components/ResumePreview', () => function MockResumePreview({
  canStartMockInterview,
  mockInterviewDisabledReason,
  onStartMockInterview,
}) {
  return (
    <div>
      <button onClick={onStartMockInterview} disabled={!canStartMockInterview}>
        Start Mock Interview
      </button>
      {mockInterviewDisabledReason && <span>{mockInterviewDisabledReason}</span>}
    </div>
  )
})

jest.mock('../components/interview/MockInterviewShell', () => function MockInterviewShell({ onBackToMatch }) {
  return <button onClick={onBackToMatch}>Back to Match</button>
})

describe('ResumeAnalysisPage mock interview navigation', () => {
  beforeEach(() => {
    jest.clearAllMocks()
    mockUploadResume.mockResolvedValue({
      status: 'ok',
      data: {
        session_id: 'session-123',
        expire_at: '2099-01-01T00:00:00Z',
      },
    })
    mockStartInterviewSession.mockResolvedValue({ interview_id: 'mock-123' })
  })

  test('keeps match results mounted when returning from the interview', async () => {
    render(<ResumeAnalysisPage />)

    fireEvent.click(screen.getByRole('button', { name: 'Select resume' }))
    fireEvent.change(screen.getByLabelText('Job Description'), {
      target: { value: 'Senior backend engineer role' },
    })
    fireEvent.click(screen.getByRole('button', { name: 'Upload resume' }))

    await waitFor(() => expect(mockUploadResume).toHaveBeenCalledTimes(1))
    fireEvent.click(screen.getByRole('button', { name: 'Match Resume' }))

    await waitFor(() => expect(screen.getByText('Persisted match result')).toBeInTheDocument())
    expect(mockAnalysisRequest).toHaveBeenCalledTimes(1)

    fireEvent.click(screen.getByRole('button', { name: 'Start Mock Interview' }))
    await waitFor(() => expect(screen.getByRole('button', { name: 'Back to Match' })).toBeInTheDocument())
    fireEvent.click(screen.getByRole('button', { name: 'Back to Match' }))

    expect(screen.getByText('Persisted match result')).toBeInTheDocument()
    expect(mockAnalysisRequest).toHaveBeenCalledTimes(1)
  })
})
