# API Reference

This document describes the externally supported FastAPI endpoints that make up the healthcare privacy proxy.

## `POST /proxy/analyse`

Accepts a JSON FHIR resource and returns the response from the configured AI backend. All requests require a body with `resourceType` and the fields defined by the relevant profile.

### Request headers

| Header | Description |
| --- | --- |
| `Content-Type` | `application/json` or `application/fhir+json` |
| `X-Request-ID` | Optional correlation ID propagated to the AI backend and audit log. |
| `Authorization` | Only required if your deployment enforces inbound auth. |

### Response codes

| Status | Meaning |
| --- | --- |
| `200` | Proxy successfully sanitised the payload and received a success response from the AI endpoint. |
| `400` | Invalid JSON or FHIR resource. Details are returned in the response body. |
| `500` | Upstream AI endpoint responded with an error body; the proxy surfaces the status code and short detail string. |
| `502` | The AI endpoint could not be reached (DNS failure, refused connection). |
| `504` | The AI endpoint timed out before responding. |

### Example request

```bash
curl -X POST http://localhost:8000/proxy/analyse \
  -H 'Content-Type: application/fhir+json' \
  -H 'X-Request-ID: example-1' \
  -d @examples/patient_before.json
```

### Example success response

```json
{
  "status": "accepted",
  "analysis_id": "mock-123"
}
```

### Example error response (invalid FHIR)

```json
{
  "detail": "Resource Patient missing required fields: name"
}
```

## `GET /health`

Returns a static body `{ "status": "ok" }` and HTTP 200. This endpoint is safe for Kubernetes, ECS, or API Gateway health checks.

## Upstream contract

The proxy forwards the sanitised JSON body to `AI_ENDPOINT_URL` via HTTP POST with:

- A JSON payload that mirrors the inbound FHIR resource (minus PII fields)
- Headers: `Content-Type: application/json` and the optional `X-Request-ID`
- Optional `Authorization` header defined by `AI_AUTH_HEADER`

Any response body returned by the upstream service is forwarded as JSON when the `Content-Type` indicates JSON. Otherwise the proxy replies with a generic acknowledgement to avoid leaking unexpected content types to clients.
