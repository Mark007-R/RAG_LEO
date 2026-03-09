

class RAGLeoException(Exception):
    status_code = 500
    error_type = "internal_error"
    
    def __init__(self, message: str, details: dict = None):
        self.message = message
        self.details = details or {}
        super().__init__(self.message)

class ValidationError(RAGLeoException):
    status_code = 400
    error_type = "validation_error"

class DocumentNotFoundError(RAGLeoException):
    status_code = 404
    error_type = "document_not_found"

class DocumentAlreadyExistsError(RAGLeoException):
    status_code = 409
    error_type = "document_exists"

class FileUploadError(RAGLeoException):
    status_code = 400
    error_type = "upload_error"

class FileTypeError(RAGLeoException):
    status_code = 400
    error_type = "invalid_file_type"

class FileSizeError(RAGLeoException):
    status_code = 413
    error_type = "file_too_large"

class PDFExtractionError(RAGLeoException):
    status_code = 422
    error_type = "extraction_error"

class IndexNotFoundError(RAGLeoException):
    status_code = 404
    error_type = "index_not_found"

class IndexBuildError(RAGLeoException):
    status_code = 500
    error_type = "index_build_error"

class RetrievalError(RAGLeoException):
    status_code = 500
    error_type = "retrieval_error"

class GenerationError(RAGLeoException):
    status_code = 500
    error_type = "generation_error"

class DatabaseError(RAGLeoException):
    status_code = 500
    error_type = "database_error"

class AuthenticationError(RAGLeoException):
    status_code = 401
    error_type = "authentication_error"

class AuthorizationError(RAGLeoException):
    status_code = 403
    error_type = "authorization_error"

class RateLimitError(RAGLeoException):
    status_code = 429
    error_type = "rate_limit_exceeded"

class ConfigurationError(RAGLeoException):
    status_code = 500
    error_type = "configuration_error"

class ExternalServiceError(RAGLeoException):
    status_code = 503
    error_type = "external_service_error"
