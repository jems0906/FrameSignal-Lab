# FrameSignal Lab Railway Deployment Plan

**Status:** Private Railway project configured and initial deployment attempted. The MetricSteward image build failed because the ignored wheel was missing from the GitHub checkout. The Dockerfile fix now builds the wheel and matching handoff inside the image; that fix still needs to be pushed so Railway can redeploy.

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
3. **Create Railway configuration.** A private `FrameSignal Lab` project exists in the Pro workspace. Four GitHub-backed services are configured with the correct Dockerfile paths, private upstreams, and health checks; both backends have no public domain, MetricSteward is read-only, one replica is selected, and its volume is mounted at `/data`. Generated domains are configured for both frontends. The initial MetricSteward build failed because the ignored `dist` wheel was absent from the source checkout. The Dockerfile now builds the wheel and regenerates the matching handoff in-image, following the CI packaging command.
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

All four local Compose services remain running and healthy; local MetricSteward remains writable by default. The MetricSteward image builds without a preexisting `dist/` directory, and its generated wheel SHA-256 matches the generated handoff. The Dockerfile fix is local and uncommitted. Railway configuration has been applied, but the initial MetricSteward build failed; no app has passed live health verification yet.

## Next Gate

The user approved deployment of a public read-only demo and the Railway Pro workspace is confirmed. Next, commit and push the verified Dockerfile fix, let CI and Railway rebuild, confirm both APIs pass health checks, upload the consistent workspace SQLite snapshot through the authenticated Railway CLI, and verify 1 import/1 review with public redaction. Then validate both generated domains. The workspace SQLite database is the migration source; do not use the separate Compose volume.