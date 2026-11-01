import hashlib
import json
import sqlite3
from contextlib import contextmanager
from datetime import datetime, timezone
from pathlib import Path

from framesignal_metrics import __version__
from framesignal_metrics.handoff import validate_educational_handoff


class CatalogStore:
    def __init__(self, path: Path):
        self.path = path
        path.parent.mkdir(parents=True, exist_ok=True)
        with self.connect() as database:
            database.executescript("""
                CREATE TABLE IF NOT EXISTS imports (
                    import_id TEXT PRIMARY KEY,
                    imported_at TEXT NOT NULL,
                    source_report_sha256 TEXT NOT NULL,
                    wheel_sha256 TEXT NOT NULL,
                    handoff_json TEXT NOT NULL
                );
                CREATE TABLE IF NOT EXISTS metrics (
                    import_id TEXT NOT NULL REFERENCES imports(import_id),
                    metric_id TEXT NOT NULL,
                    entry_json TEXT NOT NULL,
                    PRIMARY KEY (import_id, metric_id)
                );
                CREATE TABLE IF NOT EXISTS reviews (
                    review_id INTEGER PRIMARY KEY AUTOINCREMENT,
                    import_id TEXT NOT NULL,
                    metric_id TEXT NOT NULL,
                    recorded_at TEXT NOT NULL,
                    reviewer TEXT NOT NULL,
                    review_kind TEXT NOT NULL,
                    decision TEXT NOT NULL,
                    notes TEXT NOT NULL,
                    evidence_reference TEXT NOT NULL,
                    FOREIGN KEY (import_id, metric_id) REFERENCES metrics(import_id, metric_id)
                );
            """)

    @contextmanager
    def connect(self):
        database = sqlite3.connect(self.path, timeout=10)
        database.row_factory = sqlite3.Row
        database.execute("PRAGMA foreign_keys = ON")
        try:
            with database:
                yield database
        finally:
            database.close()

    def import_evidence(self, handoff: dict, report_bytes: bytes, wheel_bytes: bytes) -> dict:
        entries = validate_educational_handoff(handoff, report_bytes, wheel_bytes)
        if handoff["library"]["version"] != __version__:
            raise ValueError("Installed shared library differs from the evidence version.")
        import_id = hashlib.sha256((handoff["source_report_sha256"] + handoff["library"]["wheel_sha256"]).encode()).hexdigest()
        imported_at = datetime.now(timezone.utc).isoformat()
        with self.connect() as database:
            cursor = database.execute("INSERT OR IGNORE INTO imports VALUES (?, ?, ?, ?, ?)", (
                import_id, imported_at, handoff["source_report_sha256"], handoff["library"]["wheel_sha256"], json.dumps(handoff),
            ))
            created = cursor.rowcount == 1
            if created:
                database.executemany("INSERT INTO metrics VALUES (?, ?, ?)", [(import_id, entry["metric_id"], json.dumps(entry)) for entry in entries])
        return {"import_id": import_id, "created": created, "metrics": len(entries), "promotion_allowed": False}

    def list_imports(self) -> list:
        with self.connect() as database:
            rows = database.execute("SELECT * FROM imports ORDER BY imported_at DESC, import_id DESC").fetchall()
        return [{**{key: row[key] for key in ("import_id", "imported_at", "source_report_sha256", "wheel_sha256")},
             "library_version": json.loads(row["handoff_json"])["library"]["version"],
             "source_seed": json.loads(row["handoff_json"])["source_seed"]} for row in rows]

    def list_metrics(self, import_id: str | None = None) -> list:
        if import_id is None:
            imports = self.list_imports()
            if not imports:
                return []
            import_id = imports[0]["import_id"]
        with self.connect() as database:
            rows = database.execute("SELECT metric_id, entry_json FROM metrics WHERE import_id = ? ORDER BY metric_id", (import_id,)).fetchall()
        result = []
        for row in rows:
            reviews = self.list_reviews(import_id, row["metric_id"])
            result.append({**json.loads(row["entry_json"]), "import_id": import_id,
                           "review_status": reviews[0]["decision"] if reviews else "pending_review", "review_count": len(reviews)})
        return result

    def get_metric(self, import_id: str, metric_id: str) -> dict:
        with self.connect() as database:
            row = database.execute("SELECT entry_json FROM metrics WHERE import_id = ? AND metric_id = ?", (import_id, metric_id)).fetchone()
        if row is None:
            raise KeyError("Metric evidence version not found.")
        reviews = self.list_reviews(import_id, metric_id)
        return {**json.loads(row["entry_json"]), "import_id": import_id,
                "review_status": reviews[0]["decision"] if reviews else "pending_review", "reviews": reviews}

    def list_reviews(self, import_id: str, metric_id: str | None = None) -> list:
        query = "SELECT * FROM reviews WHERE import_id = ?"
        params = [import_id]
        if metric_id is not None:
            query += " AND metric_id = ?"
            params.append(metric_id)
        with self.connect() as database:
            rows = database.execute(query + " ORDER BY review_id DESC", params).fetchall()
        return [dict(row) for row in rows]

    def record_review(self, import_id: str, metric_id: str, reviewer: str, review_kind: str,
                      decision: str, notes: str, evidence_reference: str = "", attested: bool = False) -> dict:
        self.get_metric(import_id, metric_id)
        if decision not in ("educational_accept", "quarantine", "defer"):
            raise ValueError("Real-world approval is blocked for synthetic educational evidence.")
        if review_kind not in ("self", "reported_peer") or not reviewer.strip() or not notes.strip() or not attested:
            raise ValueError("A named reviewer, substantive notes, and an explicit accuracy attestation are required.")
        if review_kind == "reported_peer" and not evidence_reference.strip():
            raise ValueError("User-reported peer feedback requires an actual feedback reference; it is not independently verified.")
        recorded_at = datetime.now(timezone.utc).isoformat()
        with self.connect() as database:
            cursor = database.execute("INSERT INTO reviews (import_id, metric_id, recorded_at, reviewer, review_kind, decision, notes, evidence_reference) VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
                                      (import_id, metric_id, recorded_at, reviewer.strip(), review_kind, decision, notes.strip(), evidence_reference.strip()))
            review_id = cursor.lastrowid
        return {"review_id": review_id, "recorded_at": recorded_at, "decision": decision, "promotion_allowed": False}

    def export_catalog(self, import_id: str) -> dict:
        with self.connect() as database:
            row = database.execute("SELECT handoff_json, imported_at FROM imports WHERE import_id = ?", (import_id,)).fetchone()
        if row is None:
            raise KeyError("Evidence import not found.")
        return {"application": "MetricSteward", "integration_status": "imported_educationally", "import_id": import_id, "imported_at": row["imported_at"],
                "handoff": json.loads(row["handoff_json"]), "metrics": self.list_metrics(import_id),
                "reviews": self.list_reviews(import_id), "promotion_allowed": False,
                "review_provenance": "Self-review or user-reported peer feedback only; the app cannot independently authenticate reviewers."}