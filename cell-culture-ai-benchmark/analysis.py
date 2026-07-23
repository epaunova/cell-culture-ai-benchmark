#!/usr/bin/env python3
"""Reproduce the public-data benchmark and figures for the manuscript.

The input CSV files are derived from the CC BY 4.0 source-data workbook of:
Narayanan et al., Nature Communications (2025), DOI:10.1038/s41467-025-61113-5.

No proprietary data are used. The analysis is deterministic given scikit-learn,
NumPy, SciPy and Matplotlib versions recorded in requirements.txt.
"""
from __future__ import annotations

import csv
import json
import math
from pathlib import Path
from typing import Dict, Iterable, List, Sequence, Tuple

import matplotlib.pyplot as plt
import numpy as np
from scipy.stats import spearmanr
from sklearn.base import clone
from sklearn.compose import ColumnTransformer
from sklearn.dummy import DummyRegressor
from sklearn.ensemble import ExtraTreesRegressor, RandomForestRegressor
from sklearn.linear_model import Ridge
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score
from sklearn.model_selection import LeaveOneGroupOut, RepeatedKFold
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder, StandardScaler

ROOT = Path(__file__).resolve().parent
DATA = ROOT / "data"
FIG = ROOT / "figures"
OUTPUT = ROOT / "outputs"
FIG.mkdir(exist_ok=True)
OUTPUT.mkdir(exist_ok=True)

SEED = 2026
MODELS = ["Mean", "Ridge", "Random forest", "Extra trees"]
PROTOCOLS = ["Random CV", "Round-blocked", "Forward-round"]


def read_csv(path: Path) -> List[dict]:
    with path.open(newline="", encoding="utf-8") as fh:
        return list(csv.DictReader(fh))


def load_pbmc() -> Tuple[np.ndarray, np.ndarray, np.ndarray]:
    rows = read_csv(DATA / "pbmc_media_blend.csv")
    X = np.array([[float(r[k]) for k in ("DMEM_pct", "RPMI10_pct", "XVIVO_pct", "AR5_pct")] for r in rows])
    y = np.array([float(r["average_viability_pct"]) for r in rows])
    g = np.array([int(r["round"]) for r in rows])
    return X, y, g


def load_kp4(path: str) -> Tuple[np.ndarray, np.ndarray, np.ndarray | None]:
    rows = read_csv(DATA / path)
    X = np.empty((len(rows), 4), dtype=object)
    X[:, 0] = [r["carbon_source"] for r in rows]
    for j, k in enumerate(("carbon_concentration_g_L", "glycerol_pct", "methanol_pct"), start=1):
        X[:, j] = [float(r[k]) for r in rows]
    y = np.array([float(r["specific_productivity_mg_L_OD600"]) for r in rows])
    g = np.array([int(r["round"]) for r in rows]) if "round" in rows[0] else None
    return X, y, g


def load_kp9() -> Tuple[np.ndarray, np.ndarray, np.ndarray]:
    rows = read_csv(DATA / "kphaffii_nine_factor.csv")
    keys = (
        "carbon_source", "carbon_concentration_g_L", "glycerol_pct", "methanol_pct",
        "glutathione_outgrowth", "tween_outgrowth", "glutathione_production",
        "tween_production", "pH",
    )
    X = np.empty((len(rows), len(keys)), dtype=object)
    X[:, 0] = [r[keys[0]] for r in rows]
    for j, k in enumerate(keys[1:], start=1):
        X[:, j] = [float(r[k]) for r in rows]
    y = np.array([float(r["specific_productivity_mg_L_OD600"]) for r in rows])
    g = np.array([int(r["round"]) for r in rows])
    return X, y, g


def make_models(n_features: int, categorical_indices: Sequence[int]) -> Dict[str, object]:
    categorical_indices = list(categorical_indices)
    numeric_indices = [i for i in range(n_features) if i not in categorical_indices]
    pre = ColumnTransformer(
        [
            ("num", StandardScaler(), numeric_indices),
            ("cat", OneHotEncoder(handle_unknown="ignore", sparse_output=False), categorical_indices),
        ],
        sparse_threshold=0.0,
    )
    return {
        "Mean": DummyRegressor(strategy="mean"),
        "Ridge": Pipeline([("pre", pre), ("model", Ridge(alpha=1.0))]),
        "Random forest": Pipeline(
            [
                ("pre", pre),
                ("model", RandomForestRegressor(
                    n_estimators=150, min_samples_leaf=2, max_features=0.8,
                    random_state=SEED, n_jobs=-1,
                )),
            ]
        ),
        "Extra trees": Pipeline(
            [
                ("pre", pre),
                ("model", ExtraTreesRegressor(
                    n_estimators=150, min_samples_leaf=2, max_features=0.8,
                    random_state=SEED, n_jobs=-1,
                )),
            ]
        ),
    }


def safe_spearman(y: np.ndarray, pred: np.ndarray) -> float:
    if len(np.unique(y)) < 2 or len(np.unique(pred)) < 2:
        return float("nan")
    return float(spearmanr(y, pred).statistic)


def metric_row(y: np.ndarray, pred: np.ndarray) -> Dict[str, float]:
    return {
        "MAE": float(mean_absolute_error(y, pred)),
        "RMSE": float(math.sqrt(mean_squared_error(y, pred))),
        "Spearman": safe_spearman(y, pred),
        "R2": float(r2_score(y, pred)) if len(y) > 1 else float("nan"),
    }


def protocol_splits(X: np.ndarray, y: np.ndarray, groups: np.ndarray) -> Dict[str, List[Tuple[np.ndarray, np.ndarray]]]:
    unique = sorted(set(int(x) for x in groups))
    return {
        "Random CV": list(RepeatedKFold(n_splits=4, n_repeats=3, random_state=SEED).split(X)),
        "Round-blocked": list(LeaveOneGroupOut().split(X, y, groups)),
        "Forward-round": [(np.where(groups < r)[0], np.where(groups == r)[0]) for r in unique[1:]],
    }


def benchmark(X: np.ndarray, y: np.ndarray, groups: np.ndarray, categorical_indices: Sequence[int]) -> Dict[str, dict]:
    output: Dict[str, dict] = {}
    splits = protocol_splits(X, y, groups)
    for model_name, estimator in make_models(X.shape[1], categorical_indices).items():
        output[model_name] = {}
        for protocol, protocol_pairs in splits.items():
            fold_rows = []
            pooled_y: List[float] = []
            pooled_p: List[float] = []
            for train, test in protocol_pairs:
                fitted = clone(estimator)
                fitted.fit(X[train], y[train])
                pred = fitted.predict(X[test])
                fold_rows.append(metric_row(y[test], pred))
                pooled_y.extend(y[test].tolist())
                pooled_p.extend(pred.tolist())
            summary = {}
            for key in ("MAE", "RMSE", "Spearman", "R2"):
                values = np.array([r[key] for r in fold_rows], dtype=float)
                summary[key] = {
                    "mean": float(np.nanmean(values)),
                    "sd": float(np.nanstd(values, ddof=1)) if np.sum(~np.isnan(values)) > 1 else float("nan"),
                }
            summary["pooled"] = metric_row(np.asarray(pooled_y), np.asarray(pooled_p))
            summary["n_folds"] = len(fold_rows)
            output[model_name][protocol] = summary
    return output


def round_summary(y: np.ndarray, groups: np.ndarray) -> List[dict]:
    rows = []
    for r in sorted(set(int(v) for v in groups)):
        vals = y[groups == r]
        rows.append({
            "round": r,
            "n": int(len(vals)),
            "mean": float(np.mean(vals)),
            "median": float(np.median(vals)),
            "best": float(np.max(vals)),
        })
    return rows


def external_validation(X_train: np.ndarray, y_train: np.ndarray, X_test: np.ndarray, y_test: np.ndarray) -> Tuple[dict, dict]:
    results, predictions = {}, {}
    for model_name, estimator in make_models(X_train.shape[1], [0]).items():
        fitted = clone(estimator)
        fitted.fit(X_train, y_train)
        pred = fitted.predict(X_test)
        results[model_name] = metric_row(y_test, pred)
        predictions[model_name] = [float(x) for x in pred]
    return results, predictions


def noncompensatory_homeostasis() -> Tuple[List[dict], List[dict]]:
    rows = read_csv(DATA / "pbmc_cytokine_homeostasis.csv")
    experimental = [r for r in rows if r["formulation"] != "C"]
    metrics = np.array([
        [
            float(r["total_viability_change_pct"]),
            float(r["B_cell_change_pct"]),
            float(r["NK_cell_change_pct"]),
            float(r["T_cell_change_pct"]),
        ] for r in experimental
    ])
    scales = np.percentile(np.abs(metrics), 75, axis=0)
    utilities = np.exp(-np.abs(metrics) / scales)
    scored = []
    for i, row in enumerate(experimental):
        scored.append({
            "formulation": row["formulation"],
            "score_min": float(np.min(utilities[i])),
            "score_geometric": float(np.exp(np.mean(np.log(utilities[i])))),
            "score_mean": float(np.mean(utilities[i])),
            "total_viability_change_pct": float(metrics[i, 0]),
            "B_cell_change_pct": float(metrics[i, 1]),
            "NK_cell_change_pct": float(metrics[i, 2]),
            "T_cell_change_pct": float(metrics[i, 3]),
        })
    scored.sort(key=lambda x: x["score_min"], reverse=True)

    # Sensitivity: multiply all tolerance scales together by 0.5--2.0.
    sensitivity = []
    for multiplier in np.linspace(0.5, 2.0, 16):
        u = np.exp(-np.abs(metrics) / (scales * multiplier))
        order = np.argsort(np.min(u, axis=1))[::-1]
        sensitivity.append({
            "scale_multiplier": float(multiplier),
            "top_formulation": experimental[int(order[0])]["formulation"],
            "top_score": float(np.min(u, axis=1)[int(order[0])]),
        })
    return scored, sensitivity


def pareto_front_kp4(X: np.ndarray, y: np.ndarray, groups: np.ndarray) -> Tuple[List[dict], np.ndarray]:
    numeric = np.asarray(X[:, 1:], dtype=float)
    mins = numeric.min(axis=0)
    ranges = np.where(numeric.max(axis=0) - mins == 0, 1.0, numeric.max(axis=0) - mins)
    burden = ((numeric - mins) / ranges).mean(axis=1)
    efficient = []
    for i in range(len(y)):
        dominated = any(
            (burden[j] <= burden[i] and y[j] >= y[i]) and
            (burden[j] < burden[i] or y[j] > y[i])
            for j in range(len(y)) if j != i
        )
        if not dominated:
            efficient.append(i)
    efficient.sort(key=lambda i: burden[i])
    rows = []
    for i in efficient:
        rows.append({
            "index": int(i), "round": int(groups[i]), "carbon_source": str(X[i, 0]),
            "carbon_concentration_g_L": float(X[i, 1]), "glycerol_pct": float(X[i, 2]),
            "methanol_pct": float(X[i, 3]), "specific_productivity_mg_L_OD600": float(y[i]),
            "normalized_process_load_proxy": float(burden[i]),
        })
    return rows, burden


def write_csv(path: Path, rows: List[dict]) -> None:
    if not rows:
        return
    with path.open("w", newline="", encoding="utf-8") as fh:
        writer = csv.DictWriter(fh, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)


def plot_workflow() -> None:
    fig, ax = plt.subplots(figsize=(10.5, 3.4))
    ax.axis("off")
    boxes = [
        (0.02, "Public iterative\nexperiments"),
        (0.22, "Round-aware\ndata partitioning"),
        (0.42, "Transparent\nbaselines"),
        (0.62, "Constraint-aware\nranking"),
        (0.82, "External and\nprospective tests"),
    ]
    for x, label in boxes:
        ax.add_patch(plt.Rectangle((x, 0.32), 0.16, 0.38, fill=False, linewidth=1.4, transform=ax.transAxes))
        ax.text(x + 0.08, 0.51, label, ha="center", va="center", fontsize=10, transform=ax.transAxes)
    for x, _ in boxes[:-1]:
        ax.annotate("", xy=(x + 0.195, 0.51), xytext=(x + 0.16, 0.51),
                    arrowprops=dict(arrowstyle="->", lw=1.3), xycoords=ax.transAxes)
    ax.text(0.5, 0.12, "Leakage-resistant evaluation before optimization claims", ha="center", fontsize=11, transform=ax.transAxes)
    fig.tight_layout()
    for ext in ("pdf", "png"):
        fig.savefig(FIG / f"benchmark_workflow.{ext}", dpi=300, bbox_inches="tight")
    plt.close(fig)


def plot_round_progression(summaries: Dict[str, List[dict]]) -> None:
    fig, ax = plt.subplots(figsize=(8.7, 5.1))
    for label, rows in summaries.items():
        means = np.array([r["median"] for r in rows])
        best = np.array([r["best"] for r in rows])
        allvals = np.concatenate([means, best])
        lo, hi = float(np.min(allvals)), float(np.max(allvals))
        den = hi - lo if hi > lo else 1.0
        x = [r["round"] for r in rows]
        ax.plot(x, (means - lo) / den, marker="o", label=f"{label}: median")
        ax.plot(x, (best - lo) / den, marker="s", linestyle="--", label=f"{label}: best")
    ax.set_xlabel("Experimental round")
    ax.set_ylabel("Within-task normalized outcome")
    ax.set_ylim(-0.05, 1.05)
    ax.set_title("Outcome progression across iterative media-development tasks")
    ax.grid(True, alpha=0.25)
    ax.legend(ncol=2, fontsize=8, frameon=False)
    fig.tight_layout()
    for ext in ("pdf", "png"):
        fig.savefig(FIG / f"round_progression.{ext}", dpi=300, bbox_inches="tight")
    plt.close(fig)


def plot_protocol_heatmap(benchmarks: Dict[str, dict], target_sd: Dict[str, float]) -> None:
    rows, labels = [], []
    for task in ("PBMC", "K. phaffii 4-factor", "K. phaffii 9-factor"):
        for model in MODELS:
            rows.append([benchmarks[task][model][p]["RMSE"]["mean"] / target_sd[task] for p in PROTOCOLS])
            labels.append(f"{task} — {model}")
    matrix = np.asarray(rows)
    fig, ax = plt.subplots(figsize=(8.3, 7.1))
    im = ax.imshow(matrix, aspect="auto")
    ax.set_xticks(range(len(PROTOCOLS)), PROTOCOLS)
    ax.set_yticks(range(len(labels)), labels, fontsize=8)
    for i in range(matrix.shape[0]):
        for j in range(matrix.shape[1]):
            ax.text(j, i, f"{matrix[i,j]:.2f}", ha="center", va="center", fontsize=7,
                    color="white" if matrix[i,j] > np.nanmedian(matrix) else "black")
    ax.set_title("Normalized RMSE changes with the validation protocol")
    cbar = fig.colorbar(im, ax=ax, fraction=0.035, pad=0.03)
    cbar.set_label("RMSE / target standard deviation")
    fig.tight_layout()
    for ext in ("pdf", "png"):
        fig.savefig(FIG / f"protocol_nrmse_heatmap.{ext}", dpi=300, bbox_inches="tight")
    plt.close(fig)


def plot_external_validation(y: np.ndarray, predictions: Dict[str, List[float]]) -> None:
    fig, ax = plt.subplots(figsize=(6.2, 5.3))
    lo = min(float(np.min(y)), min(min(v) for v in predictions.values()))
    hi = max(float(np.max(y)), max(max(v) for v in predictions.values()))
    ax.plot([lo, hi], [lo, hi], linestyle="--", linewidth=1, label="Identity")
    for model in ("Ridge", "Random forest", "Extra trees"):
        ax.scatter(y, predictions[model], label=model, alpha=0.8)
    ax.set_xlabel("Observed specific productivity (mg L$^{-1}$ OD$_{600}^{-1}$)")
    ax.set_ylabel("Predicted specific productivity")
    ax.set_title("Held-out validation conditions expose limited absolute transfer")
    ax.legend(frameon=False, fontsize=8)
    ax.grid(True, alpha=0.22)
    fig.tight_layout()
    for ext in ("pdf", "png"):
        fig.savefig(FIG / f"external_validation.{ext}", dpi=300, bbox_inches="tight")
    plt.close(fig)


def plot_homeostasis(scored: List[dict]) -> None:
    ordered = sorted(scored, key=lambda r: int(r["formulation"]))
    x = [r["formulation"] for r in ordered]
    y = [r["score_min"] for r in ordered]
    fig, ax = plt.subplots(figsize=(8.1, 4.5))
    ax.bar(x, y)
    top = max(scored, key=lambda r: r["score_min"])
    ax.annotate(f"Balanced candidate: {top['formulation']}",
                xy=(x.index(top["formulation"]), top["score_min"]),
                xytext=(0.57, 0.91), textcoords="axes fraction",
                arrowprops=dict(arrowstyle="->"), fontsize=9)
    ax.set_xlabel("Cytokine formulation")
    ax.set_ylabel("Worst-dimension utility")
    ax.set_ylim(0, 1.0)
    ax.set_title("Non-compensatory PBMC homeostasis ranking")
    ax.grid(axis="y", alpha=0.22)
    fig.tight_layout()
    for ext in ("pdf", "png"):
        fig.savefig(FIG / f"pbmc_noncompensatory_score.{ext}", dpi=300, bbox_inches="tight")
    plt.close(fig)


def plot_pareto(X: np.ndarray, y: np.ndarray, burden: np.ndarray, frontier: List[dict]) -> None:
    fig, ax = plt.subplots(figsize=(6.6, 5.0))
    ax.scatter(burden, y, alpha=0.55, label="Evaluated formulations")
    fx = [r["normalized_process_load_proxy"] for r in frontier]
    fy = [r["specific_productivity_mg_L_OD600"] for r in frontier]
    ax.plot(fx, fy, marker="o", linewidth=1.5, label="Pareto frontier")
    for r in frontier:
        ax.annotate(str(r["round"]), (r["normalized_process_load_proxy"], r["specific_productivity_mg_L_OD600"]),
                    xytext=(3, 3), textcoords="offset points", fontsize=7)
    ax.set_xlabel("Normalized process-load proxy (lower is better)")
    ax.set_ylabel("Specific productivity (mg L$^{-1}$ OD$_{600}^{-1}$)")
    ax.set_title("Resource-aware ranking retains multiple efficient media candidates")
    ax.legend(frameon=False, fontsize=8)
    ax.grid(True, alpha=0.22)
    fig.tight_layout()
    for ext in ("pdf", "png"):
        fig.savefig(FIG / f"kp4_pareto.{ext}", dpi=300, bbox_inches="tight")
    plt.close(fig)


def main() -> None:
    X_pb, y_pb, g_pb = load_pbmc()
    X_kp4, y_kp4, g_kp4 = load_kp4("kphaffii_four_factor_train.csv")
    X_val, y_val, _ = load_kp4("kphaffii_four_factor_validation.csv")
    X_kp9, y_kp9, g_kp9 = load_kp9()

    benchmarks = {
        "PBMC": benchmark(X_pb, y_pb, g_pb, []),
        "K. phaffii 4-factor": benchmark(X_kp4, y_kp4, g_kp4, [0]),
        "K. phaffii 9-factor": benchmark(X_kp9, y_kp9, g_kp9, [0]),
    }
    external, predictions = external_validation(X_kp4, y_kp4, X_val, y_val)
    scored, sensitivity = noncompensatory_homeostasis()
    frontier, burden = pareto_front_kp4(X_kp4, y_kp4, g_kp4)
    summaries = {
        "PBMC": round_summary(y_pb, g_pb),
        "K. phaffii 4-factor": round_summary(y_kp4, g_kp4),
        "K. phaffii 9-factor": round_summary(y_kp9, g_kp9),
    }

    results = {
        "seed": SEED,
        "datasets": {
            "PBMC": {"n": len(y_pb), "n_rounds": len(set(g_pb)), "target_sd": float(np.std(y_pb, ddof=1))},
            "K. phaffii 4-factor": {"n": len(y_kp4), "n_rounds": len(set(g_kp4)), "target_sd": float(np.std(y_kp4, ddof=1)), "external_n": len(y_val)},
            "K. phaffii 9-factor": {"n": len(y_kp9), "n_rounds": len(set(g_kp9)), "target_sd": float(np.std(y_kp9, ddof=1))},
        },
        "round_summaries": summaries,
        "benchmarks": benchmarks,
        "external_validation": external,
        "external_predictions": predictions,
        "homeostasis_scores": scored,
        "homeostasis_scale_sensitivity": sensitivity,
        "kp4_pareto_front": frontier,
        "process_load_definition": "mean min-max normalized carbon concentration, glycerol percentage, and methanol percentage; illustrative proxy, not monetary cost",
    }
    with (OUTPUT / "results_summary.json").open("w", encoding="utf-8") as fh:
        json.dump(results, fh, indent=2, allow_nan=True)

    # Flat tables for verification and downstream use.
    flat = []
    for task, task_data in benchmarks.items():
        for model, model_data in task_data.items():
            for protocol, stats in model_data.items():
                flat.append({
                    "task": task, "model": model, "protocol": protocol,
                    "rmse_mean": stats["RMSE"]["mean"], "rmse_sd": stats["RMSE"]["sd"],
                    "mae_mean": stats["MAE"]["mean"], "spearman_mean": stats["Spearman"]["mean"],
                    "pooled_spearman": stats["pooled"]["Spearman"], "n_folds": stats["n_folds"],
                })
    write_csv(OUTPUT / "benchmark_metrics.csv", flat)
    write_csv(OUTPUT / "external_validation_metrics.csv", [{"model": k, **v} for k, v in external.items()])
    write_csv(OUTPUT / "pbmc_homeostasis_scores.csv", scored)
    write_csv(OUTPUT / "kp4_pareto_front.csv", frontier)

    plot_workflow()
    plot_round_progression(summaries)
    plot_protocol_heatmap(benchmarks, {k: v["target_sd"] for k, v in results["datasets"].items()})
    plot_external_validation(y_val, predictions)
    plot_homeostasis(scored)
    plot_pareto(X_kp4, y_kp4, burden, frontier)

    print(json.dumps({
        "datasets": results["datasets"],
        "external_validation": external,
        "top_homeostasis": scored[:3],
        "pareto_n": len(frontier),
    }, indent=2))


if __name__ == "__main__":
    main()
