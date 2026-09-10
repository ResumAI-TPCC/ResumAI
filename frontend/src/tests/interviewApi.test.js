import { pollJobResult } from '../utils/api'
import {
  startInterview,
  submitInterviewAnswer,
} from '../utils/interviewApi'

jest.mock('../utils/api', () => ({
  pollJobResult: jest.fn(),
}))

jest.mock('../config/env.js', () => ({
  ENV: { API_BASE_URL: 'http://test/api' },
}))

const questionResult = {
  interview_id: 'mock-123',
  questions: [
    {
      id: 'q1',
      type: 'self_intro',
      label: 'Self Introduction',
      question: 'Please introduce yourself.',
      focus_areas: ['role fit'],
    },
  ],
}

const feedbackResult = {
  question_id: 'q1',
  score: 80,
  strengths: ['Relevant example'],
  weaknesses: ['Add more detail'],
  suggestions: ['Use STAR'],
  improved_answer: 'Improved answer',
  jd_alignment: 'Good alignment',
  scoring_breakdown: {
    relevance: 24,
    specificity: 20,
    structure: 16,
    impact: 12,
    communication: 8,
  },
}

function acceptedResponse(jobId) {
  return {
    ok: true,
    status: 202,
    json: jest.fn().mockResolvedValue({
      code: 202,
      status: 'ok',
      data: { job_id: jobId, status: 'pending' },
    }),
  }
}

describe('mock interview async job flow', () => {
  beforeEach(() => {
    jest.clearAllMocks()
    globalThis.fetch = jest.fn()
  })

  test('starts an interview by submitting and polling a queued job', async () => {
    globalThis.fetch.mockResolvedValueOnce(acceptedResponse('start-job-1'))
    pollJobResult.mockResolvedValueOnce(questionResult)

    const result = await startInterview({
      session_id: 'session-1',
      job_description: 'Python API engineer',
    })

    expect(globalThis.fetch).toHaveBeenCalledWith(
      expect.stringContaining('/interviews/start'),
      expect.objectContaining({ method: 'POST' })
    )
    expect(pollJobResult).toHaveBeenCalledWith('start-job-1')
    expect(result.interview_id).toBe('mock-123')
    expect(result.questions).toHaveLength(1)
  })

  test('evaluates an answer by submitting and polling a queued job', async () => {
    globalThis.fetch
      .mockResolvedValueOnce(acceptedResponse('start-job-2'))
      .mockResolvedValueOnce(acceptedResponse('answer-job-1'))
    pollJobResult
      .mockResolvedValueOnce(questionResult)
      .mockResolvedValueOnce(feedbackResult)

    await startInterview({
      session_id: 'session-2',
      job_description: 'Python API engineer',
    })
    const feedback = await submitInterviewAnswer({
      interview_id: 'mock-123',
      question_id: 'q1',
      answer: 'I built a Python API.',
    })

    expect(globalThis.fetch).toHaveBeenLastCalledWith(
      expect.stringContaining('/interviews/answer'),
      expect.objectContaining({ method: 'POST' })
    )
    expect(pollJobResult).toHaveBeenLastCalledWith('answer-job-1')
    expect(feedback.score).toBe(80)
  })

  test('surfaces a failed queued job', async () => {
    globalThis.fetch.mockResolvedValueOnce(acceptedResponse('start-job-failed'))
    pollJobResult.mockRejectedValueOnce(new Error('Job processing failed'))

    await expect(startInterview({
      session_id: 'session-3',
      job_description: 'Python API engineer',
    })).rejects.toThrow('Job processing failed')
  })
})
