# Deployment playbook

This guide describes how to run the privacy proxy in cloud or on-prem environments while satisfying
privacy controls.

## 1. Build and publish the container image

```bash
make docker-build
# optionally push to your registry
docker tag fhir-privacy-proxy registry.example.com/fhir-privacy-proxy:latest
docker push registry.example.com/fhir-privacy-proxy:latest
```

## 2. Configure runtime secrets

- `AI_AUTH_HEADER` should be supplied via a secrets manager or injected as a Kubernetes secret.
- `PII_RULE_PATH` can point to a ConfigMap volume. Reload the process after updating the rule file.
- Store audit logs on encrypted disks or forward them to your SIEM.

## 3. Recommended infrastructure patterns

| Environment | Notes |
| --- | --- |
| **Docker Compose** | Use the bundled `docker-compose.yml` for local or demo setups. |
| **Kubernetes** | Deploy as a Deployment + Service with a HorizontalPodAutoscaler watching CPU. Mount `pii_rules.json` via ConfigMap. |
| **API Gateway** | Terminate TLS and enforce client auth at the gateway. Forward the `X-Request-ID` header to the proxy. |

## 4. Health probes and monitoring

- `GET /health` responds with `{ "status": "ok" }` for readiness checks.
- Scrape container logs for `privacy_proxy.audit` entries to satisfy compliance reporting.
- Use the `modified_fields` array to detect suspicious spikes in redactions.

## 5. Disaster recovery

- Keep backups of rule files and audit logs for at least 7 years per Australian Digital Health guidance.
- Run the proxy in at least two availability zones and front it with a load balancer.
- Test failover quarterly by simulating an AI endpoint outage (expect 504 responses and `timeout` audit entries).
