# Contributing Guide

Thank you for helping harden the Healthcare (FHIR) Privacy Proxy. To keep the codebase healthy and
compliant, follow these guidelines before opening a pull request.

## Development workflow

1. **Set up tooling**
   ```bash
   make dev-install
   ```
2. **Create a feature branch** using descriptive names such as `feature/add-observation-validator`.
3. **Add or update tests** alongside code changes.
4. **Run quality gates** locally before submitting:
   ```bash
   make lint
   make format
   make test
   ```
5. **Open a pull request** with a clear summary of the intent and any regulatory implications.

## Coding standards

- Prefer type hints everywhere.
- Keep functions small and focused; favour pure helpers for PII logic.
- Avoid storing PII in logs or fixtures.
- Add docstrings for public interfaces and ensure README/Docs stay accurate.

## Documentation expectations

Every change that alters user-facing behaviour must update `README.md` and any relevant files in
`docs/`. Architectural changes should extend `docs/DEPLOYMENT.md` or a new document describing the
impact on security posture.

## Reporting vulnerabilities

Security issues should **not** be filed as public GitHub issues. Follow the guidance in
[`SECURITY.md`](SECURITY.md) to reach the maintainers privately.
