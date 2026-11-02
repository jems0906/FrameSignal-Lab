# FrameSignal Lab Railway Deployment Plan

**Status:** Deployed and verified on Railway from commit `6dd03a2` in the user's Pro workspace; its full CI passed. All four services are healthy. MetricSteward is public read-only, with its catalog snapshot seeded and verified.

## Goal and Access Model

Deploy FrameSignal Lab and MetricSteward as a public, read-only educational portfolio demo. Use synthetic data only. Preserve existing scientific results and MetricSteward catalog/review history, but do not accept public review records or evidence imports. Public access is not independent peer review, real-world approval, or production suitability.

Read-only is the first-deployment recommendation because the current app has no user authentication, and Railway service networking does not provide end-user login. A later authenticated deployment requires selecting and implementing an identity provider before enabling writes.

## Proposed Services

Use the existing Dockerfiles as four Railway services built from the repository root, preserving shared package/report build inputs:

| Railway service | Dockerfile | Exposure | Port |
| --- | --- | --- | --- |
| `framesignal-frontend` | `frontend/Dockerfile` | Public generated domain | 80 |
| `framesignal-backend` | `backend/Dockerfile` | Private networking only | 8000 |
| `metricsteward-frontend` | `metricsteward/frontend/Dockerfile` | Public generated domain | 80 |
| `metricsteward-backend` | `metricsteward/backend/Dockerfile` | Private networking only; one replica | 8001 |

Configure the frontend service build context as the repository root and select its Dockerfile path explicitly. Do not set per-service root directories that omit shared package files, reports, or the generated wheel. Do not import `compose.yaml` blindly; Railway documents that not every Compose feature is supported.

Set the runtime nginx variables to Railway private-network addresses:

- `FRAMESIGNAL_API_UPSTREAM=http://framesignal-backend.railway.internal:8000`
- `METRICSTEWARD_API_UPSTREAM=http://metricsteward-backend.railway.internal:8001`

Leave backend services without public domains. Confirm Railway's assigned target ports for public nginx services and ensure the service listens on the configured port.
Set `PORT=8000` on `framesignal-backend`, `PORT=8001` on `metricsteward-backend`, and `PORT=80` on both nginx frontends. Railway uses `PORT` for deployment health checks; each value must match the port the container actually listens on.
Attach one Railway volume to `metricsteward-backend` at `/data`; the existing container path is `/data/catalog.sqlite3`. Keep this service to one replica. Railway volumes do not support replicas and redeploys can cause short downtime, which is acceptable for this read-only portfolio demo.

## Access and Data Safeguards

1. Make MetricSteward read-only in the hosted environment. Disable the evidence-import and review-write endpoints and remove or clearly disable their UI controls. Keep read endpoints and the stateless calculation endpoint available with request-size and rate limits. Preserve local development behavior behind an explicit environment setting.
2. Keep the existing scientific decision and real-world-promotion guards unchanged. Do not create, import, or imply any peer-feedback records beyond the catalog snapshot already present.
3. Keep SQLite for this single-replica read-only demo. Use the workspace catalog at `metricsteward/data/catalog.sqlite3` as the migration source. It currently contains 1 import and 1 review; the separate Compose volume currently contains 1 import and 0 reviews. Create a consistent backup of the workspace catalog, upload that snapshot to the Railway volume mounted at `/data`, and verify it contains 1 import and 1 review before making the frontends public. Keep a separate verified backup for rollback.
4. Redact reviewer identity, notes, and references from public read-only review responses. Block public exports, evidence imports, and review writes. Preserve original records unchanged in the mounted SQLite database. Keep local development behavior writable by default.
5. Add limits for public calculation/simulation requests and monitor Railway CPU, memory, volume usage, egress, and logs to reduce abuse and cost surprises.

## Cost and Plan Fit

The Railway workspace shown during setup is on Pro. Current published Pro pricing is $20/month with $20/month of included resource usage; usage above that is billed separately. CPU, memory, volume storage, and network egress are metered. Actual cost depends on runtime and traffic; review Railway's [current pricing](https://railway.com/pricing) and usage before deploying, and set any available usage alerts/limits.

The single Railway volume is chosen to reuse the current SQLite store and avoid a database rewrite for a low-traffic, read-only demo. Do not scale the MetricSteward backend beyond one replica. If the project later needs writable multi-user access or higher availability, add authentication and move to PostgreSQL first.

## Stages and Gates

1. **Prepare the app.** Runtime-configurable nginx upstreams, an opt-in MetricSteward read-only mode, reviewer-detail redaction, blocked imports/reviews/exports, nginx API rate limits (10 requests/second with a burst of 40 per frontend proxy), and in-image shared-wheel/handoff generation are implemented and tested locally.
2. **Prepare source/builds.** The Railway GitHub App has access to this repository only in addition to the two previously selected repositories; all-repository access remains disabled. Commit `5c0a61d` is pushed and all three CI jobs passed. Railway services build from the repository root with service-specific Dockerfile paths; deployments use commit-pinned images.
3. **Create Railway configuration.** A private `FrameSignal Lab` project exists in the Pro workspace. Four GitHub-backed services are configured with the correct Dockerfile paths, private upstreams, health checks, and explicit `PORT` values; both backends have no public domain, MetricSteward is read-only, one replica is selected, and its volume is mounted at `/data`. Generated domains are configured for both frontends. The first MetricSteward build failed because the ignored `dist` wheel was absent from the source checkout; the Dockerfile now builds the wheel and regenerates the matching handoff in-image. Its corrected image built successfully, started Uvicorn on `0.0.0.0:8001`, and reached the health check; deployment is retrying with `PORT=8001`.
4. **Preserve data.** Back up the workspace SQLite catalog and review history, upload the consistent snapshot to the MetricSteward Railway volume, and verify counts/checksums through the read-only API. The workspace database has 1 import and 1 review; the separate Compose volume has 1 import and 0 reviews and is not the migration source.
5. **Deploy and validate.** Railway applies this environment as one staged batch, so generated frontend domains may become public before data is seeded. The app is read-only and has no catalog writes; upload the verified snapshot immediately after the MetricSteward backend becomes healthy. Verify health/private DNS/read-only behavior and the 1-import/1-review catalog before sharing the generated URLs. Validate rate limits, calculations, mobile layout, redaction, and absence of secrets in logs. Exercise rollback before sharing the URL.

## Acceptance and Rollback

- Only frontend services have public domains; APIs and database are private.
- Public users can inspect synthetic results and calculate metrics but cannot import evidence or write review records.
- Existing catalog and review history are present with matching verified counts/checksums; public responses redact reviewer identity and notes while educational labels and promotion blocks remain unchanged.
- Both frontends and API health checks pass, and the shared metric calculator remains consistent with the local test suite.
- Deployments use the existing local Compose defaults for development and Railway private addresses only through runtime variables.

Rollback by redeploying the previous application images and restoring the verified SQLite backup to the Railway volume if necessary. Do not delete the source catalog or backup until migration verification is complete.

## Current Local Preparation

Both frontend Dockerfiles now copy nginx configuration as a startup template and accept runtime upstream variables, retaining Compose defaults. Both nginx frontends apply API request-rate limiting. Both images rebuilt successfully. MetricSteward read-only mode is implemented in the API and UI; API tests verify writes/exports are blocked and public review details are redacted. The frontend build passes, the runtime banner was browser-checked, and these proxied health checks passed:

- `http://127.0.0.1:8080/api/health`
- `http://127.0.0.1:8082/api/steward/health`

All four local Compose services remain running and healthy; local MetricSteward remains writable by default. The MetricSteward image builds without a preexisting `dist/` directory, and its generated wheel SHA-256 matches the generated handoff. The fix is committed and pushed as `fe3b7a5`; its GitHub CI and Railway deployment are in progress.

## Live Deployment

- FrameSignal Lab: https://framesignal-frontend-production.up.railway.app
- MetricSteward: https://metricsteward-frontend-production.up.railway.app
- Railway project: https://railway.com/project/e1099ee7-3d42-426e-8d77-fe7bf7ac3cc6?environmentId=504f5280-055f-45dc-aa75-4fb9f1421481
- GitHub CI for deployed commit: https://github.com/jems0906/FrameSignal-Lab/actions/runs/41526791405 (all three jobs passed)

Both sites and API health routes return successfully. MetricSteward shows five definitions and one preserved review with reviewer details redacted. Public import, export, and review-write routes return `403`. Its `/data/catalog.sqlite3` volume contains the verified workspace snapshot (1 import, 1 review; SQLite integrity `ok`; SHA-256 `1f6be3c33659660964a568b188bc6fffc37f922951b2ee9dafce40f6f94ae041`). The separate Compose volume was not used.

The MetricSteward catalog remains a single-replica SQLite read-only demo. Railway Pro is billed at the current published $20/month base with $20 of included resource usage; excess usage is metered. Public deployment does not add authentication or constitute independent review, real-world approval, or production suitability. If the demo later needs writes, multiple replicas, or higher availability, add authentication and migrate to PostgreSQL first.

## Monitoring and Spending Controls

The `Public demo health` workflow in `.github/workflows/uptime.yml` checks both public API health URLs at 00:17, 06:17, 12:17, and 18:17 UTC. It requires HTTP success and JSON `status=ok` from both APIs, plus `read_only=true` from MetricSteward. Requests have bounded retries and timeouts, and the job has a five-minute limit. It does not import evidence, write reviews, or export catalog data.

Run the check on demand with `gh workflow run uptime.yml --repo jems0906/FrameSignal-Lab`. Review results in GitHub Actions under `Public demo health`. Enable Actions failure notifications in [GitHub notification settings](https://github.com/settings/notifications) for the account that triggers or schedules the workflow. Email delivery has not been configured or verified by this setup; a failed check alone does not guarantee an email alert.

The private repository's Actions minute allowance applies. One job runs every six hours, approximately 120 runs per 30 days, without an external uptime account or monitoring secrets. Scheduled Actions can be delayed or dropped and are not an availability guarantee; failures between checks may go undetected.

Railway's workspace usage controls were inspected on November 2, 2026. Compute soft limits send email alerts; hard limits stop all workspace resources, including unrelated projects. At the user's direction, spending alerts and hard limits were left unchanged. No paid monitoring service was added.

Both nginx proxies refresh private-service DNS through Railway's container resolver every ten seconds. This prevents a frontend started before a backend redeploy from retaining the backend's previous IP address. After any deployment, verify the API routes as well as the frontend pages; a healthy static page does not prove its API upstream is reachable.