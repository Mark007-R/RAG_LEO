from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel, Field, field_validator, ConfigDict

class DocumentUploadResponse(BaseModel):
    message: str
    doc_id: str
    filename: str
    chunks_count: int
    text_length: int
    file_size: int
    processing_time_seconds: float
    
    model_config = ConfigDict(from_attributes=True)

class DocumentInfo(BaseModel):
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
    documents: List[DocumentInfo]
    count: int
    total_size_bytes: int

class QueryRequest(BaseModel):
    query: str = Field(..., min_length=1, max_length=1000, description="User question")
    doc_id: str = Field(..., min_length=36, max_length=36, description="Document UUID")
    top_k: int = Field(default=4, ge=1, le=10, description="Number of chunks to retrieve")
    temperature: float = Field(default=0.7, ge=0.0, le=2.0, description="LLM temperature")
    max_tokens: int = Field(default=512, ge=50, le=2048, description="Maximum tokens in response")
    
    @field_validator('query')
    @classmethod
    def validate_query(cls, v: str) -> str:
        if not v.strip():
            raise ValueError('Query cannot be empty')
        return v.strip()

class RetrievedChunk(BaseModel):
    chunk_index: int
    text: str
    score: Optional[float] = None

class QueryResponse(BaseModel):
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
    error: str
    error_type: Optional[str] = None
    details: Optional[dict] = None
    timestamp: datetime = Field(default_factory=datetime.utcnow)

class HealthCheckResponse(BaseModel):
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
    message: str
    doc_id: str
    filename: str
    deleted_at: datetime

class StatsResponse(BaseModel):
    total_documents: int
    total_queries: int
    total_chunks: int
    active_documents: int
    average_processing_time_seconds: float
    average_query_time_ms: float
    storage_used_mb: float
    uptime_seconds: float
