/**
 * FileUpload Component Tests
 * 
 * RA-21/22: Resume Upload UI & Logic Testing
 * Tests for drag-and-drop, file validation, and upload status display
 */

import { render, screen, fireEvent } from '@testing-library/react'
import '@testing-library/jest-dom'
import FileUpload from '../components/FileUpload'

// Mock file creation helper
const createMockFile = (name, size, type) => {
  const file = new File(['x'.repeat(size)], name, { type })
  Object.defineProperty(file, 'size', { value: size })
  return file
}

describe('FileUpload Component', () => {
  const mockOnFileSelect = jest.fn()
  const mockOnRemoveFile = jest.fn()

  beforeEach(() => {
    jest.clearAllMocks()
  })

  // RA-21: UI Rendering Tests
  describe('UI Rendering', () => {
    test('renders upload area with correct text', () => {
      render(
        <FileUpload 
          onFileSelect={mockOnFileSelect} 
          onRemoveFile={mockOnRemoveFile} 
        />
      )
      
      expect(screen.getByText(/Click to upload or drag and drop/i)).toBeInTheDocument()
      expect(screen.getByText(/PDF, DOCX/i)).toBeInTheDocument()
      expect(screen.getByText(/Max 10MB/i)).toBeInTheDocument()
    })

    test('renders file info when uploadedFile is provided', () => {
      const mockFile = { name: 'resume.pdf', size: 1024 }
      
      render(
        <FileUpload 
          onFileSelect={mockOnFileSelect} 
          uploadedFile={mockFile}
          onRemoveFile={mockOnRemoveFile}
        />
      )
      
      expect(screen.getByText('resume.pdf')).toBeInTheDocument()
      expect(screen.getByText('1 KB')).toBeInTheDocument()
    })

    test('shows green checkmark when isUploaded is true', () => {
      const mockFile = { name: 'resume.pdf', size: 1024 }
      
      render(
        <FileUpload 
          onFileSelect={mockOnFileSelect} 
          uploadedFile={mockFile}
          isUploaded={true}
          onRemoveFile={mockOnRemoveFile}
        />
      )
      
      // Check for the green checkmark container
      const checkmark = screen.getByTitle('Remove file').parentElement.querySelector('.bg-green-100')
      expect(checkmark).toBeInTheDocument()
    })
  })

  // RA-22: File Validation Tests
  describe('File Validation', () => {
    test('accepts valid PDF file', () => {
      render(
        <FileUpload 
          onFileSelect={mockOnFileSelect} 
          onRemoveFile={mockOnRemoveFile}
        />
      )
      
      const file = createMockFile('resume.pdf', 1024, 'application/pdf')
      const input = document.querySelector('input[type="file"]')
      
      fireEvent.change(input, { target: { files: [file] } })
      
      expect(mockOnFileSelect).toHaveBeenCalledWith(file)
    })

    test('accepts valid DOCX file', () => {
      render(
        <FileUpload 
          onFileSelect={mockOnFileSelect} 
          onRemoveFile={mockOnRemoveFile}
        />
      )
      
      const file = createMockFile(
        'resume.docx', 
        1024, 
        'application/vnd.openxmlformats-officedocument.wordprocessingml.document'
      )
      const input = document.querySelector('input[type="file"]')
      
      fireEvent.change(input, { target: { files: [file] } })
      
      expect(mockOnFileSelect).toHaveBeenCalledWith(file)
    })

    test('rejects unsupported file type (.txt)', () => {
      render(
        <FileUpload 
          onFileSelect={mockOnFileSelect} 
          onRemoveFile={mockOnRemoveFile}
        />
      )
      
      const file = createMockFile('resume.txt', 512, 'text/plain')
      const input = document.querySelector('input[type="file"]')
      
      fireEvent.change(input, { target: { files: [file] } })
      
      expect(mockOnFileSelect).not.toHaveBeenCalled()
      expect(screen.getByText(/Only PDF and DOCX formats under 10MB are supported/i)).toBeInTheDocument()
    })

    test('rejects unsupported file type (.doc)', () => {
      render(
        <FileUpload 
          onFileSelect={mockOnFileSelect} 
          onRemoveFile={mockOnRemoveFile}
        />
      )
      
      const file = createMockFile('resume.doc', 1024, 'application/msword')
      const input = document.querySelector('input[type="file"]')
      
      fireEvent.change(input, { target: { files: [file] } })
      
      expect(mockOnFileSelect).not.toHaveBeenCalled()
      expect(screen.getByText(/Only PDF and DOCX formats under 10MB are supported/i)).toBeInTheDocument()
    })

    test('rejects unsupported file type (.exe)', () => {
      render(
        <FileUpload 
          onFileSelect={mockOnFileSelect} 
          onRemoveFile={mockOnRemoveFile}
        />
      )
      
      const file = createMockFile('malware.exe', 1024, 'application/x-msdownload')
      const input = document.querySelector('input[type="file"]')
      
      fireEvent.change(input, { target: { files: [file] } })
      
      expect(mockOnFileSelect).not.toHaveBeenCalled()
      expect(screen.getByText(/Only PDF and DOCX formats under 10MB are supported/i)).toBeInTheDocument()
    })

    test('rejects unsupported file type (.js)', () => {
      render(
        <FileUpload 
          onFileSelect={mockOnFileSelect} 
          onRemoveFile={mockOnRemoveFile}
        />
      )
      
      const file = createMockFile('script.js', 1024, 'application/javascript')
      const input = document.querySelector('input[type="file"]')
      
      fireEvent.change(input, { target: { files: [file] } })
      
      expect(mockOnFileSelect).not.toHaveBeenCalled()
      expect(screen.getByText(/Only PDF and DOCX formats under 10MB are supported/i)).toBeInTheDocument()
    })

    test('rejects file exceeding 10MB limit', () => {
      render(
        <FileUpload 
          onFileSelect={mockOnFileSelect} 
          onRemoveFile={mockOnRemoveFile}
        />
      )
      
      const file = createMockFile('large.pdf', 11 * 1024 * 1024, 'application/pdf')
      const input = document.querySelector('input[type="file"]')
      
      fireEvent.change(input, { target: { files: [file] } })
      
      expect(mockOnFileSelect).not.toHaveBeenCalled()
      expect(screen.getByText(/Only PDF and DOCX formats under 10MB are supported/i)).toBeInTheDocument()
    })

    test('accepts file exactly at 10MB limit', () => {
      render(
        <FileUpload 
          onFileSelect={mockOnFileSelect} 
          onRemoveFile={mockOnRemoveFile}
        />
      )
      
      const file = createMockFile('exact.pdf', 10 * 1024 * 1024, 'application/pdf')
      const input = document.querySelector('input[type="file"]')
      
      fireEvent.change(input, { target: { files: [file] } })
      
      expect(mockOnFileSelect).toHaveBeenCalledWith(file)
    })
  })

  // RA-21: Drag and Drop Tests
  describe('Drag and Drop', () => {
    test('shows drag overlay on drag over', () => {
      render(
        <FileUpload 
          onFileSelect={mockOnFileSelect} 
          onRemoveFile={mockOnRemoveFile}
        />
      )
      
      const dropzone = screen.getByText(/Click to upload/i).closest('div[class*="border-dashed"]')
      
      fireEvent.dragOver(dropzone, {
        dataTransfer: { files: [] }
      })
      
      expect(screen.getByText(/Release to upload file/i)).toBeInTheDocument()
    })

    test('handles file drop correctly', () => {
      render(
        <FileUpload 
          onFileSelect={mockOnFileSelect} 
          onRemoveFile={mockOnRemoveFile}
        />
      )
      
      const file = createMockFile('resume.pdf', 1024, 'application/pdf')
      const dropzone = screen.getByText(/Click to upload/i).closest('div[class*="border-dashed"]')
      
      fireEvent.drop(dropzone, {
        dataTransfer: { files: [file] }
      })
      
      expect(mockOnFileSelect).toHaveBeenCalledWith(file)
    })
  })

  // Remove File Tests
  describe('Remove File', () => {
    test('calls onRemoveFile when remove button clicked', () => {
      const mockFile = { name: 'resume.pdf', size: 1024 }
      
      render(
        <FileUpload 
          onFileSelect={mockOnFileSelect} 
          uploadedFile={mockFile}
          onRemoveFile={mockOnRemoveFile}
        />
      )
      
      const removeButton = screen.getByTitle('Remove file')
      fireEvent.click(removeButton)
      
      expect(mockOnRemoveFile).toHaveBeenCalled()
    })
  })

  // File Size Formatting Tests
  describe('File Size Display', () => {
    test('displays bytes correctly', () => {
      const mockFile = { name: 'tiny.txt', size: 500 }
      
      render(
        <FileUpload 
          onFileSelect={mockOnFileSelect} 
          uploadedFile={mockFile}
          onRemoveFile={mockOnRemoveFile}
        />
      )
      
      expect(screen.getByText('500 Bytes')).toBeInTheDocument()
    })

    test('displays KB correctly', () => {
      const mockFile = { name: 'small.pdf', size: 2048 }
      
      render(
        <FileUpload 
          onFileSelect={mockOnFileSelect} 
          uploadedFile={mockFile}
          onRemoveFile={mockOnRemoveFile}
        />
      )
      
      expect(screen.getByText('2 KB')).toBeInTheDocument()
    })

    test('displays MB correctly', () => {
      const mockFile = { name: 'large.pdf', size: 2 * 1024 * 1024 }
      
      render(
        <FileUpload 
          onFileSelect={mockOnFileSelect} 
          uploadedFile={mockFile}
          onRemoveFile={mockOnRemoveFile}
        />
      )
      
      expect(screen.getByText('2 MB')).toBeInTheDocument()
    })
  })
})
