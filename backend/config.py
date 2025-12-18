"""
Configuration management for PDF Research Summarizer.
Handles environment variables and application settings.
"""

import os
from typing import Optional
from dotenv import load_dotenv
import logging

logger = logging.getLogger(__name__)

# Load environment variables from .env file
load_dotenv()

class Config:
    """Application configuration class."""
    
    def __init__(self):
        """Initialize configuration with environment variables."""
        self.gemini_api_key = self._get_required_env("GEMINI_API_KEY")
        self.backend_host = os.getenv("BACKEND_HOST", "127.0.0.1")
        self.backend_port = int(os.getenv("BACKEND_PORT", "8000"))
        self.frontend_port = int(os.getenv("FRONTEND_PORT", "5173"))
        
        # Validate configuration
        self._validate_config()
    
    def _get_required_env(self, key: str) -> str:
        """Get required environment variable or raise error."""
        value = os.getenv(key)
        if not value:
            error_msg = f"Missing required environment variable: {key}"
            logger.error(error_msg)
            raise ValueError(error_msg)
        return value
    
    def _get_optional_env(self, key: str, default: str = "") -> str:
        """Get optional environment variable with default."""
        return os.getenv(key, default)
    
    def _validate_config(self) -> None:
        """Validate configuration values."""
        if not self.gemini_api_key.strip():
            raise ValueError("GEMINI_API_KEY cannot be empty")
        
        if not (1 <= self.backend_port <= 65535):
            raise ValueError(f"Invalid BACKEND_PORT: {self.backend_port}")
        
        if not (1 <= self.frontend_port <= 65535):
            raise ValueError(f"Invalid FRONTEND_PORT: {self.frontend_port}")
        
        logger.info("Configuration validated successfully")
    
    @property
    def frontend_url(self) -> str:
        """Get frontend URL for CORS configuration."""
        return f"http://{self.backend_host}:{self.frontend_port}"
    
    @property
    def backend_url(self) -> str:
        """Get backend URL."""
        return f"http://{self.backend_host}:{self.backend_port}"

def get_config() -> Config:
    """Get application configuration instance."""
    try:
        return Config()
    except ValueError as e:
        logger.error(f"Configuration error: {str(e)}")
        raise
    except Exception as e:
        logger.error(f"Unexpected configuration error: {str(e)}")
        raise ValueError(f"Failed to load configuration: {str(e)}")

def validate_startup_config() -> dict:
    """
    Validate startup configuration and return status.
    
    Returns:
        dict: Configuration status and any error messages
    """
    try:
        config = get_config()
        return {
            "status": "success",
            "message": "Configuration loaded successfully",
            "backend_url": config.backend_url,
            "frontend_url": config.frontend_url
        }
    except ValueError as e:
        error_msg = str(e)
        if "GEMINI_API_KEY" in error_msg:
            return {
                "status": "error",
                "message": "Missing GEMINI_API_KEY environment variable",
                "details": "Please copy .env.example to .env and add your Google Gemini API key",
                "required_vars": ["GEMINI_API_KEY"]
            }
        else:
            return {
                "status": "error",
                "message": f"Configuration error: {error_msg}",
                "details": "Please check your environment variables"
            }
    except Exception as e:
        return {
            "status": "error",
            "message": f"Unexpected configuration error: {str(e)}",
            "details": "Please check your .env file and environment setup"
        }