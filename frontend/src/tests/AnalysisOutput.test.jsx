import { render, screen, waitFor } from '@testing-library/react'
import '@testing-library/jest-dom'
import AnalysisOutput from '../components/AnalysisOutput'

jest.mock('../utils/api', () => ({
  analyzeResume: jest.fn(),
  matchResumeWithJob: jest.fn(),
}))

import { analyzeResume, matchResumeWithJob } from '../utils/api'

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
        expect(analyzeResume).toHaveBeenCalledWith('test-session-123')
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
          'TechCorp'
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
  })
})

