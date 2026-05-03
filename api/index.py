"""
Vercel deployment entry point for PDF Research Summarizer.
Exports the FastAPI app for serverless deployment.
"""

from main import app

# Export the FastAPI app for Vercel
app = app