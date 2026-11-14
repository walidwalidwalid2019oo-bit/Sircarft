# Sircarft

A mobile-first Minecraft server-hosting dashboard concept with a dark forest, stone and warm-gold visual identity.

## Current prototype

- Responsive dashboard with mobile navigation
- Overview, server list, world library, plan preview and settings screens
- Java / Bedrock selection and Survival / Creative / Adventure presets
- Local preview records saved in the browser with localStorage
- World detail modal that clearly shows preview status and no assigned IP
- Safe text rendering for user-entered world names
- Keyboard-friendly modal dismissal (Escape)
- No external libraries required by the dashboard at runtime (Google Fonts are optional)

## Important status

The browser dashboard is still a **local preview**. Creating a world stores a demo record in that browser; it does not contact the API and does not start a Minecraft server.

A separate Python API foundation now validates server requests, authenticates a single configured operator token, stores server records in SQLite, and writes idempotent provisioning jobs to a durable database queue. It intentionally has **no Minecraft runtime worker** yet. A queued record is not an online server.

Not implemented: multi-user accounts, browser-to-API session integration, payment processing, a provisioning worker, Minecraft runtime images, host infrastructure, console access, backups, monitoring or Java/Bedrock networking.

## Run the dashboard

Open index.html in a browser, or publish the repository with GitHub Pages.

## Run the API foundation locally

Use Python 3.10+:

~~~bash
cd server-api
pip install -r requirements.txt
cp .env.example .env
python -c "import secrets; print(secrets.token_urlsafe(32))"
~~~

Put the generated value in SIRCARFT_API_TOKEN inside the private .env file. Never paste that token into app.js, HTML, or any browser-visible setting. Then start the API:

~~~bash
uvicorn app:app --host 127.0.0.1 --port 8000
~~~

GET /health reports degraded while the service is queue-only. Authenticated API routes use a bearer token and support listing server records, creating an idempotent queued request, and reading server/job status. SIRCARFT_MAX_SERVERS is enforced by the backend, not trusted from the browser.

The first API foundation is deliberately single-tenant. Do not expose it publicly as-is; replace the operator token with verified per-user authentication and add rate limits, TLS, monitoring and an isolated worker before public hosting.

## Planned hosting architecture

1. Verified account identity and per-resource ownership checks.
2. Server-side quotas and validated, idempotent provisioning requests.
3. Durable queue and separate worker with reviewed, allow-listed runtime configurations.
4. Isolated non-root server processes; never expose Docker or host control APIs to the browser.
5. Restricted network egress, patched runtimes, backups, abuse reporting and monitoring.
6. Java and Bedrock support. Cross-play may later use a carefully configured Geyser-compatible bridge.

Free hosting must have explicit CPU, memory, storage, bandwidth and uptime limits. No unlimited or always-on hosting is promised.

## Design direction

Sircarft has its own identity: charcoal, forest green, moss, stone and warm gold; pixel-fantasy landscape details; calm, polished cards and mobile-first navigation. It is inspired by the atmosphere of a block-building world, not copied from NEXUS.
