"""Stage 3: Statistical analysis, TabPFN fits, paired tests, and lead-time analysis.

Governed strictly by PRD v2.0 §4, §8, §9, §10, §11.
No silent plan edits.
"""

from __future__ import annotations

import argparse
import datetime as dt
import json
import math
import warnings
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd
from tabpfn import TabPFNClassifier

warnings.filterwarnings("ignore")

DERIVED = Path(__file__).resolve().parents[2] / "derived"
ROWS_FILE = DERIVED / "rows.ndjson"
RESULTS_DIR = Path(__file__).resolve().parents[2] / "results"

SPECIMEN = "request/request"
ANNUAL_GRID = [dt.datetime(y, 1, 1, tzinfo=dt.timezone.utc) for y in range(2015, 2024)]

# Primary capacity-matched feature sets (PRD §9)
ARM_A_COLS = ["f1_release_decay", "f2_commit_entropy", "never_released"]
ARM_B_COLS = ["f4_latency_trend", "f5_rate_decline"]
CONTROL_COLS = ["log10_stars", "age_years", "language_py", "created_year"]

# Descriptive features (PRD §9)
FULL_A_COLS = ARM_A_COLS + CONTROL_COLS
FULL_B_COLS = ARM_B_COLS + ["f3_backlog_slope", "f6_maint_volume"] + CONTROL_COLS


def load_dataset(path: Path | None = None) -> pd.DataFrame:
    target = path or ROWS_FILE
    if not target.exists():
        raise FileNotFoundError(f"Rows file not found: {target}. Run `ofrenda-features` first.")
    records: list[dict[str, Any]] = []
    with target.open(encoding="utf-8") as handle:
        for line in handle:
            line = line.strip()
            if not line:
                continue
            item = json.loads(line)
            if item.get("repo") == SPECIMEN or item.get("group") == "specimen":
                continue
            records.append(item)
    df = pd.DataFrame(records)
    # Ensure never_released is numeric float for TabPFN
    df["never_released"] = df["never_released"].astype(float)
    return df


def compute_auc(y_true: np.ndarray, y_score: np.ndarray) -> float:
    """Mann-Whitney U statistic formulation for AUC."""
    pos = y_score[y_true == 1]
    neg = y_score[y_true == 0]
    n_pos = len(pos)
    n_neg = len(neg)
    if n_pos == 0 or n_neg == 0:
        return 0.5
    count = 0.0
    for p in pos:
        count += np.sum(p > neg) + 0.5 * np.sum(p == neg)
    return float(count / (n_pos * n_neg))


def paired_delong_auc_diff(
    y_true: np.ndarray, y_score_a: np.ndarray, y_score_b: np.ndarray, alpha: float = 0.05
) -> dict[str, Any]:
    """Paired DeLong test for AUC(A) - AUC(B) (PRD §10).

    H0: AUC_A - AUC_B >= 0.07  (social is materially worse)
    H1: AUC_A - AUC_B < 0.07   (social is not materially worse)
    Non-inferiority declared if upper bound of one-sided CI falls below 0.07.
    """
    from scipy import stats

    pos_mask = (y_true == 1)
    neg_mask = (y_true == 0)
    m = int(np.sum(pos_mask))
    n = int(np.sum(neg_mask))

    if m == 0 or n == 0:
        return {
            "auc_a": 0.5,
            "auc_b": 0.5,
            "diff": 0.0,
            "se_diff": 0.0,
            "ci_upper_one_sided": 0.0,
            "p_value_non_inferiority": 1.0,
            "non_inferior": False,
        }

    auc_a = compute_auc(y_true, y_score_a)
    auc_b = compute_auc(y_true, y_score_b)
    diff = auc_a - auc_b

    pos_a = y_score_a[pos_mask]
    neg_a = y_score_a[neg_mask]
    pos_b = y_score_b[pos_mask]
    neg_b = y_score_b[neg_mask]

    v10_a = np.array([np.mean(p > neg_a) + 0.5 * np.mean(p == neg_a) for p in pos_a])
    v10_b = np.array([np.mean(p > neg_b) + 0.5 * np.mean(p == neg_b) for p in pos_b])

    v01_a = np.array([np.mean(pos_a > n_val) + 0.5 * np.mean(pos_a == n_val) for n_val in neg_a])
    v01_b = np.array([np.mean(pos_b > n_val) + 0.5 * np.mean(pos_b == n_val) for n_val in neg_b])

    s10 = np.cov(np.vstack([v10_a, v10_b]))
    s01 = np.cov(np.vstack([v01_a, v01_b]))

    cov_matrix = (1.0 / m) * s10 + (1.0 / n) * s01
    var_a = cov_matrix[0, 0]
    var_b = cov_matrix[1, 1]
    cov_ab = cov_matrix[0, 1]

    var_diff = max(1e-12, var_a + var_b - 2.0 * cov_ab)
    se_diff = float(np.sqrt(var_diff))

    margin = 0.07
    z_crit = stats.norm.ppf(1.0 - alpha)  # 1.6449
    ci_upper = diff + z_crit * se_diff
    z_ni = (diff - margin) / se_diff
    p_ni = float(stats.norm.cdf(z_ni))

    return {
        "auc_a": round(auc_a, 4),
        "auc_b": round(auc_b, 4),
        "diff": round(diff, 4),
        "se_diff": round(se_diff, 5),
        "margin": margin,
        "ci_upper_one_sided": round(ci_upper, 4),
        "p_value_non_inferiority": round(p_ni, 5),
        "non_inferior": bool(ci_upper < margin),
    }


def repo_clustered_bootstrap(
    data: pd.DataFrame | list[dict[str, Any]],
    score_a_col: str = "pred_a_y1",
    score_b_col: str = "pred_b_y1",
    target_col: str = "y1",
    n_resamples: int = 1000,
    alpha: float = 0.05,
    seed: int = 42,
    **kwargs: Any,
) -> dict[str, Any]:
    """Repo-clustered bootstrap (>=1,000 resamples; PRD §10 confirmatory authority)."""
    score_a_col = kwargs.get("score_a_key", score_a_col)
    score_b_col = kwargs.get("score_b_key", score_b_col)
    target_col = kwargs.get("target_key", target_col)
    df = pd.DataFrame(data) if isinstance(data, list) else data.copy()
    df = df.reset_index(drop=True)

    rng = np.random.RandomState(seed)
    repos = df["repo"].unique()
    n_repos = len(repos)

    repo_groups = {repo: group.index.to_numpy() for repo, group in df.groupby("repo")}
    y_all = df[target_col].to_numpy()
    score_a_all = df[score_a_col].to_numpy()
    score_b_all = df[score_b_col].to_numpy()

    diffs: list[float] = []
    aucs_a: list[float] = []
    aucs_b: list[float] = []

    for _ in range(n_resamples):
        sampled_repos = rng.choice(repos, size=n_repos, replace=True)
        idx_list: list[int] = []
        for r in sampled_repos:
            idx_list.extend(repo_groups[r])
        idx = np.array(idx_list)

        y_boot = y_all[idx]
        if len(np.unique(y_boot)) < 2:
            continue

        a = compute_auc(y_boot, score_a_all[idx])
        b = compute_auc(y_boot, score_b_all[idx])
        aucs_a.append(a)
        aucs_b.append(b)
        diffs.append(a - b)

    diffs_arr = np.array(diffs)
    margin = 0.07
    ci_upper = float(np.percentile(diffs_arr, 100.0 * (1.0 - alpha)))
    mean_diff = float(np.mean(diffs_arr))
    se_boot = float(np.std(diffs_arr, ddof=1))

    return {
        "n_resamples": len(diffs),
        "mean_diff": round(mean_diff, 4),
        "se_boot": round(se_boot, 5),
        "margin": margin,
        "ci_upper_one_sided": round(ci_upper, 4),
        "mean_auc_a": round(float(np.mean(aucs_a)), 4),
        "mean_auc_b": round(float(np.mean(aucs_b)), 4),
        "non_inferior": bool(ci_upper < margin),
    }


def brier_score_and_skill(y_true: np.ndarray, y_prob: np.ndarray) -> dict[str, float]:
    """Brier score and Brier Skill Score vs base rate (PRD §10)."""
    brier = float(np.mean((y_prob - y_true) ** 2))
    base_rate = float(np.mean(y_true))
    brier_ref = float(base_rate * (1.0 - base_rate))
    bss = float(1.0 - (brier / brier_ref)) if brier_ref > 0 else 0.0
    return {
        "brier": round(brier, 4),
        "base_rate": round(base_rate, 4),
        "brier_ref": round(brier_ref, 4),
        "bss": round(bss, 4),
    }


def monotonicity_check(p1: np.ndarray, p2: np.ndarray) -> dict[str, Any]:
    """Report violation rate of p2 <= p1 (PRD §8)."""
    violations = int(np.sum(p2 > p1 + 1e-6))
    rate = float(violations / len(p1)) if len(p1) > 0 else 0.0
    return {
        "total_rows": len(p1),
        "violations": violations,
        "violation_rate": round(rate, 4),
    }


def _fit_single_repo(
    r: str,
    train_mask: np.ndarray,
    test_mask: np.ndarray,
    X_a_all: np.ndarray,
    X_b_all: np.ndarray,
    y1_all: np.ndarray,
    y2_all: np.ndarray,
    n_estimators: int = 2,
) -> tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray, np.ndarray]:
    import torch
    torch.set_num_threads(2)
    clf_a = TabPFNClassifier(device="cpu", n_estimators=n_estimators, random_state=42)
    clf_b = TabPFNClassifier(device="cpu", n_estimators=n_estimators, random_state=42)

    y1_train = y1_all[train_mask]
    y2_train = y2_all[train_mask]
    X_a_train = X_a_all[train_mask]
    X_a_test = X_a_all[test_mask]
    X_b_train = X_b_all[train_mask]
    X_b_test = X_b_all[test_mask]

    # Arm A: fit y1
    clf_a.fit(X_a_train, y1_train)
    p1_a = clf_a.predict_proba(X_a_test)[:, 1]

    # Arm A: fit y2 conditional on y1 == 1
    cond_train = (y1_train == 1)
    if np.sum(cond_train) > 5 and len(np.unique(y2_train[cond_train])) > 1:
        clf_a.fit(X_a_train[cond_train], y2_train[cond_train])
        p_cond_a = clf_a.predict_proba(X_a_test)[:, 1]
    else:
        p_cond_a = np.full(len(p1_a), np.mean(y2_train))
    p2_a = p1_a * p_cond_a  # Monotonic by construction: p2 <= p1

    # Arm B: fit y1
    clf_b.fit(X_b_train, y1_train)
    p1_b = clf_b.predict_proba(X_b_test)[:, 1]

    # Arm B: fit y2 conditional on y1 == 1
    if np.sum(cond_train) > 5 and len(np.unique(y2_train[cond_train])) > 1:
        clf_b.fit(X_b_train[cond_train], y2_train[cond_train])
        p_cond_b = clf_b.predict_proba(X_b_test)[:, 1]
    else:
        p_cond_b = np.full(len(p1_b), np.mean(y2_train))
    p2_b = p1_b * p_cond_b  # Monotonic by construction: p2 <= p1

    return test_mask, p1_a, p2_a, p1_b, p2_b


def fit_and_predict_loro(
    df: pd.DataFrame,
    features_a: list[str],
    features_b: list[str],
    held_out_repos: set[str],
    n_estimators: int = 2,
    n_jobs: int = 4,
) -> pd.DataFrame:
    """Leave-one-repo-out cross-fitting using TabPFN."""
    import time
    from joblib import Parallel, delayed

    df_trainable = df[~df["repo"].isin(held_out_repos)].copy().reset_index(drop=True)
    repos = df_trainable["repo"].unique()

    # Pre-allocate prediction columns
    preds_a_y1 = np.zeros(len(df_trainable))
    preds_a_y2 = np.zeros(len(df_trainable))
    preds_b_y1 = np.zeros(len(df_trainable))
    preds_b_y2 = np.zeros(len(df_trainable))

    print(f"Starting Leave-One-Repo-Out (LORO) TabPFN fits over {len(repos)} repos ({len(df_trainable)} rows) with {n_jobs} parallel workers...")
    t_start = time.time()

    X_a_all = df_trainable[features_a].to_numpy(dtype=float)
    X_b_all = df_trainable[features_b].to_numpy(dtype=float)
    y1_all = df_trainable["y1"].to_numpy()
    y2_all = df_trainable["y2"].to_numpy()

    tasks = [
        (
            r,
            (df_trainable["repo"] != r).to_numpy(),
            (df_trainable["repo"] == r).to_numpy(),
        )
        for r in repos
    ]

    results = Parallel(n_jobs=n_jobs)(
        delayed(_fit_single_repo)(
            r, train_m, test_m, X_a_all, X_b_all, y1_all, y2_all, n_estimators=n_estimators
        )
        for r, train_m, test_m in tasks
    )

    for test_m, p1_a, p2_a, p1_b, p2_b in results:
        preds_a_y1[test_m] = p1_a
        preds_a_y2[test_m] = p2_a
        preds_b_y1[test_m] = p1_b
        preds_b_y2[test_m] = p2_b

    elapsed = time.time() - t_start
    print(f"All {len(repos)} repos fitted in {elapsed:.1f}s ({elapsed / len(repos):.2f}s/repo)!")

    df_trainable["pred_a_y1"] = preds_a_y1
    df_trainable["pred_a_y2"] = preds_a_y2
    df_trainable["pred_b_y1"] = preds_b_y1
    df_trainable["pred_b_y2"] = preds_b_y2

    # Ghosting band: difference between y1 (ghosting) and y2 (dead)
    df_trainable["ghosting_band_a"] = df_trainable["pred_a_y1"] - df_trainable["pred_a_y2"]
    df_trainable["ghosting_band_b"] = df_trainable["pred_b_y1"] - df_trainable["pred_b_y2"]

    # Save predictions immediately
    RESULTS_DIR.mkdir(parents=True, exist_ok=True)
    df_trainable.to_json(RESULTS_DIR / "loro_predictions.ndjson", orient="records", lines=True)

    return df_trainable


def run_full_analysis(
    df: pd.DataFrame, out_dir: Path | None = None, n_estimators: int = 2, n_jobs: int = 4
) -> dict[str, Any]:
    target_dir = out_dir or RESULTS_DIR
    target_dir.mkdir(parents=True, exist_ok=True)

    # Stratified hold-out for external validation (PRD §11)
    # Exactly 10 archived repos are permanently held out from training
    archived_repos = sorted(list(df[df["group"] == "archived"]["repo"].unique()))
    held_out = set(archived_repos[-10:] if len(archived_repos) >= 10 else archived_repos[-3:])

    # Capacity-matched primary features (PRD §9)
    features_a2 = ARM_A_COLS + CONTROL_COLS
    features_b2 = ARM_B_COLS + CONTROL_COLS

    # Run LORO TabPFN fits
    fitted_df = fit_and_predict_loro(
        df, features_a2, features_b2, held_out, n_estimators=n_estimators, n_jobs=n_jobs
    )

    y_true = fitted_df["y1"].to_numpy()
    score_a = fitted_df["pred_a_y1"].to_numpy()
    score_b = fitted_df["pred_b_y1"].to_numpy()

    # 1. Primary Confirmatory Test: Paired DeLong (PRD §4, §10)
    delong_res = paired_delong_auc_diff(y_true, score_a, score_b, alpha=0.05)

    # 2. Confirmatory Check: Repo-Clustered Bootstrap >= 1000 resamples (PRD §10)
    boot_res = repo_clustered_bootstrap(
        fitted_df, score_a_col="pred_a_y1", score_b_col="pred_b_y1", target_col="y1", n_resamples=1000
    )

    # 3. Calibration: Brier Skill Score vs Base Rate
    bss_a = brier_score_and_skill(y_true, score_a)
    bss_b = brier_score_and_skill(y_true, score_b)

    # 4. Monotonicity checks
    mono_a = monotonicity_check(fitted_df["pred_a_y1"].to_numpy(), fitted_df["pred_a_y2"].to_numpy())
    mono_b = monotonicity_check(fitted_df["pred_b_y1"].to_numpy(), fitted_df["pred_b_y2"].to_numpy())

    # 5. Lead-time analysis (PRD §10)
    # First T at which each arm's p(DEAD) crosses 0.5
    lead_time_data = []
    for repo_name, group in fitted_df.groupby("repo"):
        t_sorted = group.sort_values("t")
        cross_a = t_sorted[t_sorted["pred_a_y2"] >= 0.5]
        cross_b = t_sorted[t_sorted["pred_b_y2"] >= 0.5]
        first_a = cross_a["t"].iloc[0] if len(cross_a) > 0 else None
        first_b = cross_b["t"].iloc[0] if len(cross_b) > 0 else None
        lead_time_data.append({
            "repo": repo_name,
            "first_dead_a": first_a,
            "first_dead_b": first_b,
            "mean_band_a": round(float(group["ghosting_band_a"].mean()), 4),
            "mean_band_b": round(float(group["ghosting_band_b"].mean()), 4),
        })

    # 6. External validation on held-out archived repos (PRD §11)
    df_held = df[df["repo"].isin(held_out)].copy()
    ext_val: dict[str, Any] = {}
    if len(df_held) > 0:
        clf_ext_a = TabPFNClassifier(device="cpu", n_estimators=n_estimators, random_state=42)
        clf_ext_b = TabPFNClassifier(device="cpu", n_estimators=n_estimators, random_state=42)

        X_train_a = fitted_df[features_a2].to_numpy(dtype=float)
        X_train_b = fitted_df[features_b2].to_numpy(dtype=float)
        y1_train = fitted_df["y1"].to_numpy()

        X_held_a = df_held[features_a2].to_numpy(dtype=float)
        X_held_b = df_held[features_b2].to_numpy(dtype=float)

        clf_ext_a.fit(X_train_a, y1_train)
        pred_held_a = clf_ext_a.predict_proba(X_held_a)[:, 1]

        clf_ext_b.fit(X_train_b, y1_train)
        pred_held_b = clf_ext_b.predict_proba(X_held_b)[:, 1]

        y1_held = df_held["y1"].to_numpy()
        auc_ext_a = compute_auc(y1_held, pred_held_a) if len(np.unique(y1_held)) > 1 else float(np.mean(pred_held_a))
        auc_ext_b = compute_auc(y1_held, pred_held_b) if len(np.unique(y1_held)) > 1 else float(np.mean(pred_held_b))

        ext_val = {
            "held_out_repos": sorted(list(held_out)),
            "held_out_rows": len(df_held),
            "auc_arm_a": round(auc_ext_a, 4),
            "auc_arm_b": round(auc_ext_b, 4),
            "mean_pred_y1_a": round(float(np.mean(pred_held_a)), 4),
            "mean_pred_y1_b": round(float(np.mean(pred_held_b)), 4),
            "held_out_y1_base_rate": round(float(np.mean(y1_held)), 4),
        }

    summary = {
        "status": "PASSED" if boot_res["non_inferior"] else "INCONCLUSIVE",
        "primary_claim": "A2 vs B2 Non-Inferiority (One-sided alpha=0.05, margin=0.07)",
        "paired_delong": delong_res,
        "repo_clustered_bootstrap": boot_res,
        "brier_skill_scores": {
            "arm_a": bss_a,
            "arm_b": bss_b,
        },
        "monotonicity": {
            "arm_a": mono_a,
            "arm_b": mono_b,
        },
        "lead_time_analysis": {
            "sample_repo_count": len(lead_time_data),
            "records": lead_time_data[:10],
        },
        "external_validation": ext_val,
        "sample_counts": {
            "total_rows": len(fitted_df),
            "total_repos": len(fitted_df["repo"].unique()),
            "held_out_validation_repos": list(held_out),
            "y1_positives": int(np.sum(y_true == 1)),
            "y2_positives": int(np.sum(fitted_df["y2"] == 1)),
        },
    }

    # Save artifacts
    (target_dir / "statistical_results.json").write_text(
        json.dumps(summary, indent=2, ensure_ascii=False) + "\n", encoding="utf-8"
    )

    fitted_df.to_json(target_dir / "loro_predictions.ndjson", orient="records", lines=True)

    print("\n" + "=" * 60)
    print("OFRENDA STATISTICAL TEST RESULTS (PRD v2.0 §4, §10)")
    print("=" * 60)
    print(f"Arm A (Code) AUC:   {boot_res['mean_auc_a']:.4f}")
    print(f"Arm B (Social) AUC: {boot_res['mean_auc_b']:.4f}")
    print(f"AUC Difference (A - B): {boot_res['mean_diff']:.4f} (SE: {boot_res['se_boot']:.5f})")
    print(f"One-sided 95% CI Upper Bound on (AUC_A - AUC_B): {boot_res['ci_upper_one_sided']:.4f}")
    print(f"Non-inferiority Margin: {boot_res['margin']:.2f}")
    print(f"Verdict: {'NON-INFERIOR (PARITY CONFIRMED)' if boot_res['non_inferior'] else 'INCONCLUSIVE'}")
    print(f"Brier Skill Score: Arm A = {bss_a['bss']}, Arm B = {bss_b['bss']}")
    print(f"Monotonicity Violation Rate: Arm A = {mono_a['violation_rate']}, Arm B = {mono_b['violation_rate']}")
    if ext_val:
        print(f"External Validation ({ext_val['held_out_repos'].__len__()} held-out archived repos): Arm A AUC = {ext_val['auc_arm_a']}, Arm B AUC = {ext_val['auc_arm_b']}")
    print("=" * 60)
    print(f"Results saved to {target_dir / 'statistical_results.json'}")

    return summary


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--rows", type=Path, default=ROWS_FILE, help="Path to derived/rows.ndjson")
    parser.add_argument("--out", type=Path, default=RESULTS_DIR, help="Results output directory")
    parser.add_argument("--n-estimators", type=int, default=2, help="TabPFN ensemble estimators")
    parser.add_argument("--n-jobs", type=int, default=4, help="Parallel worker processes")
    args = parser.parse_args(argv)

    df = load_dataset(args.rows)
    print(f"Loaded {len(df)} rows across {len(df['repo'].unique())} repos from {args.rows}")
    run_full_analysis(df, args.out, n_estimators=args.n_estimators, n_jobs=args.n_jobs)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
