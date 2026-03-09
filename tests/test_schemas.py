"""
Tests for Pydantic schemas.
"""
import pytest
from pydantic import ValidationError
from schemas import QueryRequest, DocumentInfo, ErrorResponse


def test_query_request_valid():
    """Test valid QueryRequest."""
    data = {
        'query': 'What is this about?',
        'doc_id': '12345678-1234-1234-1234-123456789012'
    }
    request = QueryRequest(**data)
    assert request.query == 'What is this about?'
    assert request.top_k == 4  # default value


def test_query_request_empty_query():
    """Test QueryRequest with empty query."""
    data = {
        'query': '',
        'doc_id': '12345678-1234-1234-1234-123456789012'
    }
    with pytest.raises(ValidationError):
        QueryRequest(**data)


def test_query_request_whitespace_query():
    """Test QueryRequest with whitespace-only query."""
    data = {
        'query': '   ',
        'doc_id': '12345678-1234-1234-1234-123456789012'
    }
    with pytest.raises(ValidationError):
        QueryRequest(**data)


def test_query_request_custom_params():
    """Test QueryRequest with custom parameters."""
    data = {
        'query': 'Test question',
        'doc_id': '12345678-1234-1234-1234-123456789012',
        'top_k': 8,
        'temperature': 0.5,
        'max_tokens': 1024
    }
    request = QueryRequest(**data)
    assert request.top_k == 8
    assert request.temperature == 0.5
    assert request.max_tokens == 1024


def test_error_response():
    """Test ErrorResponse schema."""
    error = ErrorResponse(
        error='Something went wrong',
        error_type='test_error',
        details={'key': 'value'}
    )
    assert error.error == 'Something went wrong'
    assert error.error_type == 'test_error'
    assert error.details == {'key': 'value'}
