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
      
      expect(screen.getByText('处理中...')).toBeInTheDocument()
    })

    test('renders default description when isLoading is true', () => {
      render(
        <LoadingState 
          isLoading={true}
        />
      )
      
      expect(screen.getByText('正在处理您的请求')).toBeInTheDocument()
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
      
      expect(screen.getByText('上传中...')).toBeInTheDocument()
      expect(screen.getByText('正在上传您的简历文件')).toBeInTheDocument()
    })

    test('displays processing state correctly', () => {
      render(
        <LoadingState 
          isLoading={true}
          stateType={LoadingStateType.PROCESSING}
        />
      )
      
      expect(screen.getByText('处理中...')).toBeInTheDocument()
      expect(screen.getByText('正在处理您的请求')).toBeInTheDocument()
    })

    test('displays analyzing state correctly', () => {
      render(
        <LoadingState 
          isLoading={true}
          stateType={LoadingStateType.ANALYZING}
        />
      )
      
      expect(screen.getByText('分析中...')).toBeInTheDocument()
      expect(screen.getByText('AI 正在分析您的简历')).toBeInTheDocument()
    })

    test('displays matching state correctly', () => {
      render(
        <LoadingState 
          isLoading={true}
          stateType={LoadingStateType.MATCHING}
        />
      )
      
      expect(screen.getByText('匹配中...')).toBeInTheDocument()
      expect(screen.getByText('正在计算简历与职位的匹配度')).toBeInTheDocument()
    })

    test('displays optimizing state correctly', () => {
      render(
        <LoadingState 
          isLoading={true}
          stateType={LoadingStateType.OPTIMIZING}
        />
      )
      
      expect(screen.getByText('优化中...')).toBeInTheDocument()
      expect(screen.getByText('AI 正在优化您的简历')).toBeInTheDocument()
    })
  })

  // Custom Message Tests
  describe('Custom Message', () => {
    test('displays custom message when provided', () => {
      render(
        <LoadingState 
          isLoading={true}
          customMessage="正在准备数据..."
        />
      )
      
      expect(screen.getByText('正在准备数据...')).toBeInTheDocument()
    })

    test('custom message overrides default title', () => {
      render(
        <LoadingState 
          isLoading={true}
          stateType={LoadingStateType.ANALYZING}
          customMessage="自定义消息"
        />
      )
      
      expect(screen.getByText('自定义消息')).toBeInTheDocument()
      // Description should still show the default
      expect(screen.getByText('AI 正在分析您的简历')).toBeInTheDocument()
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
      
      expect(screen.queryByText('取消')).not.toBeInTheDocument()
    })

    test('shows cancel button when onCancel is provided', () => {
      render(
        <LoadingState 
          isLoading={true}
          onCancel={mockOnCancel}
        />
      )
      
      expect(screen.getByText('取消')).toBeInTheDocument()
    })

    test('calls onCancel when cancel button is clicked', () => {
      render(
        <LoadingState 
          isLoading={true}
          onCancel={mockOnCancel}
        />
      )
      
      const cancelButton = screen.getByText('取消')
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
      
      const cancelButton = screen.getByText('取消')
      expect(cancelButton).toHaveAttribute('aria-label', '取消当前操作')
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
      expect(screen.getByText('处理中...')).toBeInTheDocument()
    })

    test('ignores progress values outside 0-100 range', () => {
      const { container } = render(
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
