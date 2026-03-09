from datetime import datetime
from typing import Optional
from sqlalchemy import String, Integer, DateTime, Text, Float, Boolean, Index
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column

class Base(DeclarativeBase):
    pass

class Document(Base):
    __tablename__ = "documents"
    
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    doc_id: Mapped[str] = mapped_column(String(36), unique=True, nullable=False, index=True)
    filename: Mapped[str] = mapped_column(String(255), nullable=False)
    original_filename: Mapped[str] = mapped_column(String(255), nullable=False)
    file_path: Mapped[str] = mapped_column(String(500), nullable=False)
    file_size: Mapped[int] = mapped_column(Integer, nullable=False)
    mime_type: Mapped[str] = mapped_column(String(100), default="application/pdf")
    status: Mapped[str] = mapped_column(String(50), default="pending")
    chunks_count: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    text_length: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    embedding_dim: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    index_path: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    chunks_path: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    last_accessed_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    page_count: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    processing_time_seconds: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    error_message: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    is_deleted: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    deleted_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    
    __table_args__ = (
        Index('idx_status', 'status'),
        Index('idx_created_at', 'created_at'),
        Index('idx_is_deleted', 'is_deleted'),
    )
    
    def __repr__(self) -> str:
        return f"<Document(doc_id={self.doc_id}, filename={self.original_filename}, status={self.status})>"
    
    def to_dict(self) -> dict:
        return {
            'id': self.id,
            'doc_id': self.doc_id,
            'filename': self.original_filename,
            'file_size': self.file_size,
            'status': self.status,
            'chunks_count': self.chunks_count,
            'text_length': self.text_length,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
            'last_accessed_at': self.last_accessed_at.isoformat() if self.last_accessed_at else None,
        }

class Query(Base):
    __tablename__ = "queries"
    
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    query_id: Mapped[str] = mapped_column(String(36), unique=True, nullable=False, index=True)
    doc_id: Mapped[str] = mapped_column(String(36), nullable=False, index=True)
    query_text: Mapped[str] = mapped_column(Text, nullable=False)
    answer_text: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    retrieval_time_ms: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    generation_time_ms: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    total_time_ms: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    top_k: Mapped[int] = mapped_column(Integer, default=4)
    chunks_retrieved: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    status: Mapped[str] = mapped_column(String(50), default="success")
    error_message: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False, index=True)
    user_id: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    ip_address: Mapped[Optional[str]] = mapped_column(String(45), nullable=True)
    
    def __repr__(self) -> str:
        return f"<Query(query_id={self.query_id}, doc_id={self.doc_id}, status={self.status})>"
    
    def to_dict(self) -> dict:
        return {
            'id': self.id,
            'query_id': self.query_id,
            'doc_id': self.doc_id,
            'query_text': self.query_text,
            'answer_text': self.answer_text,
            'total_time_ms': self.total_time_ms,
            'status': self.status,
            'created_at': self.created_at.isoformat() if self.created_at else None,
        }

class APIKey(Base):
    __tablename__ = "api_keys"
    
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    key_hash: Mapped[str] = mapped_column(String(256), unique=True, nullable=False, index=True)
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    request_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    last_used_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)
    expires_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    rate_limit_per_minute: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    
    def __repr__(self) -> str:
        return f"<APIKey(name={self.name}, is_active={self.is_active})>"
    
    def is_valid(self) -> bool:
        if not self.is_active:
            return False
        if self.expires_at and self.expires_at < datetime.utcnow():
            return False
        return True
