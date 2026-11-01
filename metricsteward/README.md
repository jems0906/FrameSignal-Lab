# MetricSteward

A separate local application in the FrameSignal monorepo: educational metric catalog, immutable evidence-import history, and append-only review records. It consumes the same `framesignal-metrics` library as FrameSignal and its notebooks. It does not approve the rejected proxies for real-world decisions.

## Run

From the repository root, install backend requirements and prepare the versioned wheel/report/handoff using the root README commands. Then:

```powershell
python -m uvicorn metricsteward.api:app --app-dir metricsteward/backend --host 127.0.0.1 --port 8001
```

In another terminal:

```powershell
npm --prefix metricsteward/frontend ci
npm --prefix metricsteward/frontend run dev
```

Open http://localhost:5174. API documentation: http://127.0.0.1:8001/docs. FrameSignal stays at http://localhost:5173. Each backend uses the same installed package; no metric formulas are duplicated in JavaScript.

## Catalog Workflow

Import FrameSignal's frozen educational handoff. The API checks the exact source report, wheel checksum, library version, and educational status before committing a catalog version. Failed validation leaves no partial import. Identical report/wheel pairs are idempotent and preserve reviews; changed evidence creates another immutable import.

Search/filter the five definitions and inspect agreement, known-truth reversals, limitations, and calibration flags. Record a named and explicitly attested self-review, or an accurately labeled user-reported peer-feedback record with an actual reference. Review decisions are educational acceptance, quarantine, or defer. **Real-world approval is blocked by the API and absent from the controls.** A review never changes imported scientific rejection/descriptive labels.

Export the catalog, original handoff, and review records as JSON. SQLite data persists at `metricsteward/data/catalog.sqlite3`; override `METRICSTEWARD_DATABASE` for isolated testing or another location. The data folder is ignored by Git. Records are append-only through the application API, not tamper-proof against local database administrators. Reviewer identities and peer feedback are not independently authenticated. There is no multi-user authentication or production deployment claim.

## Shared Calculation Contract

`POST /api/steward/calculate` accepts household/event/exposure records and a 7- or 14-day window. It calls `framesignal_metrics.calculate_household_metrics`, preserves all registered households, and returns null completion for non-starters. Fully observed binary late-return outcomes are required. Cross-app tests compare MetricSteward output to FrameSignal's calculator in all three scenarios and both windows.

## Containers and Tests

After preparing the wheel and handoff:

```powershell
docker compose up --build metricsteward-backend metricsteward-frontend
```

Container UI: http://localhost:8082. A named volume preserves its catalog. Builds use the repository root as context. Stop the native server on port 8001 before using the default container binding.

```powershell
python -m pytest metricsteward/backend/tests -q
python -m ruff check metricsteward/backend
npm --prefix metricsteward/frontend run build
```

Integration tests require the generated `dist` wheel and matching report/handoff; CI creates them before testing. UI and API smoke-test evidence is recorded in the root verification document, not claimed as external peer review or remote CI.