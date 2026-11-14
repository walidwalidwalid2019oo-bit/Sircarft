# Sircarft server control API foundation

This is a small FastAPI service that validates a server request and persists it as a server record plus a provisioning-queue job. It is a real API and database foundation, **not a Minecraft host or runtime provisioner**.

## Security boundary

- All /v1 routes require a bearer token configured only on the API host as SIRCARFT_API_TOKEN.
- Tokens are compared with a constant-time comparison and are never returned by an endpoint.
- The current foundation is single-tenant (single-tenant owner scope). It is not suitable for public multi-user hosting until a verified account identity provider replaces this token model.
- Request fields are allow-listed. The browser cannot choose a Docker image, shell command, filesystem path, CPU, memory, environment variable, or owner ID.
- Server-slot limits are read and enforced by the backend.
- Creation requires an Idempotency-Key; replays return the original record, while reusing a key for different content is rejected.
- The API has no CORS allow-list, browser token flow, Docker socket access, or host-control endpoint. Do not put the bearer token in frontend code.

## Local setup

~~~bash
pip install -r requirements.txt
cp .env.example .env
python -c "import secrets; print(secrets.token_urlsafe(32))"
~~~

Put the generated value in SIRCARFT_API_TOKEN in the private .env file. SIRCARFT_DB_PATH defaults to server-api/data/sircarft.sqlite3 when run from this directory. SIRCARFT_MAX_SERVERS defaults to 2 and is clamped to a safe configuration range.

Start from this directory:

~~~bash
uvicorn app:app --host 127.0.0.1 --port 8000
~~~

## Endpoints

- GET /health — setup state and honest queue_only provisioning status.
- GET /v1/servers — list records in the configured owner scope.
- POST /v1/servers — validate and persist a queued request; returns HTTP 202.
- GET /v1/servers/{id} — read a server record in the owner scope.
- GET /v1/jobs/{id} — read a provisioning job in the owner scope.

Creation example:

~~~bash
curl -X POST http://127.0.0.1:8000/v1/servers \
  -H "Authorization: Bearer $SIRCARFT_API_TOKEN" \
  -H "Idempotency-Key: create-world-00000001" \
  -H "Content-Type: application/json" \
  -d '{"name":"Oakheart","edition":"Bedrock","mode":"Survival"}'
~~~

The returned server and job remain queued. There is no worker to consume the queue and no Minecraft process, address, or online state. The browser dashboard is not connected to this API yet.

## Required before public hosting

1. Replace the single operator token with verified per-user authentication and authorization.
2. Add rate limits, CSRF/session strategy for browser access, TLS, audit events and abuse reporting.
3. Implement a separate worker with fixed, reviewed runtime images and allow-listed launch settings.
4. Run each server as a non-root isolated workload with restricted network egress and hard resource quotas.
5. Add lifecycle transitions, backups, monitoring, safe deletion and recovery tests.
6. Add deployment secrets management and operational alerting.

Never expose Docker or host-control credentials to the browser or accept arbitrary commands from requests.
