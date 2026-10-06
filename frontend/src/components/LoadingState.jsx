import { useEffect, useRef } from 'react'
import PropTypes from 'prop-types'

/**
 * Loading state types
 */
export const LoadingStateType = {
  UPLOADING: 'uploading',
  PROCESSING: 'processing',
  ANALYZING: 'analyzing',
  MATCHING: 'matching',
  OPTIMIZING: 'optimizing',
}

/**
 * Loading state configuration
 * Maps state types to display messages
 */
const LOADING_CONFIG = {
  [LoadingStateType.UPLOADING]: {
    title: '上传中...',
    description: '正在上传您的简历文件',
    icon: 'upload',
  },
  [LoadingStateType.PROCESSING]: {
    title: '处理中...',
    description: '正在处理您的请求',
    icon: 'process',
  },
  [LoadingStateType.ANALYZING]: {
    title: '分析中...',
    description: 'AI 正在分析您的简历',
    icon: 'analyze',
  },
  [LoadingStateType.MATCHING]: {
    title: '匹配中...',
    description: '正在计算简历与职位的匹配度',
    icon: 'match',
  },
  [LoadingStateType.OPTIMIZING]: {
    title: '优化中...',
    description: 'AI 正在优化您的简历',
    icon: 'optimize',
  },
}

/**
 * LoadingState Component
 * Displays loading state with progress indication and cancel button
 * 
 * @param {Object} props - Component props
 * @param {string} props.stateType - Type of loading state (from LoadingStateType)
 * @param {boolean} props.isLoading - Whether the loading state is active
 * @param {function} props.onCancel - Callback when cancel button is clicked
 * @param {string} props.customMessage - Optional custom message to display
 * @param {number} props.progress - Optional progress percentage (0-100)
 */
function LoadingState({
  stateType = LoadingStateType.PROCESSING,
  isLoading = false,
  onCancel = null,
  customMessage = null,
  progress = null,
}) {
  const config = LOADING_CONFIG[stateType] || LOADING_CONFIG[LoadingStateType.PROCESSING]
  
  // Track if component is mounted to prevent state updates after unmount
  const isMountedRef = useRef(true)
  
  useEffect(() => {
    return () => {
      isMountedRef.current = false
    }
  }, [])

  if (!isLoading) {
    return null
  }

  return (
    <div className="bg-white rounded-lg shadow p-8 text-center" role="status" aria-live="polite">
      {/* Spinner */}
      <div className="mb-5">
        <div 
          className="w-16 h-16 mx-auto border-4 border-blue-200 border-t-blue-500 rounded-full animate-spin" 
          aria-hidden="true"
        />
      </div>

      {/* Title */}
      <h2 className="text-lg font-semibold text-gray-800 mb-2">
        {customMessage || config.title}
      </h2>

      {/* Description */}
      <p className="text-gray-600 text-sm mb-4">
        {config.description}
      </p>

      {/* Progress bar (if provided) */}
      {progress !== null && progress >= 0 && progress <= 100 && (
        <div className="mb-4">
          <div className="w-full bg-gray-200 rounded-full h-2">
            <div 
              className="bg-blue-500 h-2 rounded-full transition-all duration-300"
              style={{ width: `${progress}%` }}
              aria-label={`Progress: ${progress}%`}
            />
          </div>
          <p className="text-xs text-gray-500 mt-1">{progress}%</p>
        </div>
      )}

      {/* Cancel button */}
      {onCancel && (
        <button
          onClick={onCancel}
          className="px-4 py-2 text-sm text-gray-600 bg-gray-100 hover:bg-gray-200 rounded-lg transition-colors duration-200 focus:outline-none focus:ring-2 focus:ring-gray-300"
          aria-label="取消当前操作"
        >
          取消
        </button>
      )}
    </div>
  )
}

LoadingState.propTypes = {
  stateType: PropTypes.oneOf(Object.values(LoadingStateType)),
  isLoading: PropTypes.bool,
  onCancel: PropTypes.func,
  customMessage: PropTypes.string,
  progress: PropTypes.number,
}

LoadingState.defaultProps = {
  stateType: LoadingStateType.PROCESSING,
  isLoading: false,
  onCancel: null,
  customMessage: null,
  progress: null,
}

export default LoadingState
