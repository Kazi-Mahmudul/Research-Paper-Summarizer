import React, { useState } from 'react'

const SummaryDisplay = ({ summary, onReset }) => {
  const [copiedSection, setCopiedSection] = useState(null)

  const copyToClipboard = async (text, sectionTitle) => {
    try {
      await navigator.clipboard.writeText(text)
      setCopiedSection(sectionTitle)
      setTimeout(() => setCopiedSection(null), 2000)
    } catch (err) {
      console.error('Failed to copy text: ', err)
      // Fallback for older browsers
      const textArea = document.createElement('textarea')
      textArea.value = text
      document.body.appendChild(textArea)
      textArea.select()
      document.execCommand('copy')
      document.body.removeChild(textArea)
      setCopiedSection(sectionTitle)
      setTimeout(() => setCopiedSection(null), 2000)
    }
  }

  const copyFullSummary = () => {
    const fullText = `${summary.title}\n\n${summary.sections.map(section => 
      `${section.title}\n${'-'.repeat(section.title.length)}\n${section.content}\n`
    ).join('\n')}`
    
    copyToClipboard(fullText, 'full-summary')
  }

  const formatProcessingTime = (seconds) => {
    if (seconds < 60) {
      return `${seconds.toFixed(1)}s`
    } else {
      const minutes = Math.floor(seconds / 60)
      const remainingSeconds = seconds % 60
      return `${minutes}m ${remainingSeconds.toFixed(0)}s`
    }
  }

  const getSectionIcon = (title) => {
    const titleLower = title.toLowerCase()
    if (titleLower.includes('problem') || titleLower.includes('research')) {
      return '🎯'
    } else if (titleLower.includes('method') || titleLower.includes('approach')) {
      return '🔬'
    } else if (titleLower.includes('result') || titleLower.includes('finding')) {
      return '📊'
    } else if (titleLower.includes('implication') || titleLower.includes('significance')) {
      return '💡'
    } else if (titleLower.includes('limitation') || titleLower.includes('future')) {
      return '🔮'
    }
    return '📝'
  }

  return (
    <div className="w-full max-w-6xl mx-auto space-y-8">
      {/* Header */}
      <div className="card overflow-hidden">
        <div className="bg-gradient-to-r from-blue-600 via-purple-600 to-indigo-700 px-4 sm:px-8 py-6 sm:py-10 text-white">
          <div className="flex flex-col space-y-4 sm:space-y-6">
            <div className="flex-1">
              <h2 className="text-xl sm:text-2xl lg:text-3xl font-bold leading-tight mb-3 sm:mb-4">
                {summary.title}
              </h2>
              <div className="flex flex-wrap gap-2 sm:gap-4 text-xs sm:text-sm">
                <div className="flex items-center space-x-2 bg-white/20 rounded-full px-3 py-1">
                  <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z" />
                  </svg>
                  <span>Processed in {formatProcessingTime(summary.processing_time)}</span>
                </div>
                <div className="flex items-center space-x-2 bg-white/20 rounded-full px-3 py-1">
                  <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 11H5m14 0a2 2 0 012 2v6a2 2 0 01-2 2H5a2 2 0 01-2-2v-6a2 2 0 012-2m14 0V9a2 2 0 00-2-2M5 11V9a2 2 0 012-2m0 0V5a2 2 0 012-2h6a2 2 0 012 2v2M7 7h10" />
                  </svg>
                  <span>{summary.chunk_count} chunks analyzed</span>
                </div>
              </div>
            </div>
            
            <div className="flex flex-col sm:flex-row gap-2 sm:gap-3">
              <button 
                onClick={copyFullSummary}
                className={`
                  flex items-center justify-center space-x-2 px-4 sm:px-6 py-2 sm:py-3 rounded-lg font-medium transition-all duration-200 text-sm sm:text-base
                  ${copiedSection === 'full-summary' 
                    ? 'bg-green-500 text-white' 
                    : 'bg-white/20 hover:bg-white/30 text-white border border-white/30'
                  }
                `}
              >
                {copiedSection === 'full-summary' ? (
                  <>
                    <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
                    </svg>
                    <span>Copied!</span>
                  </>
                ) : (
                  <>
                    <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8 16H6a2 2 0 01-2-2V6a2 2 0 012-2h8a2 2 0 012 2v2m-6 12h8a2 2 0 002-2v-8a2 2 0 00-2-2h-8a2 2 0 00-2 2v8a2 2 0 002 2z" />
                    </svg>
                    <span>Copy All</span>
                  </>
                )}
              </button>
              
              <button 
                onClick={onReset}
                className="flex items-center justify-center space-x-2 px-4 sm:px-6 py-2 sm:py-3 bg-white/20 hover:bg-white/30 text-white border border-white/30 rounded-lg font-medium transition-all duration-200 text-sm sm:text-base"
              >
                <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 16v1a3 3 0 003 3h10a3 3 0 003-3v-1m-4-8l-4-4m0 0L8 8m4-4v12" />
                </svg>
                <span>New Upload</span>
              </button>
            </div>
          </div>
        </div>
      </div>

      {/* Summary Sections */}
      <div className="space-y-6">
        {summary.sections.map((section, index) => (
          <div key={index} className="card overflow-hidden group hover:shadow-xl transition-all duration-300">
            {/* Section Header */}
            <div className="bg-gradient-to-r from-gray-50 to-blue-50 px-4 sm:px-6 py-3 sm:py-4 border-b border-gray-200">
              <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-3">
                <div className="flex items-center space-x-2 sm:space-x-3">
                  <span className="text-xl sm:text-2xl">{getSectionIcon(section.title)}</span>
                  <h3 className="text-lg sm:text-xl font-bold text-gray-900">{section.title}</h3>
                </div>
                <button
                  onClick={() => copyToClipboard(section.content, section.title)}
                  className={`
                    flex items-center space-x-2 px-3 sm:px-4 py-1.5 sm:py-2 rounded-lg font-medium transition-all duration-200 text-xs sm:text-sm self-end sm:self-auto
                    ${copiedSection === section.title 
                      ? 'bg-green-100 text-green-700 border border-green-200' 
                      : 'bg-white hover:bg-gray-50 text-gray-600 border border-gray-200 hover:border-gray-300'
                    }
                  `}
                  title="Copy this section"
                >
                  {copiedSection === section.title ? (
                    <>
                      <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
                      </svg>
                      <span className="text-sm">Copied</span>
                    </>
                  ) : (
                    <>
                      <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8 16H6a2 2 0 01-2-2V6a2 2 0 012-2h8a2 2 0 012 2v2m-6 12h8a2 2 0 002-2v-8a2 2 0 00-2-2h-8a2 2 0 00-2 2v8a2 2 0 002 2z" />
                      </svg>
                      <span className="text-sm">Copy</span>
                    </>
                  )}
                </button>
              </div>
            </div>
            
            {/* Section Content */}
            <div className="p-4 sm:p-6">
              <div className="academic-text text-base sm:text-lg leading-relaxed">
                {section.content.split('\n').map((paragraph, pIndex) => {
                  if (!paragraph.trim()) return null;
                  
                  // Handle bold text formatting
                  const formattedParagraph = paragraph
                    .replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>')
                    .replace(/\*(.*?)\*/g, '<em>$1</em>');
                  
                  return (
                    <p 
                      key={pIndex} 
                      className="mb-4 last:mb-0"
                      dangerouslySetInnerHTML={{ __html: formattedParagraph }}
                    />
                  );
                })}
              </div>
            </div>
          </div>
        ))}
      </div>

      {/* Footer Stats */}
      <div className="card p-4 sm:p-8">
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6 sm:gap-8 mb-6 sm:mb-8">
          <div className="text-center">
            <div className="w-14 h-14 sm:w-16 sm:h-16 bg-blue-100 rounded-full flex items-center justify-center mx-auto mb-3">
              <svg className="w-7 h-7 sm:w-8 sm:h-8 text-blue-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 11H5m14 0a2 2 0 012 2v6a2 2 0 01-2 2H5a2 2 0 01-2-2v-6a2 2 0 012-2m14 0V9a2 2 0 00-2-2M5 11V9a2 2 0 012-2m0 0V5a2 2 0 012-2h6a2 2 0 012 2v2M7 7h10" />
              </svg>
            </div>
            <div className="text-xl sm:text-2xl font-bold text-gray-900">{summary.sections.length}</div>
            <div className="text-xs sm:text-sm text-gray-600 font-medium">Sections</div>
          </div>
          
          <div className="text-center">
            <div className="w-14 h-14 sm:w-16 sm:h-16 bg-green-100 rounded-full flex items-center justify-center mx-auto mb-3">
              <svg className="w-7 h-7 sm:w-8 sm:h-8 text-green-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z" />
              </svg>
            </div>
            <div className="text-xl sm:text-2xl font-bold text-gray-900">{formatProcessingTime(summary.processing_time)}</div>
            <div className="text-xs sm:text-sm text-gray-600 font-medium">Processing Time</div>
          </div>
          
          <div className="text-center">
            <div className="w-14 h-14 sm:w-16 sm:h-16 bg-purple-100 rounded-full flex items-center justify-center mx-auto mb-3">
              <svg className="w-7 h-7 sm:w-8 sm:h-8 text-purple-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z" />
              </svg>
            </div>
            <div className="text-xl sm:text-2xl font-bold text-gray-900">{summary.chunk_count}</div>
            <div className="text-xs sm:text-sm text-gray-600 font-medium">Chunks Analyzed</div>
          </div>
        </div>
        
        {/* Disclaimer */}
        <div className="border-t border-gray-200 pt-4 sm:pt-6">
          <div className="bg-amber-50 border border-amber-200 rounded-xl p-4 sm:p-6">
            <div className="flex items-start space-x-2 sm:space-x-3">
              <div className="flex-shrink-0">
                <svg className="w-5 h-5 sm:w-6 sm:h-6 text-amber-600 mt-0.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
                </svg>
              </div>
              <div>
                <h4 className="font-semibold text-amber-900 mb-1 text-sm sm:text-base">Important Note</h4>
                <p className="text-amber-800 leading-relaxed text-xs sm:text-sm">
                  This summary was generated by AI and may not capture all nuances of the original research paper. 
                  Please refer to the original document for complete accuracy and detailed analysis.
                </p>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}

export default SummaryDisplay