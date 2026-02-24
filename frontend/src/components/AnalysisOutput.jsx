import { useState } from 'react'
import PropTypes from 'prop-types'
import { matchResumeWithJob, analyzeResume } from '../utils/api'

function AnalysisOutput({ sessionId, jobDescription, companyName, jobTitle, isOptimizing, optimizedData, onGenerateResume, onDownloadResume }) {
  const [analysisData, setAnalysisData] = useState(null)
  const [isAnalyzing, setIsAnalyzing] = useState(false)
  const [error, setError] = useState(null)

  const handleAnalyze = async () => {
    if (!sessionId) {
      setError('Please upload a resume first')
      return
    }

    setIsAnalyzing(true)
    setError(null)

    try {
      let result;
      if (jobDescription && jobDescription.trim()) {
        // Call match API with job description
        result = await matchResumeWithJob(
          sessionId,
          jobDescription,
          jobTitle || '',
          companyName || ''
        )
        
        // Set data for match analysis
        setAnalysisData({
          type: 'match',
          matchScore: result.data?.match_score || 68,
          matchBreakdown: result.data?.match_breakdown || {
            skills_match: 85,
            experience_match: 75,
            education_match: 90,
            keywords_match: 70
          },
          scoringPrinciples: [
            {
              title: 'Skill Match (35%)',
              description: 'Assessment of how well your skills align with job requirements'
            },
            {
              title: 'Experience Alignment (25%)',
              description: 'Analysis of how your work experience relates to job requirements'
            },
            {
              title: 'Education & Background (15%)',
              description: 'How well your educational matches job requirements'
            },
            {
              title: 'Achievement Impact (15%)',
              description: 'Measurable results, metrics, and concrete value from achievements'
            },
            {
              title: 'Keyword & Format (10%)',
              description: 'Compliance with resume best practices and key skills from the JD'
            }
          ],
          analysisReasoning: 'Based on the Job Description (JD) you provided, we provide detailed match analysis and optimization recommendations.',
          suggestions: result.data?.suggestions || []
        })
      } else {
        // Call analyze API without job description
        result = await analyzeResume(sessionId)
        
        // Set data for general analysis
        setAnalysisData({
          type: 'analyze',
          suggestions: result.data?.suggestions || []
        })
      }
    } catch (err) {
      console.error('Analysis error:', err)
      setError(err.message || 'Failed to analyze resume')
    } finally {
      setIsAnalyzing(false)
    }
  }

  const handleGenerateResume = () => {
    if (onGenerateResume) onGenerateResume()
  }

  const handleDownloadResume = () => {
    if (onDownloadResume) onDownloadResume()
  }

  return (
    <main className="flex-1 p-6 bg-gray-50 overflow-y-auto">
      <div className="max-w-3xl mx-auto">
        {/* Header */}
        <div className="mb-6">
          <h1 className="text-xl font-bold text-gray-800">
            {analysisData?.type === 'match' ? 'Match Analysis' : 'Resume Analysis'}
          </h1>
        </div>

        {/* Empty State - Show when no analysis yet */}
        {!analysisData && (
          <div className="bg-white rounded-lg shadow p-8 text-center">
            <div className="mb-4">
              <svg className="w-16 h-16 mx-auto text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24" role="img" aria-label="Resume icon">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
              </svg>
            </div>
            <h2 className="text-lg font-semibold text-gray-800 mb-2">
              {jobDescription && jobDescription.trim() ? 'Ready to Analyze Match' : 'Ready to Analyze Resume'}
            </h2>
            <p className="text-gray-600 mb-6 text-sm">
              {!sessionId && 'Please upload your resume to get started'}
              {sessionId && (!jobDescription || !jobDescription.trim()) && 'Click the button below to analyze your resume'}
              {sessionId && jobDescription && jobDescription.trim() && 'Click the button below to analyze your resume against the job description'}
            </p>
            <button
              onClick={handleAnalyze}
              disabled={!sessionId || isAnalyzing}
              className="px-6 py-2.5 bg-blue-600 text-white text-sm font-medium rounded-lg hover:bg-blue-700 disabled:bg-gray-300 disabled:cursor-not-allowed transition-colors"
            >
              {isAnalyzing ? (
                <span className="flex items-center justify-center">
                  <svg className="animate-spin -ml-1 mr-2 h-4 w-4 text-white" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" role="status" aria-label="Loading">
                    <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
                    <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                  </svg>
                  Analyzing...
                </span>
              ) : (
                jobDescription && jobDescription.trim() ? 'Analyze Match' : 'Analyze Resume'
              )}
            </button>
            {error && (
              <div className="mt-4 p-3 bg-red-50 border border-red-200 rounded-lg">
                <p className="text-red-600 text-sm">{error}</p>
              </div>
            )}
          </div>
        )}

        {/* Analysis Results */}
        {analysisData && (
          <div className="space-y-4">
            {/* Match Score Card - Only for match type */}
            {analysisData.type === 'match' && (
              <div className="relative overflow-hidden rounded-lg shadow-lg">
                <div className="bg-gradient-to-r from-indigo-500 via-purple-500 to-purple-600 p-6 text-white">
                  <div className="flex items-center justify-between">
                    <div>
                      <div className="flex items-baseline gap-2">
                        <svg className="w-5 h-5" fill="currentColor" viewBox="0 0 20 20">
                          <path fillRule="evenodd" d="M6.267 3.455a3.066 3.066 0 001.745-.723 3.066 3.066 0 013.976 0 3.066 3.066 0 001.745.723 3.066 3.066 0 012.812 2.812c.051.643.304 1.254.723 1.745a3.066 3.066 0 010 3.976 3.066 3.066 0 00-.723 1.745 3.066 3.066 0 01-2.812 2.812 3.066 3.066 0 00-1.745.723 3.066 3.066 0 01-3.976 0 3.066 3.066 0 00-1.745-.723 3.066 3.066 0 01-2.812-2.812 3.066 3.066 0 00-.723-1.745 3.066 3.066 0 010-3.976 3.066 3.066 0 00.723-1.745 3.066 3.066 0 012.812-2.812zm7.44 5.252a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z" clipRule="evenodd" />
                        </svg>
                        <h2 className="text-sm font-medium">Match Score</h2>
                      </div>
                      <div className="mt-2 flex items-baseline">
                        <span className="text-5xl font-bold">{analysisData.matchScore}</span>
                        <span className="text-2xl font-medium ml-1">/100</span>
                      </div>
                    </div>
                    <div className="hidden sm:block">
                      <svg className="w-20 h-20 opacity-30" fill="currentColor" viewBox="0 0 20 20">
                        <path d="M9 2a1 1 0 000 2h2a1 1 0 100-2H9z" />
                        <path fillRule="evenodd" d="M4 5a2 2 0 012-2 3 3 0 003 3h2a3 3 0 003-3 2 2 0 012 2v11a2 2 0 01-2 2H6a2 2 0 01-2-2V5zm9.707 5.707a1 1 0 00-1.414-1.414L9 12.586l-1.293-1.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z" clipRule="evenodd" />
                      </svg>
                    </div>
                  </div>
                  {/* Progress bar */}
                  <div className="mt-4">
                    <div className="w-full bg-white bg-opacity-30 rounded-full h-2.5">
                      <div 
                        className="bg-white h-2.5 rounded-full transition-all duration-500"
                        style={{ width: `${analysisData.matchScore}%` }}
                      ></div>
                    </div>
                  </div>
                </div>
              </div>
            )}

            {/* Scoring Principles - Only for match type */}
            {analysisData.type === 'match' && (
              <div className="bg-white rounded-lg shadow p-6">
                <div className="flex items-center gap-2 mb-4">
                  <svg className="w-5 h-5 text-gray-700" fill="currentColor" viewBox="0 0 20 20" role="img" aria-label="Scoring principles icon">
                    <path fillRule="evenodd" d="M6 2a1 1 0 00-1 1v1H4a2 2 0 00-2 2v10a2 2 0 002 2h12a2 2 0 002-2V6a2 2 0 00-2-2h-1V3a1 1 0 10-2 0v1H7V3a1 1 0 00-1-1zm0 5a1 1 0 000 2h8a1 1 0 100-2H6z" clipRule="evenodd" />
                  </svg>
                  <h2 className="text-base font-semibold text-gray-800">Scoring Principles</h2>
                </div>
                <p className="text-sm text-gray-600 mb-4">
                  Based on the Job Description (JD) you provided, we evaluate resume match using the following dimensions:
                </p>
                <ul className="space-y-3">
                  {analysisData.scoringPrinciples.map((principle, index) => (
                    <li key={index} className="flex items-start">
                      <span className="inline-flex items-center justify-center w-5 h-5 rounded-full bg-blue-100 text-blue-600 text-xs font-semibold mr-3 mt-0.5 flex-shrink-0">
                        {index + 1}
                      </span>
                      <div>
                        <p className="text-sm font-medium text-gray-800">{principle.title}</p>
                        <p className="text-sm text-gray-600">{principle.description}</p>
                      </div>
                    </li>
                  ))}
                </ul>
              </div>
            )}

            {/* Analysis Reasoning - Only for match type */}
            {analysisData.type === 'match' && (
              <div className="bg-white rounded-lg shadow p-6">
                <div className="flex items-center gap-2 mb-4">
                  <svg className="w-5 h-5 text-purple-600" fill="currentColor" viewBox="0 0 20 20" role="img" aria-label="Analysis reasoning icon">
                    <path d="M9 4.804A7.968 7.968 0 005.5 4c-1.255 0-2.443.29-3.5.804v10A7.969 7.969 0 015.5 14c1.669 0 3.218.51 4.5 1.385A7.962 7.962 0 0114.5 14c1.255 0 2.443.29 3.5.804v-10A7.968 7.968 0 0014.5 4c-1.255 0-2.443.29-3.5.804V12a1 1 0 11-2 0V4.804z" />
                  </svg>
                  <h2 className="text-base font-semibold text-gray-800">Analysis Reasoning</h2>
                </div>
                <p className="text-sm text-gray-700 leading-relaxed">
                  {analysisData.analysisReasoning}
                </p>
              </div>
            )}

            {/* Suggestions */}
            {analysisData.suggestions && analysisData.suggestions.length > 0 && (
              <div className="bg-white rounded-lg shadow p-6">
                <div className="flex items-center gap-2 mb-4">
                  <svg className="w-5 h-5 text-green-600" fill="currentColor" viewBox="0 0 20 20" role="img" aria-label="Suggestions icon">
                    <path fillRule="evenodd" d="M18 10a8 8 0 11-16 0 8 8 0 0116 0zm-7-4a1 1 0 11-2 0 1 1 0 012 0zM9 9a1 1 0 000 2v3a1 1 0 001 1h1a1 1 0 100-2v-3a1 1 0 00-1-1H9z" clipRule="evenodd" />
                  </svg>
                  <h2 className="text-base font-semibold text-gray-800">
                    {analysisData.type === 'match' ? 'Improvement Suggestions' : 'Resume Analysis Suggestions'}
                  </h2>
                </div>
                <div className="space-y-4">
                  {analysisData.suggestions.map((suggestion, index) => (
                    <div key={index} className="border border-gray-200 rounded-lg p-4">
                      <div className="flex items-start gap-3">
                        <div className={`flex-shrink-0 w-8 h-8 rounded-full flex items-center justify-center text-xs font-semibold ${
                          suggestion.priority === 'high' ? 'bg-red-100 text-red-700' :
                          suggestion.priority === 'medium' ? 'bg-yellow-100 text-yellow-700' :
                          'bg-blue-100 text-blue-700'
                        }`}>
                          {suggestion.priority === 'high' ? 'H' : suggestion.priority === 'medium' ? 'M' : 'L'}
                        </div>
                        <div className="flex-1">
                          <h3 className="text-sm font-medium text-gray-800 mb-1">
                            {suggestion.title || suggestion.category}
                          </h3>
                          <p className="text-sm text-gray-600 mb-2">
                            {suggestion.description}
                          </p>
                          {suggestion.example && (
                            <div className="bg-gray-50 rounded p-2">
                              <p className="text-xs text-gray-500 mb-1">Example:</p>
                              <p className="text-sm text-gray-700 italic">{suggestion.example}</p>
                            </div>
                          )}
                          {suggestion.action && (
                            <div className="bg-blue-50 rounded p-2 mt-2">
                              <p className="text-xs text-blue-600 mb-1">Suggested Action:</p>
                              <p className="text-sm text-blue-700">{suggestion.action}</p>
                            </div>
                          )}
                        </div>
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            )}

            {/* Action Buttons */}
            <div className="bg-white rounded-lg shadow p-6">
              <div className="flex flex-col sm:flex-row gap-3">
                <button
                  onClick={handleGenerateResume}
                  disabled={isOptimizing}
                  className="flex-1 px-4 py-2.5 bg-purple-600 text-white text-sm font-medium rounded-lg hover:bg-purple-700 disabled:bg-purple-300 disabled:cursor-not-allowed transition-colors flex items-center justify-center gap-2"
                >
                  {isOptimizing ? (
                    <>
                      <svg className="animate-spin h-4 w-4 text-white" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" aria-hidden="true">
                        <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
                        <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                      </svg>
                      Generating...
                    </>
                  ) : (
                    <>
                      <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24" aria-hidden="true">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M11 5H6a2 2 0 00-2 2v11a2 2 0 002 2h11a2 2 0 002-2v-5m-1.414-9.414a2 2 0 112.828 2.828L11.828 15H9v-2.828l8.586-8.586z" />
                      </svg>
                      {optimizedData ? 'Regenerate Resume' : 'Generate Polished Resume'}
                    </>
                  )}
                </button>
                <button
                  onClick={handleDownloadResume}
                  disabled={!optimizedData}
                  className="flex-1 px-4 py-2.5 bg-blue-600 text-white text-sm font-medium rounded-lg hover:bg-blue-700 disabled:bg-blue-300 disabled:cursor-not-allowed transition-colors flex items-center justify-center gap-2"
                >
                  <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24" aria-hidden="true">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 16v1a3 3 0 003 3h10a3 3 0 003-3v-1m-4-4l-4 4m0 0l-4-4m4 4V4" />
                  </svg>
                  Download Polished Resume
                </button>
              </div>
              <button
                onClick={handleAnalyze}
                disabled={isAnalyzing}
                className="mt-3 w-full px-4 py-2 bg-gray-100 text-gray-700 text-sm font-medium rounded-lg hover:bg-gray-200 disabled:bg-gray-50 disabled:cursor-not-allowed transition-colors"
              >
                {isAnalyzing ? 'Re-analyzing...' : 'Re-analyze'}
              </button>
            </div>
          </div>
        )}
      </div>
    </main>
  )
}

AnalysisOutput.propTypes = {
  sessionId: PropTypes.string,
  jobDescription: PropTypes.string,
  companyName: PropTypes.string,
  jobTitle: PropTypes.string,
  isOptimizing: PropTypes.bool,
  optimizedData: PropTypes.shape({
    encoded_file: PropTypes.string,
    optimized_html: PropTypes.string,
  }),
  onGenerateResume: PropTypes.func,
  onDownloadResume: PropTypes.func,
}

export default AnalysisOutput
