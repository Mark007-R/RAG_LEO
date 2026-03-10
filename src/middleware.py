import hashlib
import logging
import re
from functools import wraps
from typing import Optional
from flask import request, jsonify, g
from datetime import datetime
from werkzeug.datastructures import FileStorage

from .config import settings
from .exceptions import AuthenticationError, RateLimitError, FileSizeError, FileTypeError

logger = logging.getLogger(__name__)


def get_api_key_from_request() -> Optional[str]:
    """Extract API key from request headers."""
    api_key = request.headers.get('Authorization')
    if api_key:
        if api_key.startswith('Bearer '):
            return api_key[7:]
        return api_key
    
    return request.headers.get('X-API-Key')


def verify_api_key(api_key: str, valid_keys: list) -> bool:
    """Verify if the provided API key is valid."""
    if not valid_keys:
        return True
    return api_key in valid_keys


def require_api_key(f):
    """Decorator to require API key authentication."""
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
    """Validator for request data."""
    
    @staticmethod
    def validate_file_size(file: FileStorage) -> None:
        """Validate that file size doesn't exceed maximum."""
        file.seek(0, 2)  # Seek to end
        file_size = file.tell()
        file.seek(0)  # Reset to beginning
        
        if file_size > settings.MAX_CONTENT_LENGTH:
            max_mb = settings.MAX_CONTENT_LENGTH / (1024 * 1024)
            raise FileSizeError(f"File size exceeds {max_mb:.1f}MB limit")
    
    @staticmethod
    def validate_file_extension(filename: str) -> None:
        """Validate that file extension is allowed."""
        allowed_extensions = settings.ALLOWED_EXTENSIONS.split(',')
        allowed_extensions = [ext.strip().lower() for ext in allowed_extensions]
        
        file_ext = filename.rsplit('.', 1)[-1].lower() if '.' in filename else ''
        
        if file_ext not in allowed_extensions:
            raise FileTypeError(f"File type '.{file_ext}' not allowed. Allowed types: {', '.join(allowed_extensions)}")
    
    @staticmethod
    def validate_file_type(content_type: str) -> None:
        """Validate that content type is allowed."""
        allowed_types = ['application/pdf', 'application/octet-stream']
        if content_type not in allowed_types:
            raise FileTypeError(f"Content type {content_type} not allowed")


def sanitize_filename(filename: str) -> str:
    """Sanitize filename to prevent path traversal and other issues."""
    # Remove path components
    filename = filename.replace('\\', '/').split('/')[-1]
    
    # Remove non-alphanumeric characters except dots, hyphens, and underscores
    filename = re.sub(r'[^\w\s.-]', '', filename)
    
    # Replace spaces with underscores
    filename = filename.replace(' ', '_')
    
    # Limit length
    max_length = 255
    if len(filename) > max_length:
        name, ext = filename.rsplit('.', 1) if '.' in filename else (filename, '')
        name = name[:max_length - len(ext) - 1]
        filename = f"{name}.{ext}" if ext else name
    
    return filename