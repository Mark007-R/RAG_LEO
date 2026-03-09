import hashlib
import logging
from functools import wraps
from typing import Optional
from flask import request, jsonify, g
from datetime import datetime

from .config import settings
from .exceptions import AuthenticationError, RateLimitError

logger = logging.getLogger(__name__)

def require_api_key(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not settings.API_KEY_ENABLED:
            return f(*args, **kwargs)
        
        api_key = get_api_key_from_request()
        if not api_key:
            logger.warning(f"Missing API key from {request.remote_addr}")
            raise AuthenticationError("API key required. Provide via Authorization header or X-API-Key header.")
        
        valid_keys = settings.get_api_keys_list()
        if not verify_api_key(api_key, valid_keys):
            logger.warning(f"Invalid API key attempt from {request.remote_addr}")
            raise AuthenticationError("Invalid API key")
        
        g.api_key = api_key
        g.authenticated = True
        
        return f(*args, **kwargs)
    
    return decorated_function

class RequestValidator:
        file.seek(0, 2)  # Seek to end
        file_size = file.tell()
        file.seek(0)  # Reset to beginning
        
        if file_size > settings.MAX_CONTENT_LENGTH:
            from exceptions import FileSizeError
            max_mb = settings.MAX_CONTENT_LENGTH / (1024 * 1024)
            raise FileSizeError(f"File size exceeds {max_mb:.1f}MB limit")
    
    @staticmethod
    def validate_file_extension(filename: str) -> None:
        allowed_types = ['application/pdf', 'application/octet-stream']
        if content_type not in allowed_types:
            from exceptions import FileTypeError
            raise FileTypeError(f"Content type {content_type} not allowed")

def sanitize_filename(filename: str) -> str: