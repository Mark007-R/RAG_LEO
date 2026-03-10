import re
from werkzeug.datastructures import FileStorage

from .config import settings
from .exceptions import FileSizeError, FileTypeError


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