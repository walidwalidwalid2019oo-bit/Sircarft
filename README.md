# Sircarft

A mobile-first Minecraft server-hosting dashboard concept with a dark forest, stone and warm-gold visual identity.

## Current prototype

- Responsive dashboard with mobile navigation
- Overview, server list, world library, plan preview and settings screens
- Java / Bedrock selection and Survival / Creative / Adventure presets
- Demo server creation with browser-local persistence (localStorage)
- Safe text rendering for user-entered world names
- Keyboard-friendly modal dismissal (Escape)
- No external libraries required at runtime (Google Fonts are optional)

## Important status

This is a **front-end prototype only**. The sample servers and quota are illustrative. Creating a world saves a local demo card in that browser's localStorage, so it remains after refresh on the same browser. It does not provision a Minecraft server.

Not implemented: account registration, authentication, persistent database, payments, real server provisioning, console access, backups, monitoring or Java/Bedrock networking.

## Run

Open `index.html` in a browser, or publish the repository with GitHub Pages.

## Planned architecture

1. Frontend dashboard and responsive UX.
2. Secure account service and database with per-user server ownership.
3. Provisioning service with strict CPU, RAM, storage and runtime limits.
4. Isolated server workers; never expose the Docker or host control API to the browser.
5. Queue, rate limits, abuse reporting, backups and monitoring.
6. Java and Bedrock support. Cross-play may later use a carefully configured Geyser-compatible bridge.

Free hosting must have explicit resource and uptime limits. No unlimited or always-on hosting is promised.

## Design direction

Sircarft has its own identity: charcoal, forest green, moss, stone and warm gold; pixel-fantasy landscape details; calm, polished cards and mobile-first navigation. It is inspired by the atmosphere of a block-building world, not copied from NEXUS.
