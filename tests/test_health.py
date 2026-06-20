"""
Jarvis V1 - Tests: Health Endpoint.

Verifica que el endpoint /health funciona correctamente.
"""

import pytest
from httpx import AsyncClient, ASGITransport

from app.main import app


@pytest.mark.asyncio
async def test_health_returns_ok():
    """GET /health debe retornar status ok."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.get("/health")

    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ok"
    assert data["version"] == "1.0.0"
    assert data["service"] == "Jarvis V1"
    assert "components" in data


@pytest.mark.asyncio
async def test_health_has_components():
    """GET /health debe incluir info de componentes."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.get("/health")

    data = response.json()
    components = data["components"]
    assert "uptime_seconds" in components
    assert "sqlite" in components
