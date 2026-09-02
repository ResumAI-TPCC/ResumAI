/**
 * AnalysisOutput Component Tests
 * 
 * Tests for analysis output display, loading state, error handling, and cancel functionality
 */

import { render, screen, waitFor, fireEvent } from '@testing-library/react'
import '@testing-library/jest-dom'
import AnalysisOutput from '../components/AnalysisOutput'
import { ApiError, ErrorTypes } from '../utils/api'

// Mock the API module
jest.mock('../utils/api', () => ({
  analyzeResume: jest.fn(),
  matchResumeWithJob: jest.fn(),
  ApiError: class ApiError extends Error {
    constructor(message, type) {
      super(message)
      this.name = 'ApiError'
      this.type = type
    }
  },
  ErrorTypes: {
    NETWORK_ERROR: 'NETWORK_ERROR',
    TIMEOUT_ERROR: 'TIMEOUT_ERROR',
    SERVER_ERROR: 'SERVER_ERROR',
    CLIENT_ERROR: 'CLIENT_ERROR',
    CANCELLED: 'CANCELLED',
    VALIDATION_ERROR: 'VALIDATION_ERROR',
    UNKNOWN_ERROR: 'UNKNOWN_ERROR',
  },
}))

import { analyzeResume, matchResumeWithJob } from '../utils/api'

function mockPendingApiCall(mockFn, resolveValue) {
  let resolvePromise
  mockFn.mockImplementation((...args) => {
    const controller = args[args.length - 1]
    return new Promise((resolve, reject) => {
      if (controller?.signal) {
        controller.signal.addEventListener('abort', () => {
          reject(new ApiError('Request cancelled', ErrorTypes.CANCELLED))
        }, { once: true })
      }
      resolvePromise = resolve
    })
  })
  return (value = resolveValue) => resolvePromise(value)
}

describe('AnalysisOutput Component', () => {
  beforeEach(() => {
    jest.clearAllMocks()
  })

  describe('Empty State', () => {
    test('renders upload hint when analysis is not available', () => {
      render(<AnalysisOutput />)
      expect(screen.getByText(/Please upload your resume to get started/i)).toBeInTheDocument()
    })

    test('renders left-panel analyze hint when analysis is available without JD', () => {
      render(<AnalysisOutput sessionId="test-session-123" canAnalyze analyzeSignal={0} />)
      expect(screen.getByText(/Ready to Analyze Resume/i)).toBeInTheDocument()
      expect(screen.getByText(/Use the Analyze button in the left panel/i)).toBeInTheDocument()
      expect(screen.queryByRole('button', { name: /Analyze Resume/i })).not.toBeInTheDocument()
    })

    test('renders left-panel match hint when JD exists', () => {
      render(
        <AnalysisOutput
          sessionId="test-session-123"
          canAnalyze
          jobDescription="Senior Software Engineer position"
          analyzeSignal={0}
        />
      )

      expect(screen.getByText(/Ready to Match Resume/i)).toBeInTheDocument()
      expect(screen.getByText(/Use the Match Resume button in the left panel/i)).toBeInTheDocument()
    })
  })

  describe('Loading State', () => {
    test('shows loading spinner when analysis is in progress', async () => {
      const finishRequest = mockPendingApiCall(analyzeResume, { data: { suggestions: [] } })

      const props = {
        sessionId: 'test-session-123',
        canAnalyze: true,
      }
      const { rerender } = render(<AnalysisOutput {...props} analyzeSignal={0} />)
      rerender(<AnalysisOutput {...props} analyzeSignal={1} />)

      // Check for loading state
      await waitFor(() => {
        expect(screen.getByRole('status')).toBeInTheDocument()
      })

      // Clean up by resolving the promise
      finishRequest()
    })

    test('shows analyzing message when analyzing without JD', async () => {
      const finishRequest = mockPendingApiCall(analyzeResume, { data: { suggestions: [] } })

      const props = {
        sessionId: 'test-session-123',
        canAnalyze: true,
      }
      const { rerender } = render(<AnalysisOutput {...props} analyzeSignal={0} />)
      rerender(<AnalysisOutput {...props} analyzeSignal={1} />)

      await waitFor(() => {
        expect(screen.getByText(/分析中.../i)).toBeInTheDocument()
      })

      finishRequest()
    })

    test('shows matching message when matching with JD', async () => {
      const finishRequest = mockPendingApiCall(matchResumeWithJob, { data: { match_score: 75, suggestions: [] } })

      const props = {
        sessionId: 'test-session-123',
        canAnalyze: true,
        jobDescription: 'Software Engineer position',
      }
      const { rerender } = render(<AnalysisOutput {...props} analyzeSignal={0} />)
      rerender(<AnalysisOutput {...props} analyzeSignal={1} />)

      await waitFor(() => {
        expect(screen.getByText(/匹配中.../i)).toBeInTheDocument()
      })

      finishRequest()
    })
  })

  describe('Analyze Resume (without JD)', () => {
    test('calls analyzeResume API when analyzeSignal increases', async () => {
      analyzeResume.mockResolvedValue({ data: { suggestions: [] } })

      const props = {
        sessionId: 'test-session-123',
        canAnalyze: true,
      }

      const { rerender } = render(<AnalysisOutput {...props} analyzeSignal={0} />)
      rerender(<AnalysisOutput {...props} analyzeSignal={1} />)

      await waitFor(() => {
        expect(analyzeResume).toHaveBeenCalledWith('test-session-123', expect.anything())
      })
    })

    test('displays suggestions after analysis', async () => {
      analyzeResume.mockResolvedValue({
        data: {
          suggestions: [
            {
              category: 'content',
              priority: 'high',
              title: 'Add Professional Summary',
              description: 'Include a 2-3 sentence summary',
            },
          ],
        },
      })

      const props = {
        sessionId: 'test-session-123',
        canAnalyze: true,
      }
      const { rerender } = render(<AnalysisOutput {...props} analyzeSignal={0} />)
      rerender(<AnalysisOutput {...props} analyzeSignal={1} />)

      await waitFor(() => {
        expect(screen.getByText(/Add Professional Summary/i)).toBeInTheDocument()
        expect(screen.getByText(/Include a 2-3 sentence summary/i)).toBeInTheDocument()
      })
    })

    test('shows error when analysis fails', async () => {
      analyzeResume.mockRejectedValue(new Error('Analysis failed'))

      const props = {
        sessionId: 'test-session-123',
        canAnalyze: true,
      }
      const { rerender } = render(<AnalysisOutput {...props} analyzeSignal={0} />)
      rerender(<AnalysisOutput {...props} analyzeSignal={1} />)

      await waitFor(() => {
        expect(screen.getByText(/Analysis failed/i)).toBeInTheDocument()
      })
    })

    test('invokes analyze status callback during analyze lifecycle', async () => {
      const onAnalyzeStatusChange = jest.fn()
      analyzeResume.mockResolvedValue({ data: { suggestions: [] } })

      const props = {
        sessionId: 'test-session-123',
        canAnalyze: true,
        onAnalyzeStatusChange,
      }
      const { rerender } = render(<AnalysisOutput {...props} analyzeSignal={0} />)
      rerender(<AnalysisOutput {...props} analyzeSignal={1} />)

      await waitFor(() => {
        expect(onAnalyzeStatusChange).toHaveBeenCalledWith(true)
        expect(onAnalyzeStatusChange).toHaveBeenCalledWith(false)
      })
    })
  })

  describe('Match Analysis (with JD)', () => {
    test('calls matchResumeWithJob API when JD is provided', async () => {
      matchResumeWithJob.mockResolvedValue({
        data: {
          match_score: 75,
          suggestions: [],
        },
      })

      const props = {
        sessionId: 'test-session-123',
        canAnalyze: true,
        jobDescription: 'We are looking for a senior engineer...',
        jobTitle: 'Senior Engineer',
        companyName: 'TechCorp',
      }
      const { rerender } = render(<AnalysisOutput {...props} analyzeSignal={0} />)
      rerender(<AnalysisOutput {...props} analyzeSignal={1} />)

      await waitFor(() => {
        expect(matchResumeWithJob).toHaveBeenCalledWith(
          'test-session-123',
          'We are looking for a senior engineer...',
          'Senior Engineer',
          'TechCorp',
          expect.anything()
        )
      })
    })

    test('displays match analysis sections after match request', async () => {
      matchResumeWithJob.mockResolvedValue({
        data: {
          match_score: 70,
          suggestions: [],
        },
      })

      const props = {
        sessionId: 'test-session-123',
        canAnalyze: true,
        jobDescription: 'Software Engineer position',
      }
      const { rerender } = render(<AnalysisOutput {...props} analyzeSignal={0} />)
      rerender(<AnalysisOutput {...props} analyzeSignal={1} />)

      await waitFor(() => {
        expect(screen.getByText(/Scoring Principles/i)).toBeInTheDocument()
        expect(screen.getByText(/Analysis Reasoning/i)).toBeInTheDocument()
      })
    })

    test('passes match score to parent callback', async () => {
      const onMatchScoreUpdate = jest.fn()
      matchResumeWithJob.mockResolvedValue({
        data: {
          match_score: 85,
          suggestions: [],
        },
      })

      const props = {
        sessionId: 'test-session-123',
        canAnalyze: true,
        jobDescription: 'Software Engineer position',
        onMatchScoreUpdate,
      }
      const { rerender } = render(<AnalysisOutput {...props} analyzeSignal={0} />)
      rerender(<AnalysisOutput {...props} analyzeSignal={1} />)

      await waitFor(() => {
        expect(onMatchScoreUpdate).toHaveBeenCalledWith(85)
      })
    })
  })

  describe('Suggestion Priority Display', () => {
    test('displays high priority badge with readable label', async () => {
      analyzeResume.mockResolvedValue({
        data: {
          suggestions: [{ category: 'content', priority: 'high', title: 'Critical Issue', description: 'Fix this' }],
        },
      })

      const { rerender } = render(<AnalysisOutput sessionId="test-session-123" canAnalyze analyzeSignal={0} />)
      rerender(<AnalysisOutput sessionId="test-session-123" canAnalyze analyzeSignal={1} />)

      await waitFor(() => {
        expect(screen.getByText('High Priority')).toBeInTheDocument()
      })
    })

    test('displays medium priority badge with readable label', async () => {
      analyzeResume.mockResolvedValue({
        data: {
          suggestions: [{ category: 'format', priority: 'medium', title: 'Medium Issue', description: 'Consider this' }],
        },
      })

      const { rerender } = render(<AnalysisOutput sessionId="test-session-123" canAnalyze analyzeSignal={0} />)
      rerender(<AnalysisOutput sessionId="test-session-123" canAnalyze analyzeSignal={1} />)

      await waitFor(() => {
        expect(screen.getByText('Medium Priority')).toBeInTheDocument()
      })
    })

    test('displays low priority badge with readable label', async () => {
      analyzeResume.mockResolvedValue({
        data: {
          suggestions: [{ category: 'style', priority: 'low', title: 'Minor Issue', description: 'Optional' }],
        },
      })

      const { rerender } = render(<AnalysisOutput sessionId="test-session-123" canAnalyze analyzeSignal={0} />)
      rerender(<AnalysisOutput sessionId="test-session-123" canAnalyze analyzeSignal={1} />)

      await waitFor(() => {
        expect(screen.getByText('Low Priority')).toBeInTheDocument()
      })
    })
  })

  describe('Error Handling', () => {
    test('shows error when analyze is triggered without sessionId', async () => {
      const { rerender } = render(<AnalysisOutput analyzeSignal={0} />)
      rerender(<AnalysisOutput analyzeSignal={1} />)

      await waitFor(() => {
        expect(screen.getByText(/Please upload a resume first/i)).toBeInTheDocument()
      })
    })

    test('shows network error with retry button', async () => {
      const networkError = new ApiError('Network error occurred', ErrorTypes.NETWORK_ERROR)
      analyzeResume.mockRejectedValue(networkError)

      const props = {
        sessionId: 'test-session-123',
        canAnalyze: true,
      }
      const { rerender } = render(<AnalysisOutput {...props} analyzeSignal={0} />)
      rerender(<AnalysisOutput {...props} analyzeSignal={1} />)

      await waitFor(() => {
        expect(screen.getByText(/网络错误/i)).toBeInTheDocument()
        expect(screen.getByText(/请检查您的网络连接后重试/i)).toBeInTheDocument()
      })
    })

    test('shows timeout error with retry button', async () => {
      const timeoutError = new ApiError('Request timed out', ErrorTypes.TIMEOUT_ERROR)
      analyzeResume.mockRejectedValue(timeoutError)

      const props = {
        sessionId: 'test-session-123',
        canAnalyze: true,
      }
      const { rerender } = render(<AnalysisOutput {...props} analyzeSignal={0} />)
      rerender(<AnalysisOutput {...props} analyzeSignal={1} />)

      await waitFor(() => {
        expect(screen.getByText(/请求超时/i)).toBeInTheDocument()
        expect(screen.getByText(/服务器响应时间过长，请稍后重试/i)).toBeInTheDocument()
      })
    })

    test('shows server error with retry button', async () => {
      const serverError = new ApiError('Server error', ErrorTypes.SERVER_ERROR)
      analyzeResume.mockRejectedValue(serverError)

      const props = {
        sessionId: 'test-session-123',
        canAnalyze: true,
      }
      const { rerender } = render(<AnalysisOutput {...props} analyzeSignal={0} />)
      rerender(<AnalysisOutput {...props} analyzeSignal={1} />)

      await waitFor(() => {
        expect(screen.getByText(/服务器错误/i)).toBeInTheDocument()
        expect(screen.getByText(/服务器暂时不可用，请稍后重试/i)).toBeInTheDocument()
      })
    })

    test('shows cancelled error without retry button', async () => {
      const cancelledError = new ApiError('Request cancelled', ErrorTypes.CANCELLED)
      analyzeResume.mockRejectedValue(cancelledError)

      const props = {
        sessionId: 'test-session-123',
        canAnalyze: true,
      }
      const { rerender } = render(<AnalysisOutput {...props} analyzeSignal={0} />)
      rerender(<AnalysisOutput {...props} analyzeSignal={1} />)

      await waitFor(() => {
        // Use more specific query to match the error title
        expect(screen.getByRole('heading', { name: /已取消/i })).toBeInTheDocument()
        // Cancelled error should not show retry button
        expect(screen.queryByText('重试')).not.toBeInTheDocument()
      })
    })

    test('retry button triggers new analysis', async () => {
      const networkError = new ApiError('Network error occurred', ErrorTypes.NETWORK_ERROR)
      analyzeResume.mockRejectedValueOnce(networkError)
      analyzeResume.mockResolvedValueOnce({ data: { suggestions: [] } })

      const props = {
        sessionId: 'test-session-123',
        canAnalyze: true,
      }
      const { rerender } = render(<AnalysisOutput {...props} analyzeSignal={0} />)
      rerender(<AnalysisOutput {...props} analyzeSignal={1} />)

      // Wait for error to appear
      await waitFor(() => {
        expect(screen.getByText(/网络错误/i)).toBeInTheDocument()
      })

      // Click retry button
      const retryButton = screen.getByText('重试')
      fireEvent.click(retryButton)

      // Verify new API call was made
      await waitFor(() => {
        expect(analyzeResume).toHaveBeenCalledTimes(2)
      })
    })
  })

  describe('Cancel Functionality', () => {
    test('shows cancel button during loading', async () => {
      const finishRequest = mockPendingApiCall(analyzeResume, { data: { suggestions: [] } })

      const props = {
        sessionId: 'test-session-123',
        canAnalyze: true,
      }
      const { rerender } = render(<AnalysisOutput {...props} analyzeSignal={0} />)
      rerender(<AnalysisOutput {...props} analyzeSignal={1} />)

      await waitFor(() => {
        expect(screen.getByText('取消')).toBeInTheDocument()
      })

      finishRequest()
    })

    test('clicking cancel button stops loading', async () => {
      const finishRequest = mockPendingApiCall(analyzeResume, { data: { suggestions: [] } })

      const props = {
        sessionId: 'test-session-123',
        canAnalyze: true,
      }
      const { rerender } = render(<AnalysisOutput {...props} analyzeSignal={0} />)
      rerender(<AnalysisOutput {...props} analyzeSignal={1} />)

      // Wait for loading state
      await waitFor(() => {
        expect(screen.getByText('取消')).toBeInTheDocument()
      })

      // Click cancel
      const cancelButton = screen.getByText('取消')
      fireEvent.click(cancelButton)

      // Loading state should be removed
      await waitFor(() => {
        expect(screen.queryByRole('status')).not.toBeInTheDocument()
      })

      finishRequest()
    })
  })

  describe('Component Cleanup', () => {
    test('cancels pending request on unmount', async () => {
      let capturedController

      analyzeResume.mockImplementation((_sessionId, controller) => {
        capturedController = controller
        return new Promise(() => {})
      })

      const props = {
        sessionId: 'test-session-123',
        canAnalyze: true,
      }
      const { rerender, unmount } = render(<AnalysisOutput {...props} analyzeSignal={0} />)
      rerender(<AnalysisOutput {...props} analyzeSignal={1} />)

      // Wait for loading state to appear
      await waitFor(() => {
        expect(screen.getByRole('status')).toBeInTheDocument()
      })

      // Unmount component
      unmount()

      expect(capturedController.signal.aborted).toBe(true)
    })
  })
})
