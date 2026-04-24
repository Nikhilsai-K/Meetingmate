# Terraform

Infrastructure-as-code definitions for MeetingMate production.

Modules (to be fleshed out when we move off Fly's managed Postgres):

- `modules/postgres/` — RDS Aurora Serverless v2 with TDE + automated backups.
- `modules/s3/` — transcripts bucket with SSE-KMS, versioning, lifecycle policy (90-day Glacier for Pro users, hard delete on user-delete).
- `modules/cloudflare/` — WAF rules (OWASP core), rate limiting per /32, bot mitigation.
- `modules/qdrant/` — Qdrant Cloud cluster peered to the Fly private network.

`environments/production/` references the modules and is applied via `terraform apply` from the `deploy-infra` workflow (not included in this commit — requires an AWS account ID).

The local dev stack uses `docker-compose.dev.yml` only; Terraform is not required for development.
