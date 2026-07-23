#!/usr/bin/env python3
"""Fast integrity check for the released benchmark outputs."""
from pathlib import Path
import csv
import json
import math

ROOT = Path(__file__).resolve().parent


def read_csv(path: Path):
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def find_row(rows, **conditions):
    for row in rows:
        if all(row[key] == value for key, value in conditions.items()):
            return row
    raise AssertionError(f"Missing row: {conditions}")


def main():
    required = [
        "analysis.py",
        "data/pbmc_media_blend.csv",
        "data/kphaffii_four_factor_train.csv",
        "data/kphaffii_four_factor_validation.csv",
        "data/kphaffii_nine_factor.csv",
        "outputs/benchmark_metrics.csv",
        "outputs/external_validation_metrics.csv",
        "outputs/pbmc_homeostasis_scores.csv",
        "outputs/kp4_pareto_front.csv",
        "outputs/results_summary.json",
        "manuscript/Cell_Culture_AI_Benchmark_preprint.pdf",
        "CITATION.cff",
        "LICENSE",
    ]
    for relative in required:
        assert (ROOT / relative).exists(), relative

    assert len(read_csv(ROOT / "data/pbmc_media_blend.csv")) == 24
    assert len(read_csv(ROOT / "data/kphaffii_four_factor_train.csv")) == 86
    assert len(read_csv(ROOT / "data/kphaffii_four_factor_validation.csv")) == 16
    assert len(read_csv(ROOT / "data/kphaffii_nine_factor.csv")) == 77

    metrics = read_csv(ROOT / "outputs/benchmark_metrics.csv")
    assert len(metrics) == 36
    pbmc = find_row(metrics, task="PBMC", model="Extra trees", protocol="Forward-round")
    assert math.isclose(float(pbmc["rmse_mean"]), 18.60312587625698, rel_tol=1e-9)

    external = read_csv(ROOT / "outputs/external_validation_metrics.csv")
    ridge = find_row(external, model="Ridge")
    assert math.isclose(float(ridge["Spearman"]), 0.7470588235294118, rel_tol=1e-9)
    assert float(ridge["R2"]) < 0

    homeostasis = read_csv(ROOT / "outputs/pbmc_homeostasis_scores.csv")
    assert homeostasis[0]["formulation"] == "11"
    assert math.isclose(float(homeostasis[0]["score_min"]), 0.814989477337779, rel_tol=1e-9)

    pareto = read_csv(ROOT / "outputs/kp4_pareto_front.csv")
    assert len(pareto) == 6

    summary = json.loads((ROOT / "outputs/results_summary.json").read_text(encoding="utf-8"))
    assert summary["seed"] == 2026
    assert summary["datasets"]["PBMC"]["n"] == 24
    assert summary["datasets"]["K. phaffii 4-factor"]["external_n"] == 16
    assert summary["datasets"]["K. phaffii 9-factor"]["n"] == 77

    print("Precomputed benchmark verification passed.")
    print("24 PBMC rows; 86 four-factor training rows; 16 held-out rows; 77 nine-factor rows.")
    print("Key model, homeostasis, and Pareto results match the release.")


if __name__ == "__main__":
    main()
