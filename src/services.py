"""
Business logic services for document and query operations.
Separates business logic from route handlers for better testability.
"""
import os
import time
import uuid
import logging
from pathlib import Path
from typing import Optional, List, Tuple
from datetime import datetime

from werkzeug.utils import secure_filename
from werkzeug.datastructures import FileStorage

from config import settings
from database import db_manager
from models import Document, Query
from rag_pipeline import RAGPipeline
from exceptions import (
    DocumentNotFoundError,
    FileUploadError,
    PDFExtractionError,
    IndexBuildError,
    ValidationError,
)
from middleware import RequestValidator, sanitize_filename

logger = logging.getLogger(__name__)


class DocumentService:
    """Service for document management operations."""
    
    def __init__(self):
        """Initialize document service."""
        self.pipeline = RAGPipeline()
        self.upload_folder = settings.get_upload_path()
        self.upload_folder.mkdir(exist_ok=True)
    
    def upload_document(self, file: FileStorage) -> Tuple[Document, dict]:
        """
        Upload and process a PDF document.
        
        Args:
            file: FileStorage object from Flask request
            
        Returns:
            Tuple of (Document model, processing stats)
            
        Raises:
            FileUploadError: If upload fails
            PDFExtractionError: If PDF processing fails
        """
        start_time = time.time()
        
        # Validate file
        if not file or file.filename == '':
            raise FileUploadError("No file provided")
        
        RequestValidator.validate_file_extension(file.filename)
        RequestValidator.validate_file_size(file)
        
        # Generate unique document ID
        doc_id = str(uuid.uuid4())
        original_filename = secure_filename(file.filename)
        original_filename = sanitize_filename(original_filename)
        save_filename = f"{doc_id}__{original_filename}"
        save_path = self.upload_folder / save_filename
        
        try:
            # Save file
            file.save(str(save_path))
            file_size = save_path.stat().st_size
            logger.info(f"Saved file: {save_filename} ({file_size} bytes)")
            
            # Create database record
            with db_manager.get_session() as session:
                document = db_manager.create_document(
                    session,
                    doc_id=doc_id,
                    filename=save_filename,
                    original_filename=original_filename,
                    file_path=str(save_path),
                    file_size=file_size,
                    status="processing"
                )
            
            # Process PDF
            try:
                text = self.pipeline.extract_text_from_pdf(str(save_path))
                
                if not text or len(text.strip()) == 0:
                    self._cleanup_failed_upload(doc_id, save_path)
                    raise PDFExtractionError("No text could be extracted from PDF")
                
                chunks = self.pipeline.chunk_text(
                    text,
                    chunk_size=settings.CHUNK_SIZE,
                    chunk_overlap=settings.CHUNK_OVERLAP
                )
                
                if not chunks:
                    self._cleanup_failed_upload(doc_id, save_path)
                    raise PDFExtractionError("Failed to create text chunks")
                
                # Build FAISS index
                index = self.pipeline.build_faiss_index(doc_id, persist=True)
                
                # Update document record
                processing_time = time.time() - start_time
                
                index_path = settings.get_index_path() / f"{doc_id}.index"
                chunks_path = settings.get_metadata_path() / f"{doc_id}_chunks.pkl"
                
                with db_manager.get_session() as session:
                    document = db_manager.update_document(
                        session,
                        doc_id=doc_id,
                        status="completed",
                        chunks_count=len(chunks),
                        text_length=len(text),
                        embedding_dim=self.pipeline.embedding_dim,
                        index_path=str(index_path),
                        chunks_path=str(chunks_path),
                        processing_time_seconds=processing_time
                    )
                
                stats = {
                    'chunks_count': len(chunks),
                    'text_length': len(text),
                    'file_size': file_size,
                    'processing_time_seconds': round(processing_time, 2)
                }
                
                logger.info(f"Successfully processed document {doc_id} in {processing_time:.2f}s")
                return document, stats
                
            except Exception as e:
                # Update status to failed
                with db_manager.get_session() as session:
                    db_manager.update_document(
                        session,
                        doc_id=doc_id,
                        status="failed",
                        error_message=str(e)
                    )
                raise PDFExtractionError(f"PDF processing failed: {str(e)}")
        
        except Exception as e:
            # Clean up on failure
            if save_path.exists():
                save_path.unlink()
            raise
    
    def _cleanup_failed_upload(self, doc_id: str, file_path: Path):
        """Clean up files and database record after failed upload."""
        try:
            if file_path.exists():
                file_path.unlink()
            
            with db_manager.get_session() as session:
                db_manager.delete_document(session, doc_id, soft_delete=False)
        except Exception as e:
            logger.error(f"Cleanup failed for {doc_id}: {e}")
    
    def get_document(self, doc_id: str) -> Document:
        """Get document by ID."""
        with db_manager.get_session() as session:
            document = db_manager.get_document_by_id(session, doc_id)
            if not document:
                raise DocumentNotFoundError(f"Document not found: {doc_id}")
            return document
    
    def list_documents(self) -> List[Document]:
        """List all documents."""
        with db_manager.get_session() as session:
            return db_manager.get_all_documents(session)
    
    def delete_document(self, doc_id: str) -> Document:
        """Delete document and associated files."""
        with db_manager.get_session() as session:
            document = db_manager.get_document_by_id(session, doc_id)
            if not document:
                raise DocumentNotFoundError(f"Document not found: {doc_id}")
            
            # Delete files
            try:
                # Delete uploaded file
                if document.file_path and Path(document.file_path).exists():
                    Path(document.file_path).unlink()
                    logger.info(f"Deleted file: {document.file_path}")
                
                # Delete index file
                if document.index_path and Path(document.index_path).exists():
                    Path(document.index_path).unlink()
                    logger.info(f"Deleted index: {document.index_path}")
                
                # Delete chunks file
                if document.chunks_path and Path(document.chunks_path).exists():
                    Path(document.chunks_path).unlink()
                    logger.info(f"Deleted chunks: {document.chunks_path}")
            
            except Exception as e:
                logger.error(f"Error deleting files for {doc_id}: {e}")
            
            # Soft delete from database
            document = db_manager.delete_document(session, doc_id, soft_delete=True)
            return document


class QueryService:
    """Service for query operations."""
    
    def __init__(self):
        """Initialize query service."""
        self.pipeline = RAGPipeline()
    
    def execute_query(
        self,
        doc_id: str,
        query_text: str,
        top_k: int = None,
        temperature: float = None,
        max_tokens: int = None
    ) -> Tuple[Query, dict]:
        """
        Execute RAG query on document.
        
        Args:
            doc_id: Document ID to query
            query_text: User query
            top_k: Number of chunks to retrieve
            temperature: LLM temperature
            max_tokens: Maximum tokens in response
            
        Returns:
            Tuple of (Query model, response data)
        """
        # Use defaults from settings if not provided
        top_k = top_k or settings.TOP_K_RETRIEVAL
        temperature = temperature if temperature is not None else settings.LLM_TEMPERATURE
        max_tokens = max_tokens or settings.LLM_MAX_TOKENS
        
        # Validate document exists
        with db_manager.get_session() as session:
            document = db_manager.get_document_by_id(session, doc_id)
            if not document:
                raise DocumentNotFoundError(f"Document not found: {doc_id}")
            
            if document.status != "completed":
                raise ValidationError(f"Document is not ready for querying. Status: {document.status}")
        
        # Load index if needed
        if self.pipeline.doc_id != doc_id:
            logger.info(f"Loading index for document {doc_id}")
            try:
                self.pipeline.load_index(doc_id)
            except FileNotFoundError:
                raise DocumentNotFoundError("Document index not found. Please re-upload the document.")
        
        # Execute retrieval and generation
        retrieval_start = time.time()
        retrieved_chunks = self.pipeline.retrieve(query_text, top_k=top_k)
        retrieval_time_ms = (time.time() - retrieval_start) * 1000
        
        generation_start = time.time()
        answer = self.pipeline.generate_answer(
            query_text,
            retrieved_chunks,
            temperature=temperature,
            max_tokens=max_tokens
        )
        generation_time_ms = (time.time() - generation_start) * 1000
        
        total_time_ms = retrieval_time_ms + generation_time_ms
        
        # Create query record
        query_id = str(uuid.uuid4())
        with db_manager.get_session() as session:
            query_record = db_manager.create_query(
                session,
                query_id=query_id,
                doc_id=doc_id,
                query_text=query_text,
                answer_text=answer,
                retrieval_time_ms=round(retrieval_time_ms, 2),
                generation_time_ms=round(generation_time_ms, 2),
                total_time_ms=round(total_time_ms, 2),
                top_k=top_k,
                chunks_retrieved=len(retrieved_chunks),
                status="success"
            )
            
            # Update last accessed
            db_manager.update_last_accessed(session, doc_id)
        
        response_data = {
            'query_id': query_id,
            'answer': answer,
            'retrieved_chunks': retrieved_chunks,
            'doc_id': doc_id,
            'filename': document.original_filename,
            'query': query_text,
            'retrieval_time_ms': round(retrieval_time_ms, 2),
            'generation_time_ms': round(generation_time_ms, 2),
            'total_time_ms': round(total_time_ms, 2)
        }
        
        logger.info(f"Query executed successfully - ID: {query_id}, Time: {total_time_ms:.2f}ms")
        return query_record, response_data


# Global service instances
document_service = DocumentService()
query_service = QueryService()
