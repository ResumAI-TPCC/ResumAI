import { act, fireEvent, render, renderHook, screen } from '@testing-library/react'
import '@testing-library/jest-dom'
import ResumePreview from '../components/ResumePreview'
import InterviewQuestionPanel from '../components/interview/InterviewQuestionPanel'
import { useMockInterview } from '../hooks/useMockInterview'
import {
  getInterviewReport,
  startInterview,
  submitInterviewAnswer,
} from '../utils/interviewApi'

jest.mock('../utils/interviewApi', () => ({
  getInterviewReport: jest.fn(),
  startInterview: jest.fn(),
  submitInterviewAnswer: jest.fn(),
}))

const question = {
  id: 'q1',
  type: 'self_intro',
  label: 'Self Introduction',
  prompt: 'Tell me about yourself.',
  focus_areas: [],
}

describe('mock interview review fixes', () => {
  beforeEach(() => {
    jest.clearAllMocks()
  })

  test('explains why mock interview is disabled without a JD', () => {
    render(
      <ResumePreview
        uploadedFile={new File(['resume'], 'resume.pdf')}
        matchScore={80}
        actionsEnabled
        canStartMockInterview={false}
        mockInterviewDisabledReason="Add a job description to start a mock interview."
        onStartMockInterview={jest.fn()}
        isOpen
      />
    )

    const button = screen.getByRole('button', { name: 'Start Mock Interview' })
    expect(button).toBeDisabled()
    expect(button).toHaveAttribute('aria-describedby', 'mock-interview-disabled-reason')
    expect(screen.getByText('Add a job description to start a mock interview.')).toBeInTheDocument()
  })

  test('offers back and retry actions when startup produces no question', () => {
    const onBackToMatch = jest.fn()
    const onRestartInterview = jest.fn()

    render(
      <InterviewQuestionPanel
        currentQuestion={null}
        currentQuestionIndex={0}
        totalQuestions={0}
        draftAnswer=""
        onDraftAnswerChange={jest.fn()}
        onSubmitAnswer={jest.fn()}
        onNextQuestion={jest.fn()}
        isStarting={false}
        isSubmitting={false}
        isGeneratingReport={false}
        isCompleted={false}
        currentFeedback={null}
        submittedAnswer=""
        error="Unable to reach the interview service."
        onBackToMatch={onBackToMatch}
        onRestartInterview={onRestartInterview}
      />
    )

    fireEvent.click(screen.getByRole('button', { name: 'Back to Match' }))
    fireEvent.click(screen.getByRole('button', { name: 'Retry' }))
    expect(onBackToMatch).toHaveBeenCalledTimes(1)
    expect(onRestartInterview).toHaveBeenCalledTimes(1)
  })

  test('records a start failure without rejecting the click-handler promise', async () => {
    startInterview.mockRejectedValue(new Error('Start failed'))
    const { result } = renderHook(() => useMockInterview())

    await act(async () => {
      await expect(result.current.startInterviewSession({ session_id: 'session-123' }))
        .resolves.toBeNull()
    })

    expect(result.current.error).toBe('Start failed')
  })

  test('records answer and report failures without rejecting click-handler promises', async () => {
    startInterview.mockResolvedValue({ interview_id: 'mock-123', questions: [question] })
    submitInterviewAnswer.mockRejectedValue(new Error('Answer failed'))
    getInterviewReport.mockRejectedValue(new Error('Report failed'))
    const { result } = renderHook(() => useMockInterview())

    await act(async () => {
      await result.current.startInterviewSession({ session_id: 'session-123' })
    })
    act(() => result.current.updateDraftAnswer('A detailed answer'))

    await act(async () => {
      await expect(result.current.submitCurrentAnswer()).resolves.toBeNull()
    })
    expect(result.current.error).toBe('Answer failed')

    submitInterviewAnswer.mockResolvedValue({ score: 80 })
    await act(async () => {
      await result.current.submitCurrentAnswer()
    })
    await act(async () => {
      await expect(result.current.goToNextStep()).resolves.toBeNull()
    })
    expect(result.current.error).toBe('Report failed')
  })
})
