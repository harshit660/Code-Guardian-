# Operations runbook

## Normal operation

Start the full stack with `docker compose up --build`. The API health endpoint is `GET /health`; interactive OpenAPI documentation is at `http://localhost:8000/docs`. A successful queued analysis should transition `QUEUED → RUNNING → COMPLETED` as the worker receives it.

## Failed analysis

1. Locate the analysis id in API logs (all entries are JSON and contain `request_id` where applicable).
2. Inspect the analysis record's `error` field using `GET /api/v1/analyses/{analysis_id}`.
3. Check worker logs for GitHub API errors or queue connectivity.
4. Verify `GITHUB_TOKEN` has repository-content read access and pull-request write access before publishing reviews.
5. Re-trigger the analysis once the external condition is fixed. Queued jobs are idempotent at the report level only when the retry uses a fresh analysis id.

## Rollback

Deploy the previously tagged API and web images together. Database changes should always be forward-compatible. Before adding a destructive migration, take a PostgreSQL backup and document the down migration in the release PR.

## Production checklist

- Replace development `SECRET_KEY` with a secret-manager value.
- Use a GitHub App installation token service rather than a shared personal token.
- Run Alembic migrations separately from app startup.
- Put Redis and PostgreSQL on managed, encrypted services with backups.
- Configure log retention, worker failure alerts, and GitHub API quota alerts.
- Run a Redis-backed distributed rate limiter at the API edge.

