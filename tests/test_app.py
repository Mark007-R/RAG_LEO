"""
Unit tests for RAG_LEO application.
Tests core functionality including document upload, query, and deletion.
"""
import pytest
import tempfile
import os
from pathlib import Path
from io import BytesIO

from app import create_app
from database import db_manager
from models import Document, Query
from config import TestingSettings


@pytest.fixture
def app():
    """Create test application instance."""
    test_config = {
        'TESTING': True,
        'DATABASE_URL': 'sqlite:///:memory:',
        'API_KEY_ENABLED': False,
        'RATE_LIMIT_ENABLED': False,
    }
    
    app = create_app(config_override=test_config)
    
    with app.app_context():
        db_manager.create_tables()
        yield app
        db_manager.drop_tables()


@pytest.fixture
def client(app):
    """Create test client."""
    return app.test_client()


@pytest.fixture
def sample_pdf():
    """Create a simple test PDF file."""
    pdf_content = b"""%PDF-1.4
1 0 obj
<<
/Type /Catalog
/Pages 2 0 R
>>
endobj
2 0 obj
<<
/Type /Pages
/Kids [3 0 R]
/Count 1
>>
endobj
3 0 obj
<<
/Type /Page
/Parent 2 0 R
/Resources <<
/Font <<
/F1 <<
/Type /Font
/Subtype /Type1
/BaseFont /Helvetica
>>
>>
>>
/Contents 4 0 R
>>
endobj
4 0 obj
<<
/Length 44
>>
stream
BT
/F1 12 Tf
100 700 Td
(Test PDF) Tj
ET
endstream
endobj
xref
0 5
trailer
<<
/Size 5
/Root 1 0 R
>>
startxref
%%EOF
"""
    return BytesIO(pdf_content)


class TestHealthEndpoint:
    """Tests for health check endpoint."""
    
    def test_health_check(self, client):
        """Test health check returns 200."""
        response = client.get('/api/v1/health')
        assert response.status_code == 200
        
        data = response.get_json()
        assert data['status'] == 'healthy'
        assert 'app_name' in data
        assert 'version' in data


class TestDocumentEndpoints:
    """Tests for document management endpoints."""
    
    def test_list_documents_empty(self, client):
        """Test listing documents when none exist."""
        response = client.get('/api/v1/documents')
        assert response.status_code == 200
        
        data = response.get_json()
        assert data['count'] == 0
        assert data['documents'] == []
    
    def test_upload_no_file(self, client):
        """Test upload without file."""
        response = client.post('/api/v1/upload')
        assert response.status_code == 400
    
    def test_upload_empty_filename(self, client):
        """Test upload with empty filename."""
        data = {'file': (BytesIO(b''), '')}
        response = client.post('/api/v1/upload', data=data)
        assert response.status_code == 400


class TestQueryEndpoints:
    """Tests for query endpoints."""
    
    def test_query_invalid_data(self, client):
        """Test query with invalid data."""
        response = client.post('/api/v1/ask', json={})
        assert response.status_code == 400
    
    def test_query_missing_doc_id(self, client):
        """Test query without doc_id."""
        data = {'query': 'Test question'}
        response = client.post('/api/v1/ask', json=data)
        assert response.status_code == 400
    
    def test_query_missing_query(self, client):
        """Test query without query text."""
        data = {'doc_id': '12345678-1234-1234-1234-123456789012'}
        response = client.post('/api/v1/ask', json=data)
        assert response.status_code == 400
    
    def test_query_nonexistent_document(self, client):
        """Test query on non-existent document."""
        data = {
            'query': 'Test question',
            'doc_id': '12345678-1234-1234-1234-123456789012'
        }
        response = client.post('/api/v1/ask', json=data)
        assert response.status_code == 404


class TestStatsEndpoint:
    """Tests for statistics endpoint."""
    
    def test_stats(self, client):
        """Test stats endpoint."""
        response = client.get('/api/v1/stats')
        assert response.status_code == 200
        
        data = response.get_json()
        assert 'total_documents' in data
        assert 'total_queries' in data
        assert 'uptime_seconds' in data


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
