"""Conftest module for integration tests."""

import pytest
from fastapi.testclient import TestClient

from app import api


@pytest.fixture
def client() -> TestClient:
    """Fixture to create a test client for the FastAPI application."""
    return TestClient(api)
