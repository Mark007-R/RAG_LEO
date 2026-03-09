"""
Pydantic schemas for request/response validation.
Ensures type safety and data validation across API endpoints.
"""
from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel, Field, field_validator, ConfigDict


class DocumentUploadResponse(BaseModel):
    """Response schema for document upload."""
    message: str
    doc_id: str
    filename: str
    chunks_count: int
    text_length: int
    file_size: int
    processing_time_seconds: float
    
    model_config = ConfigDict(from_attributes=True)


class DocumentInfo(BaseModel):
    """Schema for document information."""
    id: int
    doc_id: str
    filename: str
    file_size: int
    status: str
    chunks_count: Optional[int] = None
    text_length: Optional[int] = None
    created_at: datetime
    updated_at: datetime
    last_accessed_at: Optional[datetime] = None
    
    model_config = ConfigDict(from_attributes=True)


class DocumentListResponse(BaseModel):
    """Response schema for listing documents."""
    documents: List[DocumentInfo]
    count: int
    total_size_bytes: int


class QueryRequest(BaseModel):
    """Request schema for query endpoint."""
    query: str = Field(..., min_length=1, max_length=1000, description="User question")
    doc_id: str = Field(..., min_length=36, max_length=36, description="Document UUID")
    top_k: int = Field(default=4, ge=1, le=10, description="Number of chunks to retrieve")
    temperature: float = Field(default=0.7, ge=0.0, le=2.0, description="LLM temperature")
    max_tokens: int = Field(default=512, ge=50, le=2048, description="Maximum tokens in response")
    
    @field_validator('query')
    @classmethod
    def validate_query(cls, v: str) -> str:
        """Validate query is not empty or whitespace."""
        if not v.strip():
            raise ValueError('Query cannot be empty')
        return v.strip()


class RetrievedChunk(BaseModel):
    """Schema for retrieved text chunk."""
    chunk_index: int
    text: str
    score: Optional[float] = None


class QueryResponse(BaseModel):
    """Response schema for query endpoint."""
    query_id: str
    answer: str
    retrieved_chunks: List[str]
    doc_id: str
    filename: str
    query: str
    retrieval_time_ms: float
    generation_time_ms: float
    total_time_ms: float


class ErrorResponse(BaseModel):
    """Schema for error responses."""
    error: str
    error_type: Optional[str] = None
    details: Optional[dict] = None
    timestamp: datetime = Field(default_factory=datetime.utcnow)


class HealthCheckResponse(BaseModel):
    """Response schema for health check endpoint."""
    status: str
    app_name: str
    version: str
    environment: str
    timestamp: datetime
    uptime_seconds: float
    documents_count: int
    queries_count: int
    database_status: str
    pipeline_status: str
    disk_usage_mb: float


class DocumentDeleteResponse(BaseModel):
    """Response schema for document deletion."""
    message: str
    doc_id: str
    filename: str
    deleted_at: datetime


class StatsResponse(BaseModel):
    """Response schema for statistics endpoint."""
    total_documents: int
    total_queries: int
    total_chunks: int
    active_documents: int
    average_processing_time_seconds: float
    average_query_time_ms: float
    storage_used_mb: float
    uptime_seconds: float


class BulkDeleteRequest(BaseModel):
    """Request schema for bulk delete."""
    doc_ids: List[str] = Field(..., min_length=1, max_length=100)
    
    @field_validator('doc_ids')
    @classmethod
    def validate_doc_ids(cls, v: List[str]) -> List[str]:
        """Validate all doc_ids are valid UUIDs."""
        for doc_id in v:
            if len(doc_id) != 36:
                raise ValueError(f'Invalid document ID format: {doc_id}')
        return v


class BulkDeleteResponse(BaseModel):
    """Response schema for bulk delete."""
    message: str
    deleted_count: int
    failed_count: int
    deleted_doc_ids: List[str]
    failed_doc_ids: List[str]
