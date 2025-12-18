# PDF Research Summarizer

A production-ready web application that accepts PDF research papers and generates comprehensive academic-style summaries using Google Gemini AI.

## 🚀 Live Demo
- **Frontend**: [https://researchsummaryai.vercel.app](https://researchsummaryai.vercel.app/)

## Features

- **PDF Text Extraction**: Extracts text from uploaded PDF research papers using PyMuPDF with pdfplumber fallback
- **Academic Section Detection**: Identifies and prioritizes key academic sections (Abstract, Introduction, Methodology, Results, Discussion, Conclusion)
- **Intelligent Chunking**: Safely handles large PDFs by chunking content to respect Gemini context limits
- **Hierarchical Summarization**: Generates structured, scholarly summaries suitable for researchers
- **Modern UI**: Beautiful, responsive React frontend with Tailwind CSS and drag-and-drop PDF upload
- **Real-time Processing**: Animated progress indicators and graceful error handling
- **Professional Design**: Academic-focused interface with gradient backgrounds and smooth animations

## Tech Stack

### Frontend
- React 18 with Vite
- Modern JavaScript (ES2022)
- Tailwind CSS v3.4 for styling
- Axios for HTTP communication
- Inter font for modern typography

### Backend
- FastAPI with Python 3.9+
- PyMuPDF (fitz) for PDF processing
- pdfplumber as fallback
- Google Generative AI SDK
- Pydantic for data validation

### AI Model
- Google Gemini 2.5 Flash (latest stable version)

## Quick Start

### Prerequisites
- Python 3.9 or higher
- Node.js 16 or higher
- Google Gemini API key

### Installation

1. **Clone the repository**
   ```bash
   git clone <repository-url>
   cd pdf-research-summarizer
   ```

2. **Set up environment variables**
   ```bash
   cp .env.example .env
   ```
   Edit `.env` and add your Google Gemini API key:
   ```
   GEMINI_API_KEY=your_actual_api_key_here
   BACKEND_HOST=127.0.0.1
   BACKEND_PORT=8000
   FRONTEND_PORT=5173
   ```

3. **Install backend dependencies**
   ```bash
   cd backend
   pip install -r requirements.txt
   ```

4. **Install frontend dependencies**
   ```bash
   cd ../frontend
   npm install
   ```

5. **Start the application**
   ```bash
   # From the root directory
   start_local.bat
   ```

   Or manually:
   ```bash
   # Terminal 1 - Backend
   cd backend
   python -m uvicorn main:app --host 127.0.0.1 --port 8000 --reload

   # Terminal 2 - Frontend
   cd frontend
   npm run dev
   ```

### Access the Application
Local Development:

- **Frontend**: http://127.0.0.1:5173
- **Backend API**: http://127.0.0.1:8000
- **API Documentation**: http://127.0.0.1:8000/docs

Production:
- **Frontend**: https://researchsummaryai.vercel.app/
- **Backend API**: https://research-paper-summarizer-w7zv.onrender.com
- **API Documentation**: https://research-paper-summarizer-w7zv.onrender.com/docs

## Usage

1. Open the application in your browser
2. Drag and drop a PDF research paper or click to browse
3. Wait for the AI to process and generate the summary
4. View the structured academic summary with sections for:
   - Problem/Research Question
   - Methods/Methodology
   - Results/Findings
   - Implications/Significance
   - Limitations/Future Work
5. Copy individual sections or the entire summary

## API Endpoints

### POST /api/summarize
Upload and summarize a PDF research paper.

**Request**: Multipart form data with PDF file
**Response**: JSON with structured summary

### GET /api/health
Check system health and configuration status.

## Architecture

The application uses a hierarchical summarization pipeline:

1. **Text Extraction**: Extract full text from PDF using PyMuPDF/pdfplumber
2. **Section Detection**: Identify academic sections using pattern matching
3. **Intelligent Chunking**: Split text into ≤10,000 character chunks with sentence boundaries
4. **Chunk Summarization**: Send each chunk to Gemini with academic prompts
5. **Final Aggregation**: Combine chunk summaries into cohesive structured output

## Configuration

### Environment Variables

- `GEMINI_API_KEY`: Your Google Gemini API key (required)
- `BACKEND_HOST`: Backend server host (default: 127.0.0.1)
- `BACKEND_PORT`: Backend server port (default: 8000)
- `FRONTEND_PORT`: Frontend development server port (default: 5173)

### File Limits

- Maximum PDF size: 50MB
- Chunk size limit: 10,000 characters
- Supported format: PDF only

## Testing

Run backend tests:
```bash
cd backend
python -m pytest test_basic.py -v
```

## Error Handling

The application includes comprehensive error handling for:
- Invalid file types and sizes
- PDF processing failures
- AI API rate limits and failures
- Network connectivity issues
- Malformed responses

## Security

- API key loaded exclusively from environment variables
- CORS properly configured for frontend communication
- File type and size validation
- No authentication required (stateless operation)

## Performance

- Concurrent chunk processing with rate limiting
- Exponential backoff for API retries
- Memory-efficient PDF processing
- Responsive UI with loading states

## Limitations

- Requires Google Gemini API key
- Processing time depends on PDF size and complexity
- AI-generated summaries may not capture all nuances
- No persistent storage (stateless operation)

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests if applicable
5. Submit a pull request

## License

This project is licensed under the MIT License.

## Support

For issues and questions:
1. Check the API health endpoint: https://research-paper-summarizer-w7zv.onrender.com/api/health
2. Review the console logs for error details
3. Ensure your Gemini API key is valid and has quota
4. Verify all dependencies are installed correctly