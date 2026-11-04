/**
 * LoadingState Component Tests
 * 
 * Tests for loading state display, progress tracking, and cancel functionality
 */

import { render, screen, fireEvent } from '@testing-library/react'
import '@testing-library/jest-dom'
import LoadingState, { LoadingStateType } from '../components/LoadingState'

describe('LoadingState Component', () => {
  const mockOnCancel = jest.fn()

  beforeEach(() => {
    jest.clearAllMocks()
  })

  // Rendering Tests
  describe('Rendering', () => {
    test('returns null when isLoading is false', () => {
      render(
        <LoadingState 
          isLoading={false}
        />
      )
      
      expect(screen.queryByRole('status')).not.toBeInTheDocument()
    })

    test('renders loading spinner when isLoading is true', () => {
      render(
        <LoadingState 
          isLoading={true}
        />
      )
      
      expect(screen.getByRole('status')).toBeInTheDocument()
    })

    test('renders default title when isLoading is true', () => {
      render(
        <LoadingState 
          isLoading={true}
        />
      )
      
      expect(screen.getByText('Processing...')).toBeInTheDocument()
    })

    test('renders default description when isLoading is true', () => {
      render(
        <LoadingState 
          isLoading={true}
        />
      )
      
      expect(screen.getByText('Processing your request')).toBeInTheDocument()
    })
  })

  // Loading State Types Tests
  describe('Loading State Types', () => {
    test('displays uploading state correctly', () => {
      render(
        <LoadingState 
          isLoading={true}
          stateType={LoadingStateType.UPLOADING}
        />
      )
      
      expect(screen.getByText('Uploading...')).toBeInTheDocument()
      expect(screen.getByText('Uploading your resume file')).toBeInTheDocument()
    })

    test('displays processing state correctly', () => {
      render(
        <LoadingState 
          isLoading={true}
          stateType={LoadingStateType.PROCESSING}
        />
      )
      
      expect(screen.getByText('Processing...')).toBeInTheDocument()
      expect(screen.getByText('Processing your request')).toBeInTheDocument()
    })

    test('displays analyzing state correctly', () => {
      render(
        <LoadingState 
          isLoading={true}
          stateType={LoadingStateType.ANALYZING}
        />
      )
      
      expect(screen.getByText('Analyzing...')).toBeInTheDocument()
      expect(screen.getByText('AI is analyzing your resume')).toBeInTheDocument()
    })

    test('displays matching state correctly', () => {
      render(
        <LoadingState 
          isLoading={true}
          stateType={LoadingStateType.MATCHING}
        />
      )
      
      expect(screen.getByText('Matching...')).toBeInTheDocument()
      expect(screen.getByText('Calculating how well your resume matches the job')).toBeInTheDocument()
    })

    test('displays optimizing state correctly', () => {
      render(
        <LoadingState 
          isLoading={true}
          stateType={LoadingStateType.OPTIMIZING}
        />
      )
      
      expect(screen.getByText('Optimizing...')).toBeInTheDocument()
      expect(screen.getByText('AI is optimizing your resume')).toBeInTheDocument()
    })
  })

  // Custom Message Tests
  describe('Custom Message', () => {
    test('displays custom message when provided', () => {
      render(
        <LoadingState 
          isLoading={true}
          customMessage="Preparing data..."
        />
      )
      
      expect(screen.getByText('Preparing data...')).toBeInTheDocument()
    })

    test('custom message overrides default title', () => {
      render(
        <LoadingState 
          isLoading={true}
          stateType={LoadingStateType.ANALYZING}
          customMessage="Custom message"
        />
      )
      
      expect(screen.getByText('Custom message')).toBeInTheDocument()
      // Description should still show the default
      expect(screen.getByText('AI is analyzing your resume')).toBeInTheDocument()
    })
  })

  // Progress Bar Tests
  describe('Progress Bar', () => {
    test('does not show progress bar when progress is null', () => {
      render(
        <LoadingState 
          isLoading={true}
          progress={null}
        />
      )
      
      expect(screen.queryByText(/%/)).not.toBeInTheDocument()
    })

    test('shows progress bar when progress is provided', () => {
      render(
        <LoadingState 
          isLoading={true}
          progress={50}
        />
      )
      
      expect(screen.getByText('50%')).toBeInTheDocument()
    })

    test('shows correct progress percentage', () => {
      render(
        <LoadingState 
          isLoading={true}
          progress={75}
        />
      )
      
      expect(screen.getByText('75%')).toBeInTheDocument()
    })

    test('handles 0% progress', () => {
      render(
        <LoadingState 
          isLoading={true}
          progress={0}
        />
      )
      
      expect(screen.getByText('0%')).toBeInTheDocument()
    })

    test('handles 100% progress', () => {
      render(
        <LoadingState 
          isLoading={true}
          progress={100}
        />
      )
      
      expect(screen.getByText('100%')).toBeInTheDocument()
    })
  })

  // Cancel Button Tests
  describe('Cancel Button', () => {
    test('does not show cancel button when onCancel is not provided', () => {
      render(
        <LoadingState 
          isLoading={true}
        />
      )
      
      expect(screen.queryByText('Cancel')).not.toBeInTheDocument()
    })

    test('shows cancel button when onCancel is provided', () => {
      render(
        <LoadingState 
          isLoading={true}
          onCancel={mockOnCancel}
        />
      )
      
      expect(screen.getByText('Cancel')).toBeInTheDocument()
    })

    test('calls onCancel when cancel button is clicked', () => {
      render(
        <LoadingState 
          isLoading={true}
          onCancel={mockOnCancel}
        />
      )
      
      const cancelButton = screen.getByText('Cancel')
      fireEvent.click(cancelButton)
      
      expect(mockOnCancel).toHaveBeenCalledTimes(1)
    })
  })

  // Accessibility Tests
  describe('Accessibility', () => {
    test('has role="status" attribute', () => {
      render(
        <LoadingState 
          isLoading={true}
        />
      )
      
      expect(screen.getByRole('status')).toBeInTheDocument()
    })

    test('has aria-live="polite" attribute', () => {
      render(
        <LoadingState 
          isLoading={true}
        />
      )
      
      expect(screen.getByRole('status')).toHaveAttribute('aria-live', 'polite')
    })

    test('cancel button has aria-label', () => {
      render(
        <LoadingState 
          isLoading={true}
          onCancel={mockOnCancel}
        />
      )
      
      const cancelButton = screen.getByText('Cancel')
      expect(cancelButton).toHaveAttribute('aria-label', 'Cancel current operation')
    })
  })

  // Edge Cases
  describe('Edge Cases', () => {
    test('handles invalid stateType gracefully', () => {
      render(
        <LoadingState 
          isLoading={true}
          stateType="invalid-type"
        />
      )
      
      // Should fall back to processing state
      expect(screen.getByText('Processing...')).toBeInTheDocument()
    })

    test('ignores progress values outside 0-100 range', () => {
      render(
        <LoadingState 
          isLoading={true}
          progress={-1}
        />
      )
      
      // Negative progress should not show progress bar
      expect(screen.queryByText(/%/)).not.toBeInTheDocument()
    })

    test('ignores progress greater than 100', () => {
      render(
        <LoadingState 
          isLoading={true}
          progress={150}
        />
      )
      
      // Progress > 100 should not show progress bar
      expect(screen.queryByText(/%/)).not.toBeInTheDocument()
    })
  })
})
