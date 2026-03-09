import os
import time
import uuid
import logging
from pathlib import Path
from typing import Optional, List, Tuple
from datetime import datetime

from werkzeug.utils import secure_filename
from werkzeug.datastructures import FileStorage

from .config import settings
from .database import db_manager
from .models import Document, Query
from .rag_pipeline import RAGPipeline
from .exceptions import (
    DocumentNotFoundError,
    FileUploadError,
    PDFExtractionError,
    IndexBuildError,
    ValidationError,
)
from .middleware import RequestValidator, sanitize_filename

logger = logging.getLogger(__name__)

class DocumentService:
    
    def __init__(self):
        self.pipeline = RAGPipeline()
        self.upload_folder = settings.get_upload_path()
        self.upload_folder.mkdir(exist_ok=True)
    
    def upload_document(self, file: FileStorage) -> Tuple[Document, dict]:
        start_time = time.time()
        
        if not file or file.filename == '':
            raise FileUploadError("No file provided")
        
        RequestValidator.validate_file_extension(file.filename)
        RequestValidator.validate_file_size(file)
        
        doc_id = str(uuid.uuid4())
        original_filename = secure_filename(file.filename)
        original_filename = sanitize_filename(original_filename)
        save_filename = f"{doc_id}__{original_filename}"
        save_path = self.upload_folder / save_filename
        
        try:
            file.save(str(save_path))
            file_size = save_path.stat().st_size
            logger.info(f"Saved file: {save_filename} ({file_size} bytes)")
            
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
                
                index = self.pipeline.build_faiss_index(doc_id, persist=True)
                
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
                with db_manager.get_session() as session:
                    db_manager.update_document(
                        session,
                        doc_id=doc_id,
                        status="failed",
                        error_message=str(e)
                    )
                raise PDFExtractionError(f"PDF processing failed: {str(e)}")
        
        except Exception as e:
            if save_path.exists():
                save_path.unlink()
            raise
    
    def _cleanup_failed_upload(self, doc_id: str, file_path: Path):
        try:
            if file_path.exists():
                file_path.unlink()
            
            with db_manager.get_session() as session:
                db_manager.delete_document(session, doc_id, soft_delete=False)
        except Exception as e:
            logger.error(f"Cleanup failed for {doc_id}: {e}")
    
    def get_document(self, doc_id: str) -> Document:
        with db_manager.get_session() as session:
            document = db_manager.get_document_by_id(session, doc_id)
            if not document:
                raise DocumentNotFoundError(f"Document not found: {doc_id}")
            return document
    
    def list_documents(self) -> List[Document]:
        with db_manager.get_session() as session:
            return db_manager.get_all_documents(session)
    
    def delete_document(self, doc_id: str) -> Document:
        with db_manager.get_session() as session:
            document = db_manager.get_document_by_id(session, doc_id)
            if not document:
                raise DocumentNotFoundError(f"Document not found: {doc_id}")
            
            try:
                if document.file_path and Path(document.file_path).exists():
                    Path(document.file_path).unlink()
                    logger.info(f"Deleted file: {document.file_path}")
                
                if document.index_path and Path(document.index_path).exists():
                    Path(document.index_path).unlink()
                    logger.info(f"Deleted index: {document.index_path}")
                
                if document.chunks_path and Path(document.chunks_path).exists():
                    Path(document.chunks_path).unlink()
                    logger.info(f"Deleted chunks: {document.chunks_path}")
            
            except Exception as e:
                logger.error(f"Error deleting files for {doc_id}: {e}")
            
            document = db_manager.delete_document(session, doc_id, soft_delete=True)
            return document

class QueryService:
    
    def __init__(self):
        self.pipeline = RAGPipeline()
    
    def execute_query(
        self,
        doc_id: str,
        query_text: str,
        top_k: int = None,
        temperature: float = None,
        max_tokens: int = None
    ) -> Tuple[Query, dict]:
        top_k = top_k or settings.TOP_K_RETRIEVAL
        temperature = temperature if temperature is not None else settings.LLM_TEMPERATURE
        max_tokens = max_tokens or settings.LLM_MAX_TOKENS
        
        with db_manager.get_session() as session:
            document = db_manager.get_document_by_id(session, doc_id)
            if not document:
                raise DocumentNotFoundError(f"Document not found: {doc_id}")
            
            if document.status != "completed":
                raise ValidationError(f"Document is not ready for querying. Status: {document.status}")
        
        if self.pipeline.doc_id != doc_id:
            logger.info(f"Loading index for document {doc_id}")
            try:
                self.pipeline.load_index(doc_id)
            except FileNotFoundError:
                raise DocumentNotFoundError("Document index not found. Please re-upload the document.")
        
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

document_service = DocumentService()
query_service = QueryService()
