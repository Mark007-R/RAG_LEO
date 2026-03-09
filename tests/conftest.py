"""
Test configuration.
"""
import pytest


@pytest.fixture(scope='session', autouse=True)
def setup_test_environment():
    """Setup test environment."""
    import os
    os.environ['APP_ENV'] = 'testing'
    os.environ['DATABASE_URL'] = 'sqlite:///:memory:'
    os.environ['GROQ_API_KEY'] = 'test-key'
    os.environ['SECRET_KEY'] = 'test-secret-key'
