import json

import pytest

httpx = pytest.importorskip("httpx")
pytest.importorskip("fastapi")

from main import app, get_http_client


def load_payload():
    with open("examples/patient_before.json", "r", encoding="utf-8") as handle:
        return json.load(handle)


@pytest.mark.asyncio
async def test_proxy_analyse_sanitises_and_forwards():
    forwarded = {}

    def handler(request: httpx.Request) -> httpx.Response:
        forwarded["json"] = json.loads(request.content.decode())
        forwarded["headers"] = dict(request.headers)
        return httpx.Response(200, json={"status": "accepted"})

    transport = httpx.MockTransport(handler)
    mock_client = httpx.AsyncClient(transport=transport, timeout=5)

    async def override_http_client():
        return mock_client

    app.dependency_overrides[get_http_client] = override_http_client

    try:
        async with httpx.AsyncClient(app=app, base_url="http://testserver") as test_client:
            response = await test_client.post(
                "/proxy/analyse",
                json=load_payload(),
                headers={"X-Request-ID": "demo-test"},
            )
    finally:
        app.dependency_overrides.clear()
        await mock_client.aclose()

    assert response.status_code == 200
    forwarded_payload = forwarded["json"]
    assert forwarded_payload["name"] == []
    assert len(forwarded_payload["identifier"][0]["value"]) == 64
    assert len(forwarded_payload["identifier"][1]["value"]) == 64
    assert forwarded_payload["managingOrganization"]["reference"].startswith("****")
    assert "Sofia" not in json.dumps(forwarded_payload)
    assert forwarded["headers"]["x-request-id"] == "demo-test"


@pytest.mark.asyncio
async def test_proxy_analyse_surfaces_ai_errors():
    def handler(_: httpx.Request) -> httpx.Response:
        return httpx.Response(500, json={"detail": "boom"})

    transport = httpx.MockTransport(handler)
    mock_client = httpx.AsyncClient(transport=transport, timeout=5)

    async def override_http_client():
        return mock_client

    app.dependency_overrides[get_http_client] = override_http_client

    try:
        async with httpx.AsyncClient(app=app, base_url="http://testserver") as test_client:
            response = await test_client.post("/proxy/analyse", json=load_payload())
    finally:
        app.dependency_overrides.clear()
        await mock_client.aclose()

    assert response.status_code == 500
    assert "AI endpoint error" in response.json()["detail"]


@pytest.mark.asyncio
async def test_proxy_handles_ai_unreachable():
    def handler(request: httpx.Request) -> httpx.Response:
        raise httpx.ConnectError("boom", request=request)

    transport = httpx.MockTransport(handler)
    mock_client = httpx.AsyncClient(transport=transport, timeout=5)

    async def override_http_client():
        return mock_client

    app.dependency_overrides[get_http_client] = override_http_client

    try:
        async with httpx.AsyncClient(app=app, base_url="http://testserver") as test_client:
            response = await test_client.post("/proxy/analyse", json=load_payload())
    finally:
        app.dependency_overrides.clear()
        await mock_client.aclose()

    assert response.status_code == 502
    assert response.json()["detail"] == "AI endpoint unreachable"
