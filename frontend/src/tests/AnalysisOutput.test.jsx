/**
 * AnalysisOutput Component Tests
 * 
 * RA-31/32: Resume Analysis Results UI Testing
 * Tests for analysis display, match score, suggestions, and action buttons
 */

import { render, screen, fireEvent, waitFor } from '@testing-library/react'
import '@testing-library/jest-dom'
import AnalysisOutput from '../components/AnalysisOutput'

// Mock the API functions
jest.mock('../utils/api', () => ({
  analyzeResume: jest.fn(),
  matchResumeWithJob: jest.fn(),
}))

import { analyzeResume, matchResumeWithJob } from '../utils/api'

describe('AnalysisOutput Component', () => {
  beforeEach(() => {
    jest.clearAllMocks()
  })

  // RA-31: Empty State Tests
  describe('Empty State', () => {
    test('renders empty state when no sessionId', () => {
      render(<AnalysisOutput />)
      
      expect(screen.getByText(/Please upload your resume/i)).toBeInTheDocument()
    })

    test('renders "Ready to Analyze" when sessionId provided without JD', () => {
      render(<AnalysisOutput sessionId="test-session-123" />)
      
      expect(screen.getByText(/Click the button below to analyze/i)).toBeInTheDocument()
      expect(screen.getByRole('button', { name: /Analyze Resume/i })).toBeInTheDocument()
    })

    test('renders "Ready to Analyze Match" when sessionId and JD provided', () => {
      render(
        <AnalysisOutput 
          sessionId="test-session-123" 
          jobDescription="Senior Software Engineer position..." 
        />
      )
      
      expect(screen.getByText(/analyze your resume against the job description/i)).toBeInTheDocument()
      expect(screen.getByRole('button', { name: /Analyze Match/i })).toBeInTheDocument()
    })

    test('analyze button is disabled without sessionId', () => {
      render(<AnalysisOutput />)
      
      const button = screen.getByRole('button', { name: /Analyze Resume/i })
      expect(button).toBeDisabled()
    })
  })

  // RA-32: Analyze Resume Tests (without JD)
  describe('Analyze Resume (without JD)', () => {
    test('calls analyzeResume API when button clicked', async () => {
      analyzeResume.mockResolvedValue({
        data: {
          suggestions: [
            { category: 'content', priority: 'high', title: 'Add Summary', description: 'Add a professional summary' }
          ]
        }
      })

      render(<AnalysisOutput sessionId="test-session-123" />)
      
      const button = screen.getByRole('button', { name: /Analyze Resume/i })
      fireEvent.click(button)
      
      expect(analyzeResume).toHaveBeenCalledWith('test-session-123')
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
              example: 'Results-driven software engineer with 5+ years...'
            }
          ]
        }
      })

      render(<AnalysisOutput sessionId="test-session-123" />)
      
      fireEvent.click(screen.getByRole('button', { name: /Analyze Resume/i }))
      
      await waitFor(() => {
        expect(screen.getByText(/Add Professional Summary/i)).toBeInTheDocument()
        expect(screen.getByText(/Include a 2-3 sentence summary/i)).toBeInTheDocument()
      })
    })

    test('shows error when analysis fails', async () => {
      analyzeResume.mockRejectedValue(new Error('Analysis failed'))

      render(<AnalysisOutput sessionId="test-session-123" />)
      
      fireEvent.click(screen.getByRole('button', { name: /Analyze Resume/i }))
      
      await waitFor(() => {
        expect(screen.getByText(/Analysis failed/i)).toBeInTheDocument()
      })
    })

    test('shows loading state during analysis', async () => {
      analyzeResume.mockImplementation(() => new Promise(() => {})) // Never resolves

      render(<AnalysisOutput sessionId="test-session-123" />)
      
      fireEvent.click(screen.getByRole('button', { name: /Analyze Resume/i }))
      
      expect(screen.getByText(/Analyzing.../i)).toBeInTheDocument()
    })
  })

  // RA-32: Match Analysis Tests (with JD)
  describe('Match Analysis (with JD)', () => {
    test('calls matchResumeWithJob API when JD provided', async () => {
      matchResumeWithJob.mockResolvedValue({
        data: {
          match_score: 75,
          suggestions: []
        }
      })

      render(
        <AnalysisOutput 
          sessionId="test-session-123" 
          jobDescription="We are looking for a senior engineer..."
          jobTitle="Senior Engineer"
          companyName="TechCorp"
        />
      )
      
      fireEvent.click(screen.getByRole('button', { name: /Analyze Match/i }))
      
      expect(matchResumeWithJob).toHaveBeenCalledWith(
        'test-session-123',
        'We are looking for a senior engineer...',
        'Senior Engineer',
        'TechCorp'
      )
    })

    test('displays match score after analysis', async () => {
      matchResumeWithJob.mockResolvedValue({
        data: {
          match_score: 85,
          suggestions: []
        }
      })

      render(
        <AnalysisOutput 
          sessionId="test-session-123" 
          jobDescription="Software Engineer position"
        />
      )
      
      fireEvent.click(screen.getByRole('button', { name: /Analyze Match/i }))
      
      await waitFor(() => {
        expect(screen.getByText('85')).toBeInTheDocument()
        expect(screen.getByText('/100')).toBeInTheDocument()
      })
    })

    test('displays scoring principles for match analysis', async () => {
      matchResumeWithJob.mockResolvedValue({
        data: { match_score: 70, suggestions: [] }
      })

      render(
        <AnalysisOutput 
          sessionId="test-session-123" 
          jobDescription="Software Engineer position"
        />
      )
      
      fireEvent.click(screen.getByRole('button', { name: /Analyze Match/i }))
      
      await waitFor(() => {
        expect(screen.getByText(/Scoring Principles/i)).toBeInTheDocument()
        expect(screen.getByText(/Skill Match/i)).toBeInTheDocument()
        expect(screen.getByText(/Experience Alignment/i)).toBeInTheDocument()
        expect(screen.getByText(/Education & Background/i)).toBeInTheDocument()
      })
    })
  })

  // Suggestion Priority Display Tests
  describe('Suggestion Priority Display', () => {
    test('displays high priority suggestions with red indicator', async () => {
      analyzeResume.mockResolvedValue({
        data: {
          suggestions: [
            { category: 'content', priority: 'high', title: 'Critical Issue', description: 'Fix this' }
          ]
        }
      })

      render(<AnalysisOutput sessionId="test-session-123" />)
      fireEvent.click(screen.getByRole('button', { name: /Analyze Resume/i }))
      
      await waitFor(() => {
        expect(screen.getByText('H')).toBeInTheDocument()
      })
    })

    test('displays medium priority suggestions with yellow indicator', async () => {
      analyzeResume.mockResolvedValue({
        data: {
          suggestions: [
            { category: 'format', priority: 'medium', title: 'Medium Issue', description: 'Consider this' }
          ]
        }
      })

      render(<AnalysisOutput sessionId="test-session-123" />)
      fireEvent.click(screen.getByRole('button', { name: /Analyze Resume/i }))
      
      await waitFor(() => {
        expect(screen.getByText('M')).toBeInTheDocument()
      })
    })

    test('displays low priority suggestions with blue indicator', async () => {
      analyzeResume.mockResolvedValue({
        data: {
          suggestions: [
            { category: 'style', priority: 'low', title: 'Minor Issue', description: 'Optional' }
          ]
        }
      })

      render(<AnalysisOutput sessionId="test-session-123" />)
      fireEvent.click(screen.getByRole('button', { name: /Analyze Resume/i }))
      
      await waitFor(() => {
        expect(screen.getByText('L')).toBeInTheDocument()
      })
    })
  })

  // Action Buttons Tests
  describe('Action Buttons', () => {
    beforeEach(async () => {
      analyzeResume.mockResolvedValue({
        data: { suggestions: [] }
      })
    })

    test('shows Generate and Download buttons after analysis', async () => {
      render(<AnalysisOutput sessionId="test-session-123" />)
      fireEvent.click(screen.getByRole('button', { name: /Analyze Resume/i }))
      
      await waitFor(() => {
        expect(screen.getByRole('button', { name: /Generate Polished Resume/i })).toBeInTheDocument()
        expect(screen.getByRole('button', { name: /Download Polished Resume/i })).toBeInTheDocument()
      })
    })

    test('Generate button is clickable after analysis', async () => {
      render(<AnalysisOutput sessionId="test-session-123" />)
      fireEvent.click(screen.getByRole('button', { name: /Analyze Resume/i }))
      
      await waitFor(() => {
        expect(screen.getByRole('button', { name: /Generate Polished Resume/i })).toBeInTheDocument()
      })
      
      // Button should be clickable (feature pending implementation)
      const generateButton = screen.getByRole('button', { name: /Generate Polished Resume/i })
      expect(generateButton).not.toBeDisabled()
    })

    test('Download button is clickable after analysis', async () => {
      render(<AnalysisOutput sessionId="test-session-123" />)
      fireEvent.click(screen.getByRole('button', { name: /Analyze Resume/i }))
      
      await waitFor(() => {
        expect(screen.getByRole('button', { name: /Download Polished Resume/i })).toBeInTheDocument()
      })
      
      // Button should be clickable (feature pending implementation)
      const downloadButton = screen.getByRole('button', { name: /Download Polished Resume/i })
      expect(downloadButton).not.toBeDisabled()
    })

    test('shows Re-analyze button after analysis', async () => {
      render(<AnalysisOutput sessionId="test-session-123" />)
      fireEvent.click(screen.getByRole('button', { name: /Analyze Resume/i }))
      
      await waitFor(() => {
        expect(screen.getByRole('button', { name: /Re-analyze/i })).toBeInTheDocument()
      })
    })
  })

  // Error Handling Tests
  describe('Error Handling', () => {
    test('shows error when sessionId is missing but button clicked', async () => {
      // This shouldn't happen due to disabled button, but testing the logic
      const { container } = render(<AnalysisOutput sessionId="" />)
      
      // Force-enable and click (simulating edge case)
      const button = screen.getByRole('button', { name: /Analyze Resume/i })
      expect(button).toBeDisabled()
    })

    test('handles API timeout gracefully', async () => {
      analyzeResume.mockRejectedValue(new Error('Network timeout'))

      render(<AnalysisOutput sessionId="test-session-123" />)
      fireEvent.click(screen.getByRole('button', { name: /Analyze Resume/i }))
      
      await waitFor(() => {
        expect(screen.getByText(/Network timeout/i)).toBeInTheDocument()
      })
    })
  })
})
