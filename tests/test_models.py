"""
Tests for database models and operations.
"""
import pytest
from datetime import datetime
from src.database import db_manager
from src.models import Document, Query


def test_document_model():
    """Test Document model creation."""
    doc = Document(
        doc_id='test-doc-id',
        filename='test.pdf',
        original_filename='test.pdf',
        file_path='/path/to/test.pdf',
        file_size=1024,
        status='pending'
    )
    
    assert doc.doc_id == 'test-doc-id'
    assert doc.status == 'pending'
    assert doc.is_deleted == False


def test_query_model():
    """Test Query model creation."""
    query = Query(
        query_id='test-query-id',
        doc_id='test-doc-id',
        query_text='What is this about?',
        answer_text='This is a test.',
        status='success'
    )
    
    assert query.query_id == 'test-query-id'
    assert query.doc_id == 'test-doc-id'
    assert query.status == 'success'


def test_document_to_dict():
    """Test Document serialization."""
    doc = Document(
        doc_id='test-doc-id',
        filename='test.pdf',
        original_filename='test.pdf',
        file_path='/path/to/test.pdf',
        file_size=1024,
        status='completed',
        chunks_count=10,
        text_length=5000
    )
    
    doc_dict = doc.to_dict()
    assert doc_dict['doc_id'] == 'test-doc-id'
    assert doc_dict['status'] == 'completed'
    assert doc_dict['chunks_count'] == 10
