import hashlib
import json
from pathlib import Path

from framesignal_metrics.handoff import build_metricsteward_handoff


ROOT = Path(__file__).resolve().parents[1]


def main():
    source = ROOT / "reports" / "latest.json"
    raw = source.read_bytes()
    handoff = build_metricsteward_handoff(json.loads(raw), hashlib.sha256(raw).hexdigest())
    wheel = ROOT / "dist" / "framesignal_metrics-1.0.0-py3-none-any.whl"
    if not wheel.exists():
        raise FileNotFoundError("Build the framesignal-metrics wheel before exporting its handoff.")
    handoff["library"].update({"wheel_filename": wheel.name, "wheel_sha256": hashlib.sha256(wheel.read_bytes()).hexdigest()})
    destination = ROOT / "reports" / "metricsteward_handoff.json"
    destination.write_text(json.dumps(handoff, indent=2, allow_nan=False) + "\n", encoding="utf-8")
    print(f"Prepared {destination}; educational-only, not imported or approved.")


if __name__ == "__main__":
    main()