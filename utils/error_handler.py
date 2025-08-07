"""
Unified error handling for fo.ai application
"""

from typing import Dict, Any, Optional
from fastapi import HTTPException
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class FoAIError(Exception):
    """Base exception for fo.ai application"""
    def __init__(self, message: str, error_code: str = "UNKNOWN_ERROR", details: Optional[Dict] = None):
        self.message = message
        self.error_code = error_code
        self.details = details or {}
        super().__init__(self.message)

class AWSConnectionError(FoAIError):
    """Raised when AWS services are not accessible"""
    def __init__(self, service: str, region: str, details: Optional[Dict] = None):
        super().__init__(
            f"Failed to connect to AWS {service} in region {region}",
            "AWS_CONNECTION_ERROR",
            details
        )

class DataFetchError(FoAIError):
    """Raised when data fetching fails"""
    def __init__(self, service: str, details: Optional[Dict] = None):
        super().__init__(
            f"Failed to fetch data from {service}",
            "DATA_FETCH_ERROR",
            details
        )

class LLMError(FoAIError):
    """Raised when LLM operations fail"""
    def __init__(self, operation: str, details: Optional[Dict] = None):
        super().__init__(
            f"LLM operation failed: {operation}",
            "LLM_ERROR",
            details
        )

class RedisError(FoAIError):
    """Raised when Redis operations fail"""
    def __init__(self, operation: str, details: Optional[Dict] = None):
        super().__init__(
            f"Redis operation failed: {operation}",
            "REDIS_ERROR",
            details
        )

def handle_aws_error(func):
    """Decorator to handle AWS API errors"""
    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except Exception as e:
            logger.error(f"AWS error in {func.__name__}: {e}")
            raise AWSConnectionError(
                service=func.__name__,
                region=kwargs.get('region', 'unknown'),
                details={'original_error': str(e)}
            )
    return wrapper

def handle_llm_error(func):
    """Decorator to handle LLM errors"""
    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except Exception as e:
            logger.error(f"LLM error in {func.__name__}: {e}")
            raise LLMError(
                operation=func.__name__,
                details={'original_error': str(e)}
            )
    return wrapper

def handle_redis_error(func):
    """Decorator to handle Redis errors"""
    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except Exception as e:
            logger.error(f"Redis error in {func.__name__}: {e}")
            raise RedisError(
                operation=func.__name__,
                details={'original_error': str(e)}
            )
    return wrapper

def create_error_response(error: FoAIError) -> Dict[str, Any]:
    """Create a standardized error response"""
    return {
        "error": True,
        "message": error.message,
        "error_code": error.error_code,
        "details": error.details
    }

def create_success_response(data: Any, message: str = "Success") -> Dict[str, Any]:
    """Create a standardized success response"""
    return {
        "error": False,
        "message": message,
        "data": data
    } 