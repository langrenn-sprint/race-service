"""Integration test cases for authentication and authorization."""

import os
import uuid
from http import HTTPStatus

import jwt
import pytest
from fastapi.testclient import TestClient

# Any endpoint protected by RoleChecker will do:
PROTECTED_URL = f"/races/{uuid.uuid4()}"


def _token(secret: str, exp: int, role: str = "admin") -> str:
    """Create a token with the given secret, expiry and role."""
    payload = {"username": os.getenv("ADMIN_USERNAME"), "exp": exp, "role": role}
    return jwt.encode(payload, secret, "HS256")


@pytest.mark.integration
async def test_no_token(client: TestClient) -> None:
    """Should return 401 Unauthorized."""
    resp = client.delete(PROTECTED_URL)
    assert resp.status_code == HTTPStatus.UNAUTHORIZED


@pytest.mark.integration
async def test_expired_token(client: TestClient) -> None:
    """Should return 401 Unauthorized."""
    token = _token(os.environ["JWT_SECRET"], exp=1)
    resp = client.delete(PROTECTED_URL, headers={"Authorization": f"Bearer {token}"})
    assert resp.status_code == HTTPStatus.UNAUTHORIZED


@pytest.mark.integration
async def test_token_with_invalid_signature(client: TestClient) -> None:
    """Should return 401 Unauthorized."""
    token = _token(
        "not_the_right_secret_for_signing_tokens_in_this_test", exp=9999999999
    )
    resp = client.delete(PROTECTED_URL, headers={"Authorization": f"Bearer {token}"})
    assert resp.status_code == HTTPStatus.UNAUTHORIZED


@pytest.mark.integration
async def test_undecodable_token(client: TestClient) -> None:
    """Should return 401 Unauthorized."""
    resp = client.delete(PROTECTED_URL, headers={"Authorization": "Bearer not-a-jwt"})
    assert resp.status_code == HTTPStatus.UNAUTHORIZED


@pytest.mark.integration
async def test_valid_token_with_insufficient_role(client: TestClient) -> None:
    """Should return 403 Forbidden."""
    token = _token(os.environ["JWT_SECRET"], exp=9999999999, role="user")
    resp = client.delete(PROTECTED_URL, headers={"Authorization": f"Bearer {token}"})
    assert resp.status_code == HTTPStatus.FORBIDDEN
