import io
import json
import zipfile
from pathlib import Path

from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from framesignal_metrics import __version__ as metrics_version

from app.analysis.workbench import PLAN, analyze, operating_characteristics, validation_suite
from app.metrics.registry import household_metrics
from app.simulations.generator import SCENARIOS, simulate


app = FastAPI(title="FrameSignal Lab", version="1.0.0", description="Fictional household-level proxy validation. Not Netflix data or retention.")
app.add_middleware(CORSMiddleware, allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"], allow_methods=["GET"], allow_headers=["*"])


@app.get("/api/health")
def health():
    return {"status": "ok", "synthetic_only": True, "metric_library_version": metrics_version}


@app.get("/api/plan")
def plan():
    return {"plan": PLAN, "scenarios": {name: spec.description for name, spec in SCENARIOS.items()}}


@app.get("/api/analysis")
def analysis(scenario: str = Query("helpful", pattern="^(helpful|unrelated|misleading)$"), n: int = Query(2000, ge=100, le=20000), seed: int = Query(20261031, ge=0, le=2147483647)):
    return analyze(scenario, n, seed)


@app.get("/api/validation")
def validation():
    return validation_suite()


@app.get("/api/operating")
def operating():
    return operating_characteristics()


def _read_extension_report(name: str) -> dict:
    report_path = Path(__file__).resolve().parents[3] / "reports" / name
    try:
        return json.loads(report_path.read_bytes())
    except FileNotFoundError as error:
        raise HTTPException(503, "Generate the predeclared extension report before requesting it.") from error


@app.get("/api/observational")
def observational_extension():
    return _read_extension_report("observational_extension.json")


@app.get("/api/learned-proxy")
def learned_proxy_extension():
    return _read_extension_report("learned_proxy_extension.json")


@app.get("/api/export")
def export(scenario: str = Query("helpful", pattern="^(helpful|unrelated|misleading)$"), n: int = Query(2000, ge=100, le=20000), seed: int = Query(20261031, ge=0, le=2147483647)):
    data = simulate(scenario, n, seed)
    buffer = io.BytesIO()
    with zipfile.ZipFile(buffer, "w", zipfile.ZIP_DEFLATED) as archive:
        for name in ("households", "titles", "exposures", "events"):
            archive.writestr(f"{name}.csv", getattr(data, name).to_csv(index=False))
        archive.writestr("household_metrics.csv", household_metrics(data).to_csv(index=False))
        archive.writestr("analysis.json", json.dumps(analyze(scenario, n, seed), indent=2))
        archive.writestr("provenance.json", json.dumps({"seed": seed, "scenario": scenario, "n": n, "plan": PLAN, "metric_library": {"name": "framesignal-metrics", "version": metrics_version}, "oracle_fields": ["affinity", "return_probability"], "warning": "Oracle fields are simulation audit information; never use them or late outcomes as proxy inputs."}, indent=2))
    buffer.seek(0)
    return StreamingResponse(buffer, media_type="application/zip", headers={"Content-Disposition": f"attachment; filename=framesignal-{scenario}-{seed}.zip"})