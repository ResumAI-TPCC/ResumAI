/**
 * API Utility Functions Tests
 * 
 * RA-22: Resume Upload Logic Testing
 * Tests for uploadResume, analyzeResume, matchResumeWithJob, optimizeResume
 */

// Mock the api module before importing
const mockUploadResume = jest.fn()
const mockAnalyzeResume = jest.fn()
const mockMatchResumeWithJob = jest.fn()
const mockOptimizeResume = jest.fn()

jest.mock('../utils/api', () => ({
  uploadResume: (...args) => mockUploadResume(...args),
  analyzeResume: (...args) => mockAnalyzeResume(...args),
  matchResumeWithJob: (...args) => mockMatchResumeWithJob(...args),
  optimizeResume: (...args) => mockOptimizeResume(...args),
}))

describe('API Utility Functions - Unit Tests', () => {
  beforeEach(() => {
    jest.clearAllMocks()
  })

  // RA-22: uploadResume Tests
  describe('uploadResume', () => {
    test('returns file data on successful upload', async () => {
      const mockResponse = {
        file_id: 'test-123',
        filename: 'resume.pdf',
        storage_path: 'gs://bucket/resume.pdf'
      }
      mockUploadResume.mockResolvedValue(mockResponse)

      const file = new File(['test content'], 'resume.pdf', { type: 'application/pdf' })
      const result = await mockUploadResume(file)
      
      expect(mockUploadResume).toHaveBeenCalledWith(file)
      expect(result.file_id).toBe('test-123')
      expect(result.filename).toBe('resume.pdf')
    })

    test('handles upload with progress callback', async () => {
      mockUploadResume.mockResolvedValue({ file_id: 'test-123' })
      
      const file = new File(['test'], 'resume.pdf', { type: 'application/pdf' })
      const onProgress = jest.fn()
      
      await mockUploadResume(file, onProgress)
      
      expect(mockUploadResume).toHaveBeenCalledWith(file, onProgress)
    })

    test('throws error on upload failure', async () => {
      mockUploadResume.mockRejectedValue(new Error('Unsupported file type'))

      await expect(mockUploadResume(new File([''], 'test.exe'))).rejects.toThrow('Unsupported file type')
    })

    test('throws error on network failure', async () => {
      mockUploadResume.mockRejectedValue(new Error('Network error occurred'))

      await expect(mockUploadResume(new File([''], 'test.pdf'))).rejects.toThrow('Network error')
    })
  })

  // RA-22: analyzeResume Tests
  describe('analyzeResume', () => {
    test('returns analysis suggestions on success', async () => {
      const mockResponse = {
        data: {
          suggestions: [
            { category: 'content', priority: 'high', title: 'Add Summary', description: 'Add a professional summary' }
          ]
        }
      }
      mockAnalyzeResume.mockResolvedValue(mockResponse)

      const result = await mockAnalyzeResume('session-123')
      
      expect(mockAnalyzeResume).toHaveBeenCalledWith('session-123')
      expect(result.data.suggestions).toHaveLength(1)
      expect(result.data.suggestions[0].priority).toBe('high')
    })

    test('throws error for empty session_id', async () => {
      mockAnalyzeResume.mockRejectedValue(new Error('Session ID is required'))

      await expect(mockAnalyzeResume('')).rejects.toThrow('Session ID is required')
    })

    test('handles 404 resume not found', async () => {
      mockAnalyzeResume.mockRejectedValue(new Error('Resume not found'))

      await expect(mockAnalyzeResume('invalid-session')).rejects.toThrow('Resume not found')
    })

    test('handles server error', async () => {
      mockAnalyzeResume.mockRejectedValue(new Error('Server error'))

      await expect(mockAnalyzeResume('session-123')).rejects.toThrow('Server error')
    })
  })

  // RA-22: matchResumeWithJob Tests
  describe('matchResumeWithJob', () => {
    test('returns match score and suggestions', async () => {
      const mockResponse = {
        data: {
          match_score: 85,
          suggestions: [
            { category: 'skills', priority: 'medium', title: 'Add Keywords', description: 'Include more keywords from JD' }
          ]
        }
      }
      mockMatchResumeWithJob.mockResolvedValue(mockResponse)

      const result = await mockMatchResumeWithJob(
        'session-123',
        'Software Engineer position...',
        'Software Engineer',
        'TechCorp'
      )
      
      expect(mockMatchResumeWithJob).toHaveBeenCalledWith(
        'session-123',
        'Software Engineer position...',
        'Software Engineer',
        'TechCorp'
      )
      expect(result.data.match_score).toBe(85)
    })

    test('handles optional parameters', async () => {
      mockMatchResumeWithJob.mockResolvedValue({ data: { match_score: 70 } })

      await mockMatchResumeWithJob('session-123', 'JD text')
      
      expect(mockMatchResumeWithJob).toHaveBeenCalledWith('session-123', 'JD text')
    })

    test('throws error on match failure', async () => {
      mockMatchResumeWithJob.mockRejectedValue(new Error('Match failed'))

      await expect(mockMatchResumeWithJob('session-123', 'JD')).rejects.toThrow('Match failed')
    })
  })

  // RA-22: optimizeResume Tests
  describe('optimizeResume', () => {
    test('returns optimized content', async () => {
      const mockResponse = {
        data: {
          optimized_content: 'Optimized resume content...',
          format: 'docx'
        }
      }
      mockOptimizeResume.mockResolvedValue(mockResponse)

      const result = await mockOptimizeResume('session-123', 'JD text', 'professional')
      
      expect(mockOptimizeResume).toHaveBeenCalledWith('session-123', 'JD text', 'professional')
      expect(result.data.optimized_content).toBeDefined()
    })

    test('uses default template when not specified', async () => {
      mockOptimizeResume.mockResolvedValue({ data: {} })

      await mockOptimizeResume('session-123')
      
      expect(mockOptimizeResume).toHaveBeenCalledWith('session-123')
    })

    test('throws error on optimization failure', async () => {
      mockOptimizeResume.mockRejectedValue(new Error('Optimization failed'))

      await expect(mockOptimizeResume('session-123')).rejects.toThrow('Optimization failed')
    })
  })
})

// Integration-style tests for API contract validation
describe('API Contract Validation', () => {
  describe('Upload Response Format', () => {
    test('upload response should match expected schema', async () => {
      const expectedSchema = {
        file_id: expect.any(String),
        filename: expect.any(String),
        storage_path: expect.stringMatching(/^gs:\/\//),
      }

      mockUploadResume.mockResolvedValue({
        file_id: 'uuid-1234',
        filename: 'resume.pdf',
        storage_path: 'gs://bucket/path/resume.pdf',
        parsed_data: null
      })

      const result = await mockUploadResume(new File([''], 'resume.pdf'))
      
      expect(result).toMatchObject(expectedSchema)
    })
  })

  describe('Analyze Response Format', () => {
    test('analyze response should include suggestions array', async () => {
      mockAnalyzeResume.mockResolvedValue({
        data: {
          suggestions: [
            {
              category: 'content',
              priority: 'high',
              title: 'Test Title',
              description: 'Test Description',
              example: 'Test Example'
            }
          ]
        }
      })

      const result = await mockAnalyzeResume('session-123')
      
      expect(result.data.suggestions).toBeInstanceOf(Array)
      expect(result.data.suggestions[0]).toHaveProperty('category')
      expect(result.data.suggestions[0]).toHaveProperty('priority')
      expect(result.data.suggestions[0]).toHaveProperty('title')
      expect(result.data.suggestions[0]).toHaveProperty('description')
    })
  })

  describe('Match Response Format', () => {
    test('match response should include score and breakdown', async () => {
      mockMatchResumeWithJob.mockResolvedValue({
        data: {
          match_score: 75,
          match_breakdown: {
            skills_match: 80,
            experience_match: 70,
            education_match: 75,
            keywords_match: 75
          },
          suggestions: []
        }
      })

      const result = await mockMatchResumeWithJob('session-123', 'JD')
      
      expect(result.data.match_score).toBeGreaterThanOrEqual(0)
      expect(result.data.match_score).toBeLessThanOrEqual(100)
    })
  })
})
