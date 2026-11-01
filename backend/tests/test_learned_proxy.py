import json
from pathlib import Path

import app.analysis.learned_proxy as learned_proxy
from app.analysis.learned_proxy import learn_and_validate_proxy


def test_learned_proxy_freezes_before_generating_heldout(monkeypatch):
    real_simulate = learned_proxy.simulate
    split_calls = []

    def tracked_simulate(*args, **kwargs):
        split_calls.append(kwargs.get("split", args[4]))
        return real_simulate(*args, **kwargs)

    monkeypatch.setattr(learned_proxy, "simulate", tracked_simulate)
    result = learn_and_validate_proxy(seed=71, n=300, experiments_per_split=3, ridge_grid=(0.1, 1.0), agreement_draws=100)
    assert split_calls == ["train"] * 3 + ["validation"] * 3 + ["heldout"] * 3
    assert result["leakage_check"]
    assert result["weight_freeze_before_heldout"]
    assert result["unique_households"] == 2700
    assert result["split_households"] == {"train": 900, "validation": 900, "heldout": 900}
    assert result["model"]["selected_alpha"] in (0.1, 1.0)
    assert result["heldout_agreement"]["n_experiments"] == 3
    assert result["status"] == "exploratory_educational_only_not_surrogate_approval"
    assert not result.get("promotion_allowed", False)


def test_learned_proxy_contract_and_excluded_inputs():
    config = json.loads((Path(__file__).resolve().parents[2] / "configs" / "learned_proxy_extension.json").read_text())
    assert config["splits"] == ["train", "validation", "heldout"]
    assert config["features"] == ["qualified_starts", "viewing_days"]
    assert config["target"] == "returned_d29_56"
    assert "assignment" in config["forbidden_features"]
    assert "return_probability" in config["forbidden_features"]
    assert "latent_loyalty" in config["forbidden_features"]
    assert "Brier score" in config["selection_metric"]
    assert "do not include training/tuning weight uncertainty" in config["interval_scope"]
