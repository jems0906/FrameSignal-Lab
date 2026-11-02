import json
import os
from pathlib import Path
from typing import Literal

import pandas as pd
from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from framesignal_metrics import METRICS, __version__, calculate_household_metrics
from pydantic import BaseModel, ConfigDict, Field

from metricsteward.store import CatalogStore


ROOT = Path(__file__).resolve().parents[3]


def redact_public_reviews(reviews: list[dict]) -> list[dict]:
    return [{**review, "reviewer": "Withheld", "notes": "Review details are withheld in the public demo.", "evidence_reference": ""} for review in reviews]


class ReviewRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")
    import_id: str = Field(pattern="^[a-f0-9]{64}$")
    reviewer: str = Field(min_length=1, max_length=120)
    review_kind: Literal["self", "reported_peer"] = "self"
    decision: str = Field(max_length=40)
    notes: str = Field(min_length=5, max_length=5000)
    evidence_reference: str = Field(default="", max_length=1000)
    attested: bool = False


class CalculationRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")
    households: list[dict] = Field(min_length=1, max_length=20000)
    events: list[dict] = Field(max_length=100000)
    exposures: list[dict] = Field(min_length=1, max_length=20000)
    window: Literal[7, 14] = 14


def create_app(database_path: Path | None = None, artifact_root: Path | None = None, read_only: bool | None = None) -> FastAPI:
    artifacts = artifact_root or ROOT
    database = database_path or Path(os.environ.get("METRICSTEWARD_DATABASE", str(ROOT / "metricsteward" / "data" / "catalog.sqlite3")))
    read_only_enabled = read_only if read_only is not None else os.environ.get("METRICSTEWARD_READ_ONLY", "").strip().lower() in {"1", "true", "yes", "on"}
    store = CatalogStore(database)
    app = FastAPI(title="MetricSteward", version="1.0.0", description="Local educational metric catalog and evidence review. No real-world approval.")
    app.state.store = store
    app.state.read_only = read_only_enabled
    app.add_middleware(CORSMiddleware, allow_origins=["http://localhost:5174", "http://127.0.0.1:5174"], allow_methods=["GET", "POST"], allow_headers=["*"])

    @app.get("/api/steward/health")
    def health():
        return {"status": "ok", "application": "MetricSteward", "metric_library_version": __version__, "education_only": True, "read_only": read_only_enabled}

    @app.post("/api/steward/imports/framesignal")
    def import_framesignal():
        if read_only_enabled:
            raise HTTPException(403, "Evidence imports are disabled in read-only mode.")
        try:
            handoff = json.loads((artifacts / "reports" / "metricsteward_handoff.json").read_bytes())
            report = (artifacts / "reports" / "latest.json").read_bytes()
            wheel = (artifacts / "dist" / f"framesignal_metrics-{__version__}-py3-none-any.whl").read_bytes()
            return store.import_evidence(handoff, report, wheel)
        except FileNotFoundError as error:
            raise HTTPException(422, "Build the shared wheel and run the FrameSignal report/handoff export first.") from error
        except (ValueError, KeyError, TypeError) as error:
            raise HTTPException(422, "Evidence validation failed; no catalog import was committed.") from error

    @app.get("/api/steward/imports")
    def imports():
        return store.list_imports()

    @app.get("/api/steward/metrics")
    def metrics(import_id: str | None = Query(None, pattern="^[a-f0-9]{64}$")):
        return store.list_metrics(import_id)

    @app.get("/api/steward/reviews")
    def reviews(import_id: str = Query(pattern="^[a-f0-9]{64}$")):
        records = store.list_reviews(import_id)
        return redact_public_reviews(records) if read_only_enabled else records

    @app.get("/api/steward/metrics/{metric_id}")
    def metric(metric_id: str, import_id: str = Query(pattern="^[a-f0-9]{64}$")):
        try:
            record = store.get_metric(import_id, metric_id)
            if read_only_enabled:
                record["reviews"] = redact_public_reviews(record["reviews"])
            return record
        except KeyError as error:
            raise HTTPException(404, "Metric evidence version not found.") from error

    @app.post("/api/steward/metrics/{metric_id}/reviews")
    def review(metric_id: str, request: ReviewRequest):
        if read_only_enabled:
            raise HTTPException(403, "Review writes are disabled in read-only mode.")
        if request.decision not in ("educational_accept", "quarantine", "defer"):
            raise HTTPException(409, "Real-world approval is blocked for synthetic educational evidence.")
        try:
            return store.record_review(metric_id=metric_id, **request.model_dump())
        except KeyError as error:
            raise HTTPException(404, "Metric evidence version not found.") from error
        except ValueError as error:
            raise HTTPException(422, str(error)) from error

    @app.get("/api/steward/exports/{import_id}")
    def export(import_id: str):
        if read_only_enabled:
            raise HTTPException(403, "Catalog exports are disabled in public read-only mode.")
        try:
            return JSONResponse(store.export_catalog(import_id), headers={"Content-Disposition": 'attachment; filename="metricsteward-catalog.json"'})
        except KeyError as error:
            raise HTTPException(404, "Evidence import not found.") from error

    @app.post("/api/steward/calculate")
    def calculate(request: CalculationRequest):
        try:
            events = pd.DataFrame(request.events) if request.events else pd.DataFrame(columns=["household_id", "day", "minutes", "qualified", "completed"])
            frame = calculate_household_metrics(pd.DataFrame(request.households), events, pd.DataFrame(request.exposures), request.window)
            if "returned_d29_56" not in frame or not frame.returned_d29_56.isin([0, 1]).all():
                raise ValueError("Fully observed binary return outcomes are required.")
            columns = ["household_id", *METRICS, "starter", "completed_any", "impressions"]
            records = frame[columns].astype(object).where(pd.notna(frame[columns]), None).to_dict("records")
            return {"metric_library_version": __version__, "household_count": len(frame), "window": request.window, "outcomes": records, "promotion_allowed": False}
        except (ValueError, KeyError, TypeError) as error:
            raise HTTPException(422, str(error)) from error

    return app


app = create_app()