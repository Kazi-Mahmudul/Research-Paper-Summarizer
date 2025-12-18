import React, { useState } from 'react'
import axios from 'axios'
import FileUpload from './components/FileUpload'
import SummaryDisplay from './components/SummaryDisplay'

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://127.0.0.1:8000'

function App() {
  const [summary, setSummary] = useState(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState(null)

  const handleFileUpload = async (file) => {
    setLoading(true)
    setError(null)
    setSummary(null)

    try {
      const formData = new FormData()
      formData.append('file', file)

      const response = await axios.post(`${API_BASE_URL}/api/summarize`, formData, {
        headers: {
          'Content-Type': 'multipart/form-data',
        },
        timeout: 300000, // 5 minutes timeout
      })

      setSummary(response.data)
    } catch (err) {
      console.error('Upload error:', err)
      
      if (err.response) {
        // Server responded with error status
        const errorMessage = err.response.data?.error || err.response.data?.detail || 'Server error occurred'
        setError(`Error: ${errorMessage}`)
      } else if (err.request) {
        // Request was made but no response received
        setError('No response from server. Please check if the backend is running.')
      } else {
        // Something else happened
        setError(`Upload failed: ${err.message}`)
      }
    } finally {
      setLoading(false)
    }
  }

  const handleReset = () => {
    setSummary(null)
    setError(null)
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-gray-50 via-blue-50 to-indigo-100">
      {/* Header */}
      <header className="relative overflow-hidden bg-white shadow-sm border-b border-gray-200">
        <div className="absolute inset-0 bg-gradient-to-r from-blue-600/5 to-indigo-600/5"></div>
        <div className="relative max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-12 text-center">
          <div className="space-y-4">
            <h1 className="text-4xl md:text-5xl font-bold text-gray-900 tracking-tight">
              PDF Research
              <span className="text-transparent bg-clip-text bg-gradient-to-r from-blue-600 to-indigo-600 ml-3">
                Summarizer
              </span>
            </h1>
            <p className="text-xl text-gray-600 max-w-3xl mx-auto leading-relaxed">
              Upload a research paper PDF to generate an AI-powered academic summary using 
              <span className="font-semibold text-blue-600"> AI</span>
            </p>
            <div className="flex items-center justify-center space-x-6 text-sm text-gray-500 pt-2">
              <div className="flex items-center space-x-2">
                <div className="w-2 h-2 bg-green-500 rounded-full"></div>
                <span>Academic Structure Detection</span>
              </div>
              <div className="flex items-center space-x-2">
                <div className="w-2 h-2 bg-blue-500 rounded-full"></div>
                <span>Hierarchical Summarization</span>
              </div>
              <div className="flex items-center space-x-2">
                <div className="w-2 h-2 bg-purple-500 rounded-full"></div>
                <span>AI-Powered Analysis</span>
              </div>
            </div>
          </div>
        </div>
      </header>

      {/* Main Content */}
      <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-12">
        {!summary && !loading && (
          <div className="animate-fade-in">
            <FileUpload 
              onFileUpload={handleFileUpload}
              loading={loading}
              error={error}
            />
          </div>
        )}

        {loading && (
          <div className="flex flex-col items-center justify-center py-20 animate-fade-in">
            <div className="relative">
              <div className="w-16 h-16 border-4 border-blue-200 border-t-blue-600 rounded-full animate-spin"></div>
              <div className="absolute inset-0 w-16 h-16 border-4 border-transparent border-r-indigo-600 rounded-full animate-spin animation-delay-150"></div>
            </div>
            <div className="mt-8 text-center space-y-3">
              <h3 className="text-2xl font-semibold text-gray-900">Processing your PDF...</h3>
              <p className="text-gray-600 max-w-md">
                This may take a few minutes while we extract text, detect sections, and generate your summary.
              </p>
              <div className="flex items-center justify-center space-x-4 text-sm text-gray-500 pt-4">
                <div className="flex items-center space-x-2">
                  <div className="w-2 h-2 bg-blue-500 rounded-full animate-pulse"></div>
                  <span>Extracting text</span>
                </div>
                <div className="flex items-center space-x-2">
                  <div className="w-2 h-2 bg-indigo-500 rounded-full animate-pulse animation-delay-300"></div>
                  <span>Analyzing structure</span>
                </div>
                <div className="flex items-center space-x-2">
                  <div className="w-2 h-2 bg-purple-500 rounded-full animate-pulse animation-delay-500"></div>
                  <span>Generating summary</span>
                </div>
              </div>
            </div>
          </div>
        )}

        {error && !loading && (
          <div className="max-w-md mx-auto animate-slide-up">
            <div className="card p-8 border-red-200 bg-red-50">
              <div className="text-center space-y-4">
                <div className="w-16 h-16 bg-red-100 rounded-full flex items-center justify-center mx-auto">
                  <svg className="w-8 h-8 text-red-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-2.5L13.732 4c-.77-.833-1.964-.833-2.732 0L3.732 16.5c-.77.833.192 2.5 1.732 2.5z" />
                  </svg>
                </div>
                <div>
                  <h3 className="text-xl font-semibold text-red-900 mb-2">Upload Error</h3>
                  <p className="text-red-700 leading-relaxed">{error}</p>
                </div>
                <button 
                  onClick={handleReset}
                  className="btn-primary bg-red-600 hover:bg-red-700 focus:ring-red-500"
                >
                  Try Again
                </button>
              </div>
            </div>
          </div>
        )}

        {summary && !loading && (
          <div className="animate-fade-in">
            <SummaryDisplay 
              summary={summary}
              onReset={handleReset}
            />
          </div>
        )}
      </main>

      {/* Footer */}
      <footer className="bg-white border-t border-gray-200 mt-20">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
          <div className="text-center space-y-4">
            <p className="text-gray-600">
              Powered by 
              <span className="font-semibold text-blue-600 mx-1">Google Gemini AI</span>
              • Built with 
              <span className="font-semibold text-cyan-600 mx-1">React</span>
              & 
              <span className="font-semibold text-green-600 mx-1">FastAPI</span>
            </p>
            <div className="flex items-center justify-center space-x-6 text-sm text-gray-500">
              <a href="#" className="hover:text-gray-700 transition-colors">Documentation</a>
              <a href="#" className="hover:text-gray-700 transition-colors">API Reference</a>
              <a href="#" className="hover:text-gray-700 transition-colors">GitHub</a>
            </div>
          </div>
        </div>
      </footer>
    </div>
  )
}

export default App