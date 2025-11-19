"""FastAPI application implementing the privacy proxy."""
from __future__ import annotations

import uuid

import httpx
from fastapi import Depends, FastAPI, Header, HTTPException, Request
from fastapi.responses import JSONResponse

from audit_logger import emit_audit_event
from config import Settings, load_settings
from fhir_utils import FHIRValidationError, extract_resource_type, validate_resource
from pii_engine import PIIEngine

app = FastAPI(title="FHIR Privacy Proxy", version="1.0.0")


async def get_http_client() -> httpx.AsyncClient:
    return app.state.http_client


def get_settings() -> Settings:
    return load_settings()


def get_pii_engine() -> PIIEngine:
    if not hasattr(app.state, "pii_engine"):
        app.state.pii_engine = PIIEngine()
    return app.state.pii_engine


@app.on_event("startup")
async def startup_event() -> None:
    settings = load_settings()
    app.state.http_client = httpx.AsyncClient(timeout=settings.ai_endpoint_timeout)
    app.state.pii_engine = PIIEngine(settings.rule_config)


@app.on_event("shutdown")
async def shutdown_event() -> None:
    client: httpx.AsyncClient = app.state.http_client
    await client.aclose()


@app.post("/proxy/analyse")
async def proxy_analyse(
    request: Request,
    http_client: httpx.AsyncClient = Depends(get_http_client),
    settings: Settings = Depends(get_settings),
    engine: PIIEngine = Depends(get_pii_engine),
    x_request_id: str | None = Header(default=None),
):
    request_id = x_request_id or str(uuid.uuid4())
    client_host = request.client.host if request.client else "unknown"
    try:
        payload = await request.json()
    except Exception as exc:  # pragma: no cover - FastAPI handles body parsing
        raise HTTPException(status_code=400, detail="Invalid JSON payload") from exc

    try:
        validate_resource(payload)
    except FHIRValidationError as exc:
        emit_audit_event(request_id, "Unknown", client_host, [], "validation_failed")
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    resource_type = extract_resource_type(payload)
    sanitized, modifications = engine.sanitize(payload)

    forward_headers = {"X-Request-ID": request_id}
    if settings.ai_auth_header:
        forward_headers["Authorization"] = settings.ai_auth_header

    try:
        response = await http_client.post(
            settings.ai_endpoint_url,
            json=sanitized,
            headers=forward_headers,
        )
        response.raise_for_status()
    except httpx.TimeoutException as exc:
        emit_audit_event(request_id, resource_type, client_host, modifications, "timeout")
        raise HTTPException(status_code=504, detail="AI endpoint timeout") from exc
    except httpx.HTTPStatusError as exc:
        emit_audit_event(
            request_id, resource_type, client_host, modifications, "ai_error"
        )
        raise HTTPException(
            status_code=exc.response.status_code,
            detail=f"AI endpoint error: {exc.response.text}",
        ) from exc
    except httpx.RequestError as exc:
        emit_audit_event(
            request_id,
            resource_type,
            client_host,
            modifications,
            "ai_unreachable",
        )
        raise HTTPException(status_code=502, detail="AI endpoint unreachable") from exc

    emit_audit_event(request_id, resource_type, client_host, modifications, "success")

    if "application/json" in response.headers.get("content-type", ""):
        try:
            return JSONResponse(status_code=response.status_code, content=response.json())
        except ValueError:
            # Upstream lied about returning JSON; fall through to opaque body
            pass
    return JSONResponse(
        status_code=response.status_code,
        content={"message": "AI endpoint response forwarded", "proxy_request_id": request_id},
    )


@app.get("/health")
async def health_check():
    return {"status": "ok"}
