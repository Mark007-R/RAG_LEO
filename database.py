"""
Database management utilities.
Handles database initialization, sessions, and operations.
"""
import logging
from typing import List, Optional
from datetime import datetime
from sqlalchemy import create_engine, select, func
from sqlalchemy.orm import Session, sessionmaker
from contextlib import contextmanager

from config import settings
from models import Base, Document, Query, APIKey
from exceptions import DatabaseError, DocumentNotFoundError

logger = logging.getLogger(__name__)


class DatabaseManager:
    """Centralized database management."""
    
    def __init__(self):
        """Initialize database engine and session factory."""
        self.engine = create_engine(
            settings.DATABASE_URL,
            echo=settings.DATABASE_ECHO,
            pool_pre_ping=True,
            pool_recycle=3600
        )
        self.SessionLocal = sessionmaker(
            autocommit=False,
            autoflush=False,
            bind=self.engine
        )
    
    def create_tables(self):
        """Create all database tables."""
        try:
            Base.metadata.create_all(bind=self.engine)
            logger.info("Database tables created successfully")
        except Exception as e:
            logger.error(f"Failed to create database tables: {e}")
            raise DatabaseError(f"Database initialization failed: {str(e)}")
    
    def drop_tables(self):
        """Drop all database tables (use with caution!)."""
        try:
            Base.metadata.drop_all(bind=self.engine)
            logger.warning("All database tables dropped")
        except Exception as e:
            logger.error(f"Failed to drop database tables: {e}")
            raise DatabaseError(f"Database cleanup failed: {str(e)}")
    
    @contextmanager
    def get_session(self):
        """Get database session with automatic cleanup."""
        session = self.SessionLocal()
        try:
            yield session
            session.commit()
        except Exception as e:
            session.rollback()
            logger.error(f"Database session error: {e}")
            raise
        finally:
            session.close()
    
    # Document operations
    def create_document(self, session: Session, **kwargs) -> Document:
        """Create new document record."""
        try:
            document = Document(**kwargs)
            session.add(document)
            session.commit()
            session.refresh(document)
            logger.info(f"Created document: {document.doc_id}")
            return document
        except Exception as e:
            session.rollback()
            logger.error(f"Failed to create document: {e}")
            raise DatabaseError(f"Document creation failed: {str(e)}")
    
    def get_document_by_id(self, session: Session, doc_id: str) -> Optional[Document]:
        """Get document by doc_id."""
        try:
            stmt = select(Document).where(
                Document.doc_id == doc_id,
                Document.is_deleted == False
            )
            result = session.execute(stmt)
            return result.scalar_one_or_none()
        except Exception as e:
            logger.error(f"Failed to get document {doc_id}: {e}")
            raise DatabaseError(f"Document retrieval failed: {str(e)}")
    
    def get_all_documents(self, session: Session, include_deleted: bool = False) -> List[Document]:
        """Get all documents."""
        try:
            stmt = select(Document)
            if not include_deleted:
                stmt = stmt.where(Document.is_deleted == False)
            stmt = stmt.order_by(Document.created_at.desc())
            result = session.execute(stmt)
            return list(result.scalars().all())
        except Exception as e:
            logger.error(f"Failed to get documents: {e}")
            raise DatabaseError(f"Document listing failed: {str(e)}")
    
    def update_document(self, session: Session, doc_id: str, **kwargs) -> Document:
        """Update document fields."""
        try:
            document = self.get_document_by_id(session, doc_id)
            if not document:
                raise DocumentNotFoundError(f"Document not found: {doc_id}")
            
            for key, value in kwargs.items():
                if hasattr(document, key):
                    setattr(document, key, value)
            
            document.updated_at = datetime.utcnow()
            session.commit()
            session.refresh(document)
            logger.info(f"Updated document: {doc_id}")
            return document
        except DocumentNotFoundError:
            raise
        except Exception as e:
            session.rollback()
            logger.error(f"Failed to update document {doc_id}: {e}")
            raise DatabaseError(f"Document update failed: {str(e)}")
    
    def delete_document(self, session: Session, doc_id: str, soft_delete: bool = True) -> Document:
        """Delete document (soft or hard delete)."""
        try:
            document = self.get_document_by_id(session, doc_id)
            if not document:
                raise DocumentNotFoundError(f"Document not found: {doc_id}")
            
            if soft_delete:
                document.is_deleted = True
                document.deleted_at = datetime.utcnow()
                session.commit()
                session.refresh(document)
                logger.info(f"Soft deleted document: {doc_id}")
            else:
                session.delete(document)
                session.commit()
                logger.info(f"Hard deleted document: {doc_id}")
            
            return document
        except DocumentNotFoundError:
            raise
        except Exception as e:
            session.rollback()
            logger.error(f"Failed to delete document {doc_id}: {e}")
            raise DatabaseError(f"Document deletion failed: {str(e)}")
    
    def update_last_accessed(self, session: Session, doc_id: str):
        """Update document last accessed timestamp."""
        try:
            document = self.get_document_by_id(session, doc_id)
            if document:
                document.last_accessed_at = datetime.utcnow()
                session.commit()
        except Exception as e:
            logger.warning(f"Failed to update last accessed for {doc_id}: {e}")
    
    # Query operations
    def create_query(self, session: Session, **kwargs) -> Query:
        """Create query record."""
        try:
            query = Query(**kwargs)
            session.add(query)
            session.commit()
            session.refresh(query)
            return query
        except Exception as e:
            session.rollback()
            logger.error(f"Failed to create query: {e}")
            raise DatabaseError(f"Query creation failed: {str(e)}")
    
    def get_query_count(self, session: Session) -> int:
        """Get total query count."""
        try:
            stmt = select(func.count(Query.id))
            result = session.execute(stmt)
            return result.scalar() or 0
        except Exception as e:
            logger.error(f"Failed to get query count: {e}")
            return 0
    
    def get_document_count(self, session: Session, include_deleted: bool = False) -> int:
        """Get total document count."""
        try:
            stmt = select(func.count(Document.id))
            if not include_deleted:
                stmt = stmt.where(Document.is_deleted == False)
            result = session.execute(stmt)
            return result.scalar() or 0
        except Exception as e:
            logger.error(f"Failed to get document count: {e}")
            return 0


# Global database manager instance
db_manager = DatabaseManager()
