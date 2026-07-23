from pathlib import Path
import csv
import json
import math

ROOT = Path(__file__).resolve().parents[1]


def read_csv(relative):
    with (ROOT / relative).open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def find_row(rows, **conditions):
    return next(row for row in rows if all(row[key] == value for key, value in conditions.items()))


def test_repository_files_exist():
    expected = [
        "analysis.py",
        "data/pbmc_media_blend.csv",
        "outputs/benchmark_metrics.csv",
        "manuscript/Cell_Culture_AI_Benchmark_preprint.pdf",
        "CITATION.cff",
        "LICENSE",
    ]
    for relative in expected:
        assert (ROOT / relative).exists(), relative


def test_dataset_dimensions():
    assert len(read_csv("data/pbmc_media_blend.csv")) == 24
    assert len(read_csv("data/kphaffii_four_factor_train.csv")) == 86
    assert len(read_csv("data/kphaffii_four_factor_validation.csv")) == 16
    assert len(read_csv("data/kphaffii_nine_factor.csv")) == 77


def test_round_aware_pbmc_metric():
    rows = read_csv("outputs/benchmark_metrics.csv")
    result = find_row(rows, task="PBMC", model="Extra trees", protocol="Forward-round")
    assert math.isclose(float(result["rmse_mean"]), 18.60312587625698, rel_tol=1e-9)


def test_external_validation_reports_rank_and_absolute_transfer():
    rows = read_csv("outputs/external_validation_metrics.csv")
    result = find_row(rows, model="Ridge")
    assert math.isclose(float(result["Spearman"]), 0.7470588235294118, rel_tol=1e-9)
    assert float(result["R2"]) < 0


def test_noncompensatory_and_pareto_outputs():
    homeostasis = read_csv("outputs/pbmc_homeostasis_scores.csv")
    assert homeostasis[0]["formulation"] == "11"
    assert len(read_csv("outputs/kp4_pareto_front.csv")) == 6


def test_summary_counts():
    summary = json.loads((ROOT / "outputs/results_summary.json").read_text(encoding="utf-8"))
    assert summary["seed"] == 2026
    assert summary["datasets"]["PBMC"]["n_rounds"] == 4
    assert summary["datasets"]["K. phaffii 4-factor"]["n_rounds"] == 7
    assert summary["datasets"]["K. phaffii 9-factor"]["n_rounds"] == 7
