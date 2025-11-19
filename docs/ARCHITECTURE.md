# Architecture & Components

This document captures how the privacy proxy is structured and how the pieces interact at runtime.

## Component map

| Component | Description |
| --- | --- |
| FastAPI app (`main.py`) | Hosts `/proxy/analyse` and `/health`, wires dependencies, and enforces error handling semantics. |
| PII Engine (`pii_engine.py`) | Recursively traverses FHIR payloads, applying redact/hash/mask rules and regex detection. |
| Config loader (`config.py`) | Resolves environment variables, reads `pii_rules.json`, and exposes hot-reload helpers for tests and tooling. |
| Audit logger (`audit_logger.py`) | Emits structured JSON audit events to stdout and optional file sinks. |
| FHIR utilities (`fhir_utils.py`) | Performs lightweight schema validation and resource-type extraction. |
| Deployment assets | `Dockerfile`, `docker-compose.yml`, `.env.example`, and `docs/DEPLOYMENT.md` describe the packaging and runtime expectations. |

## Data flow

1. A client submits an HL7 FHIR JSON payload to `POST /proxy/analyse`.
2. `main.py` validates the payload shape via `fhir_utils.validate_resource`.
3. The `PIIEngine` walks the document, replacing PII fields with redacted/masked content and collecting the modified field list.
4. The proxy forwards the sanitised payload to `AI_ENDPOINT_URL` using `httpx.AsyncClient` and streams the response back to the client.
5. `audit_logger.emit_audit_event` records the request metadata, modified fields, and result outcome without storing raw PII.

```
Client --> FastAPI Router --> FHIR Validation --> PII Engine --> AI Endpoint
                                  |                               |
                                  +--------- Audit Log -----------+
```

## Non-functional requirements

- **Security** – No raw identifiers are written to disk; audit events are structured JSON for SIEM ingestion. TLS termination should occur at the load balancer or API gateway tier.
- **Observability** – Audit events include timestamps, IPs, request IDs, and modification metadata. Additional metrics can be scraped via FastAPI middleware or ASGI instrumenters.
- **Configurability** – Rules are hot-reloadable via `config.reload_rules()` and reusable across deployments with `.env` overrides.
- **Resilience** – The proxy differentiates between upstream failures (HTTP 5xx), reachability issues (502), and timeouts (504) so that clients can react appropriately.

## Extensibility checklist

- Add new FHIR resource validators in `fhir_utils.REQUIRED_FIELDS`.
- Extend `pii_rules.json` with wildcard selectors or mask configs for additional resources.
- Plug in tracing/metrics via FastAPI middleware or ASGI lifespan hooks.
- Use the provided Docker and Makefile targets to build reproducible artefacts for CI/CD systems.
