# Sircarft server control API — proposed contract

This document defines a safe boundary for a future backend. It is architecture documentation, **not a running API or provisioner**.

## Non-negotiable boundary

The browser must never receive Docker socket access, host credentials, provider tokens, or direct worker control. The API authenticates a user, checks ownership and quotas, then places a validated job on a private provisioning queue. A separate worker performs allow-listed operations inside isolated server environments.

## Proposed endpoints

- `GET /v1/servers` — list only servers owned by the authenticated user.
- `POST /v1/servers` — request creation with edition, plan, region, and world settings.
- `GET /v1/servers/{id}` — return state and connection details only after ownership checks.
- `POST /v1/servers/{id}/start` and `/stop` — enqueue an idempotent lifecycle request.
- `DELETE /v1/servers/{id}` — request deletion after an explicit confirmation step.
- `GET /v1/servers/{id}/events` — read sanitized lifecycle events; never raw host logs or secrets.

## Creation request (illustrative)

```json
{
  "edition": "bedrock",
  "plan": "free",
  "region": "selected-region",
  "world": {
    "name": "Oakheart",
    "mode": "survival",
    "difficulty": "normal"
  }
}
```

The backend must validate every field against server-side allow-lists. Never trust a client-supplied owner ID, resource limit, image name, command, filesystem path, or environment variable.

## Required controls before public hosting

1. Authentication and per-resource authorization on every request.
2. Per-account and global CPU, memory, disk, bandwidth, and server-count quotas.
3. Fixed, reviewed runtime images and allow-listed launch configuration; no arbitrary shell commands.
4. Isolated workers, restricted network egress, non-root processes, and patched runtimes.
5. Rate limits, idempotency keys, audit events, abuse reporting, and safe deletion.
6. Encrypted backups with retention limits and restore testing.
7. Health checks and monitoring that distinguish queued, starting, online, stopping, and failed states.
8. Published free-tier limits and honest uptime expectations.

## Current implementation status

Only the static dashboard and browser-local demo cards exist today. No endpoint, account system, database, queue, worker, Minecraft process, or hosting infrastructure is implemented by this document.
