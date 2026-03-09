"""
Custom exceptions for better error handling.
Provides specific exceptions with proper HTTP status codes.
"""


class RAGLeoException(Exception):
    """Base exception for all RAG_LEO errors."""
    status_code = 500
    error_type = "internal_error"
    
    def __init__(self, message: str, details: dict = None):
        self.message = message
        self.details = details or {}
        super().__init__(self.message)


class ValidationError(RAGLeoException):
    """Raised when input validation fails."""
    status_code = 400
    error_type = "validation_error"


class DocumentNotFoundError(RAGLeoException):
    """Raised when document is not found."""
    status_code = 404
    error_type = "document_not_found"


class DocumentAlreadyExistsError(RAGLeoException):
    """Raised when trying to create duplicate document."""
    status_code = 409
    error_type = "document_exists"


class FileUploadError(RAGLeoException):
    """Raised when file upload fails."""
    status_code = 400
    error_type = "upload_error"


class FileTypeError(RAGLeoException):
    """Raised when file type is not allowed."""
    status_code = 400
    error_type = "invalid_file_type"


class FileSizeError(RAGLeoException):
    """Raised when file size exceeds limit."""
    status_code = 413
    error_type = "file_too_large"


class PDFExtractionError(RAGLeoException):
    """Raised when PDF text extraction fails."""
    status_code = 422
    error_type = "extraction_error"


class IndexNotFoundError(RAGLeoException):
    """Raised when FAISS index is not found."""
    status_code = 404
    error_type = "index_not_found"


class IndexBuildError(RAGLeoException):
    """Raised when FAISS index building fails."""
    status_code = 500
    error_type = "index_build_error"


class RetrievalError(RAGLeoException):
    """Raised when document retrieval fails."""
    status_code = 500
    error_type = "retrieval_error"


class GenerationError(RAGLeoException):
    """Raised when answer generation fails."""
    status_code = 500
    error_type = "generation_error"


class DatabaseError(RAGLeoException):
    """Raised when database operation fails."""
    status_code = 500
    error_type = "database_error"


class AuthenticationError(RAGLeoException):
    """Raised when authentication fails."""
    status_code = 401
    error_type = "authentication_error"


class AuthorizationError(RAGLeoException):
    """Raised when authorization fails."""
    status_code = 403
    error_type = "authorization_error"


class RateLimitError(RAGLeoException):
    """Raised when rate limit is exceeded."""
    status_code = 429
    error_type = "rate_limit_exceeded"


class ConfigurationError(RAGLeoException):
    """Raised when configuration is invalid."""
    status_code = 500
    error_type = "configuration_error"


class ExternalServiceError(RAGLeoException):
    """Raised when external service (Groq API) fails."""
    status_code = 503
    error_type = "external_service_error"
