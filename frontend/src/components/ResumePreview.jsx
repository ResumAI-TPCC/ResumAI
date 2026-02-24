import PropTypes from 'prop-types'

function ResumePreview({ sessionId, uploadedFile, optimizedHtml }) {
  void sessionId
  void uploadedFile

  return (
    <aside className="w-80 bg-white border-l border-gray-200 h-screen flex flex-col">
      <div className="p-4 border-b border-gray-200">
        <h2 className="font-bold text-lg text-gray-800">Resume Preview</h2>
      </div>
      <div className="flex-1 overflow-y-auto p-4">
        {optimizedHtml ? (
          <>
            <style>{`
              .resume-preview h1 { font-size: 1.25rem; font-weight: 700; color: #1a1a2e; border-bottom: 2px solid #1a1a2e; padding-bottom: 4px; margin-bottom: 8px; text-align: center; }
              .resume-preview h2 { font-size: 1rem; font-weight: 600; color: #1a1a2e; border-bottom: 1px solid #e5e7eb; padding-bottom: 2px; margin-top: 14px; margin-bottom: 6px; text-transform: uppercase; letter-spacing: 0.5px; }
              .resume-preview h3 { font-size: 0.9rem; font-weight: 600; color: #333; margin-top: 8px; margin-bottom: 4px; }
              .resume-preview p { margin: 2px 0 6px 0; }
              .resume-preview ul { padding-left: 16px; margin: 2px 0; }
              .resume-preview li { margin-bottom: 2px; }
              .resume-preview strong { color: #1a1a2e; }
              .resume-preview em { color: #555; }
            `}</style>
            <div
              className="resume-preview text-sm text-gray-700 leading-relaxed"
              dangerouslySetInnerHTML={{ __html: optimizedHtml }}
            />
          </>
        ) : (
          <div className="text-gray-400 text-center mt-8">
            <svg className="w-12 h-12 mx-auto mb-3" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
            </svg>
            <p className="text-sm">Optimized resume will appear here after generation</p>
          </div>
        )}
      </div>
    </aside>
  )
}

ResumePreview.propTypes = {
  sessionId: PropTypes.string,
  uploadedFile: PropTypes.shape({
    name: PropTypes.string,
    size: PropTypes.number,
  }),
  optimizedHtml: PropTypes.string,
}

export default ResumePreview
