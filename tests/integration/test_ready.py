"""Integration test cases for the ready route."""

from http import HTTPStatus

import pytest
from fastapi.testclient import TestClient


@pytest.mark.integration
@pytest.mark.asyncio
async def test_ready(client: TestClient) -> None:
    """Should return OK."""
    resp = client.get("/ready")
    assert resp.status_code == HTTPStatus.OK
    text = resp.text
    assert "OK" in text
