"""Integration test cases for the ready route."""

from http import HTTPStatus

import pytest
from aiohttp.test_utils import TestClient as _TestClient


@pytest.mark.integration
@pytest.mark.asyncio
async def test_ready(client: _TestClient) -> None:
    """Should return OK."""
    resp = await client.get("/ready")
    assert resp.status == HTTPStatus.OK
    text = await resp.text()
    assert "OK" in text
