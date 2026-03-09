"""
Security middleware for authentication, authorization, and rate limiting.
"""
import hashlib
import logging
from functools import wraps
from typing import Optional
from flask import request, jsonify, g
from datetime import datetime

from config import settings
from exceptions import AuthenticationError, RateLimitError

logger = logging.getLogger(__name__)


def hash_api_key(api_key: str) -> str:
    """Hash API key for secure storage."""
    return hashlib.sha256(api_key.encode()).hexdigest()


def verify_api_key(provided_key: str, valid_keys: list) -> bool:
    """Verify if provided API key is valid."""
    if not valid_keys:
        return False
    return provided_key in valid_keys


def get_api_key_from_request() -> Optional[str]:
    """Extract API key from request headers or query parameters."""
    # Check Authorization header
    auth_header = request.headers.get('Authorization', '')
    if auth_header.startswith('Bearer '):
        return auth_header[7:]
    
    # Check X-API-Key header
    api_key = request.headers.get('X-API-Key')
    if api_key:
        return api_key
    
    # Check query parameter (less secure, but convenient for testing)
    api_key = request.args.get('api_key')
    if api_key:
        return api_key
    
    return None


def require_api_key(f):
    """
    Decorator to require API key authentication.
    Usage: @require_api_key
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        # Skip if API key authentication is disabled
        if not settings.API_KEY_ENABLED:
            return f(*args, **kwargs)
        
        # Get API key from request
        api_key = get_api_key_from_request()
        if not api_key:
            logger.warning(f"Missing API key from {request.remote_addr}")
            raise AuthenticationError("API key required. Provide via Authorization header or X-API-Key header.")
        
        # Verify API key
        valid_keys = settings.get_api_keys_list()
        if not verify_api_key(api_key, valid_keys):
            logger.warning(f"Invalid API key attempt from {request.remote_addr}")
            raise AuthenticationError("Invalid API key")
        
        # Store validated key info in request context
        g.api_key = api_key
        g.authenticated = True
        
        return f(*args, **kwargs)
    
    return decorated_function


def log_request():
    """Log incoming request details."""
    logger.info(f"{request.method} {request.path} - {request.remote_addr}")


def log_response(response):
    """Log outgoing response details."""
    logger.info(f"Response {response.status_code} - {request.path}")
    return response


class RequestValidator:
    """Validate incoming requests."""
    
    @staticmethod
    def validate_file_size(file) -> None:
        """Validate uploaded file size."""
        file.seek(0, 2)  # Seek to end
        file_size = file.tell()
        file.seek(0)  # Reset to beginning
        
        if file_size > settings.MAX_CONTENT_LENGTH:
            from exceptions import FileSizeError
            max_mb = settings.MAX_CONTENT_LENGTH / (1024 * 1024)
            raise FileSizeError(f"File size exceeds {max_mb:.1f}MB limit")
    
    @staticmethod
    def validate_file_extension(filename: str) -> None:
        """Validate file extension."""
        if not filename or '.' not in filename:
            from exceptions import FileTypeError
            raise FileTypeError("Invalid filename")
        
        ext = filename.rsplit('.', 1)[1].lower()
        allowed_extensions = settings.ALLOWED_EXTENSIONS.split(',')
        
        if ext not in allowed_extensions:
            from exceptions import FileTypeError
            raise FileTypeError(f"File type .{ext} not allowed. Allowed types: {', '.join(allowed_extensions)}")
    
    @staticmethod
    def validate_content_type(content_type: str) -> None:
        """Validate content type."""
        allowed_types = ['application/pdf', 'application/octet-stream']
        if content_type not in allowed_types:
            from exceptions import FileTypeError
            raise FileTypeError(f"Content type {content_type} not allowed")


def sanitize_filename(filename: str) -> str:
    """Sanitize filename to prevent directory traversal."""
    # Remove any path components
    filename = filename.replace('\\', '_').replace('/', '_')
    
    # Remove potentially dangerous characters
    dangerous_chars = ['..', '<', '>', ':', '"', '|', '?', '*']
    for char in dangerous_chars:
        filename = filename.replace(char, '_')
    
    return filename
