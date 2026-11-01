# MetricSteward Handoff

## Current Status

The shared calculator is now packaged as `framesignal-metrics` v1.0.0. The FrameSignal compatibility wrapper delegates to it; both research notebooks include exact-parity checks. The dashboard CSV export is recomputed by a separate library consumer in regression tests. Valid zero-viewing populations remain in the denominator; malformed or incomplete input fails explicitly.

A versioned wheel and `reports/metricsteward_handoff.json` are generated and checked locally. **MetricSteward is now integrated as a separate app under `metricsteward/` in this repository.** Its API validates and imports the handoff, persists immutable evidence versions and append-only reviews, and computes household outcomes through this package. Cross-app parity tests cover every scenario and both windows. No external review or remote CI success is invented.

## Reproduce the Package and Evidence

From the repository root, using the same environment as the notebooks/API:

```powershell
python -m pip install -r backend/requirements.txt
python -m pip wheel --no-deps ./packages/framesignal-metrics --wheel-dir dist
python backend/run_analysis.py
python backend/export_metricsteward.py
python -m pytest -q
python backend/execute_notebooks.py
```

The backend Dockerfile installs the local library before starting the API. CI builds the wheel and publishes it with the handoff, full report, and executed notebooks. Notebook execution pins its kernel to the invoking interpreter rather than an ambiguous `python` executable. Interactive notebooks must select an environment in which the package is installed.

## Consumer Contract

MetricSteward must install this same wheel and use `framesignal_metrics.calculate_household_metrics`, not rewrite the formulas in JavaScript or a notebook. Preserve the whole registered population and observed zeros, the 7/14-day window, and the starter-selection warning. The producer contract and required columns are documented in the package README.

Before importing catalog entries, validate the handoff against the exact source report and wheel bytes:

```python
import json
from pathlib import Path
from framesignal_metrics.handoff import validate_educational_handoff

handoff = json.loads(Path("metricsteward_handoff.json").read_text())
entries = validate_educational_handoff(
    handoff,
    Path("latest.json").read_bytes(),
    Path(handoff["library"]["wheel_filename"]).read_bytes(),
)
```

The validator reconstructs entries from source evidence and checks report/wheel hashes. It detects mismatched artifacts and edited promotion flags, but does not authenticate authorship. MetricSteward persists the original handoff, library version, plan/report/wheel provenance and limitations for each evidence version. The producer handoff retains its original preparation marker; consumer exports separately mark `integration_status=imported_educationally`. Tests recompute household outcomes through both applications and compare values and denominator counts.

## Promotion Gates

- Educational availability means definitions/calculations are reusable and parity-tested; it is not evidence that the metric is a reliable retention proxy.
- Qualified starts and viewing days carry rejected general-surrogate status because positive short-term effects coexist with harmful known longer-horizon policy effects. Their held-out agreement does not clear the frozen 80% lower-bound screen.
- Completion remains descriptive because starting is post-assignment. Bootstrap precision does not fix selection.
- Watch time is a diagnostic, not a surrogate approved by this study. Later return is the fictional primary target, not Netflix retention.
- The +4 pp operating coverage flag remains unresolved evidence. Importing a catalog entry must not hide it.
- Every handoff entry has `education_use_only=true` and `promotion_allowed=false`. Real-world approval needs fresh scoped preregistered evidence, justified power, external review that actually occurs, and a separate documented approval decision.

These gates are deliberately not relaxed to make a portfolio claim pass. A failed proxy is a valid educational result, not a missing implementation feature.

## External Steps Still Required

No separate MetricSteward URL is needed for this monorepo integration. Publishing code or triggering fresh remote CI still requires repository access and authorization; local execution is not remote CI. Peer feedback must come from an actual reviewer before it is recorded as user-reported feedback. The app's implementation self-review is not independent peer review. Learned composites and observational extensions remain deferred under the original MVP instructions.