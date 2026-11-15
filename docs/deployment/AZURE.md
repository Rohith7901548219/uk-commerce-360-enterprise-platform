# Azure deployment design — not deployed

| Local component | Azure candidate | Required engineering before public deployment |
|---|---|---|
| API/UI/worker | Container Apps | Entra ID, private ingress, managed identities, TLS |
| PostgreSQL | Azure Database for PostgreSQL Flexible Server | Private endpoint, backups, least privilege |
| Raw files/artifacts | Blob Storage | Retention, lifecycle, encryption, no public access |
| Redpanda | Dedicated supported hosting or Kafka-compatible Event Hubs | Validate Kafka API compatibility and offsets |
| Secrets | Key Vault | Role assignments; remove env-file deployment |
| Telemetry | Monitor / Log Analytics | Redaction, retention, alerts and cost limits |
| Images | Container Registry | Image signing and vulnerability scanning |

`infra/main.bicep` is a limited example for the telemetry workspace, not a complete
deployment template. It has not been applied. **No Azure resources have been created.**
Do not run deployment commands without explicit paid-service approval. Local Compose
is the complete intended runtime. A public deployment additionally needs read access
authentication, distributed rate limits, broker ACL/TLS, disaster recovery exercises,
resource sizing, dependency scanning, load tests and a licence review.

Redpanda is single-broker development configuration here. No enterprise-only features
are required, and no availability claim is made. Review its current licensing before
commercial use. Power BI Desktop assembly and any hosted gateway are separate.
