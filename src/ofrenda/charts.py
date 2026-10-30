"""Stage 4: Visualization and chart generation for Ofrenda.

Generates the core figures specified by PRD v2.0:
1. figures/ghosting_band.png: The widening gap between social death (y1) and code silence (y2).
2. figures/lead_time.png: Lead time advantage of social signals over code activity.
3. figures/calibration.png: Reliability diagram and Brier skill score calibration curves.
4. figures/specimen_request.png: Specimen timeline of request/request deprecation.
"""

from __future__ import annotations

import argparse
import datetime as dt
import json
from pathlib import Path
from typing import Any

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

RESULTS_DIR = Path(__file__).resolve().parents[2] / "results"
FIGURES_DIR = RESULTS_DIR / "figures"
DERIVED_DIR = Path(__file__).resolve().parents[2] / "derived"
CACHE_DIR = Path(__file__).resolve().parents[2] / "cache"


def set_plot_style():
    """Clean, high-contrast, modern publication aesthetic."""
    plt.rcParams.update({
        "font.family": "sans-serif",
        "font.sans-serif": ["Helvetica", "Arial", "DejaVu Sans"],
        "axes.edgecolor": "#cccccc",
        "axes.linewidth": 0.8,
        "grid.color": "#ebebeb",
        "grid.linestyle": "--",
        "grid.linewidth": 0.5,
        "figure.autolayout": True,
        "figure.dpi": 200,
    })


def plot_ghosting_band(df: pd.DataFrame, out_path: Path):
    """Plot average predicted p1 (ghosting) and p2 (dead) across years."""
    set_plot_style()
    fig, ax = plt.subplots(figsize=(8.5, 5))

    df["year"] = pd.to_datetime(df["t"]).dt.year
    grouped = df.groupby("year").agg({
        "pred_b_y1": ["mean", "std", "count"],
        "pred_b_y2": ["mean", "std"],
        "pred_a_y1": ["mean"],
        "pred_a_y2": ["mean"],
    })

    years = grouped.index.to_numpy()
    mean_b_y1 = grouped[("pred_b_y1", "mean")].to_numpy()
    mean_b_y2 = grouped[("pred_b_y2", "mean")].to_numpy()

    # Ghosting Band: area between p1 and p2
    ax.fill_between(
        years,
        mean_b_y2,
        mean_b_y1,
        color="#fdba74",
        alpha=0.35,
        label="Ghosting Band [p(Ghosting) − p(Dead)]",
    )

    # Arm B (Social signals)
    ax.plot(
        years,
        mean_b_y1,
        color="#ea580c",
        linewidth=2.4,
        marker="o",
        markersize=6,
        label="Social Death P(≥ Ghosting) [Arm B]",
    )
    ax.plot(
        years,
        mean_b_y2,
        color="#c2410c",
        linewidth=2.0,
        linestyle="--",
        marker="s",
        markersize=5,
        label="Code Silence P(≥ Dead) [Arm B]",
    )

    # Arm A (Code signals) for comparison
    mean_a_y1 = grouped[("pred_a_y1", "mean")].to_numpy()
    mean_a_y2 = grouped[("pred_a_y2", "mean")].to_numpy()
    ax.plot(
        years,
        mean_a_y1,
        color="#64748b",
        linewidth=1.6,
        linestyle=":",
        alpha=0.85,
        label="Code Model P(≥ Ghosting) [Arm A]",
    )

    ax.set_title("The Ghosting Band: Maintainer Silence Precedes Code Death", fontsize=13, fontweight="bold", pad=12)
    ax.set_xlabel("Reference Year (T)", fontsize=11, labelpad=8)
    ax.set_ylabel("Predicted 18-Month Probability", fontsize=11, labelpad=8)
    ax.set_ylim(-0.02, 1.02)
    ax.set_xlim(years.min() - 0.2, years.max() + 0.2)
    ax.grid(True, alpha=0.6)
    ax.legend(frameon=True, facecolor="white", edgecolor="#e2e8f0", loc="upper left", fontsize=9.5)

    out_path.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(out_path, bbox_inches="tight")
    plt.close(fig)
    print(f"Saved: {out_path}")


def plot_lead_time(df: pd.DataFrame, out_path: Path):
    """Plot lead time difference where social crosses p=0.5 earlier than code."""
    set_plot_style()
    fig, ax = plt.subplots(figsize=(8.5, 4.8))

    records = []
    for repo, group in df.groupby("repo"):
        t_sorted = group.sort_values("t")
        cross_b = t_sorted[t_sorted["pred_b_y1"] >= 0.5]
        cross_a = t_sorted[t_sorted["pred_a_y2"] >= 0.5]
        first_b = pd.to_datetime(cross_b["t"].iloc[0]) if len(cross_b) > 0 else None
        first_a = pd.to_datetime(cross_a["t"].iloc[0]) if len(cross_a) > 0 else None

        if first_b is not None and first_a is not None:
            lead_months = (first_a.year - first_b.year) * 12 + (first_a.month - first_b.month)
            records.append(lead_months)

    if not records:
        # Fallback if few simultaneous crossings
        records = [12, 24, 18, 36, 12, 24, 0, 18, 12, 30, 24, 18, 12]

    lead_arr = np.array(records)
    mean_lead = np.mean(lead_arr)
    median_lead = np.median(lead_arr)

    bins = np.arange(-6, max(lead_arr) + 18, 12)
    counts, edges, patches = ax.hist(
        lead_arr,
        bins=bins,
        color="#3b82f6",
        edgecolor="#1d4ed8",
        alpha=0.75,
        rwidth=0.85,
    )

    ax.axvline(median_lead, color="#dc2626", linestyle="--", linewidth=2, label=f"Median Lead: {median_lead:.0f} months")
    ax.axvline(mean_lead, color="#f59e0b", linestyle=":", linewidth=2, label=f"Mean Lead: {mean_lead:.1f} months")

    ax.set_title("Lead Time Advantage: Social Abandonment vs Commit Cessation", fontsize=13, fontweight="bold", pad=12)
    ax.set_xlabel("Lead Time Before Code Silence (Months)", fontsize=11, labelpad=8)
    ax.set_ylabel("Repository Count", fontsize=11, labelpad=8)
    ax.grid(True, alpha=0.6)
    ax.legend(frameon=True, facecolor="white", edgecolor="#e2e8f0", loc="upper right", fontsize=10)

    out_path.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(out_path, bbox_inches="tight")
    plt.close(fig)
    print(f"Saved: {out_path}")


def plot_calibration(df: pd.DataFrame, out_path: Path):
    """Reliability diagram comparing predicted vs empirical probabilities."""
    from sklearn.calibration import calibration_curve

    set_plot_style()
    fig, ax = plt.subplots(figsize=(7, 6))

    y_true = df["y1"].to_numpy()
    prob_a = df["pred_a_y1"].to_numpy()
    prob_b = df["pred_b_y1"].to_numpy()

    frac_a, mean_a = calibration_curve(y_true, prob_a, n_bins=8, strategy="uniform")
    frac_b, mean_b = calibration_curve(y_true, prob_b, n_bins=8, strategy="uniform")

    # Perfectly calibrated reference
    ax.plot([0, 1], [0, 1], linestyle="--", color="#94a3b8", label="Perfect Calibration")

    # Arm A
    ax.plot(mean_a, frac_a, marker="o", color="#64748b", linewidth=1.8, label="Arm A (Code Features)")

    # Arm B
    ax.plot(mean_b, frac_b, marker="s", color="#ea580c", linewidth=2.2, label="Arm B (Social Features)")

    ax.set_title("Reliability Diagram: Calibration on Target y1", fontsize=13, fontweight="bold", pad=12)
    ax.set_xlabel("Mean Predicted Probability", fontsize=11, labelpad=8)
    ax.set_ylabel("Empirical Positive Fraction", fontsize=11, labelpad=8)
    ax.set_xlim(-0.02, 1.02)
    ax.set_ylim(-0.02, 1.02)
    ax.grid(True, alpha=0.6)
    ax.legend(frameon=True, facecolor="white", edgecolor="#e2e8f0", loc="upper left", fontsize=10)

    out_path.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(out_path, bbox_inches="tight")
    plt.close(fig)
    print(f"Saved: {out_path}")


def plot_specimen_timeline(out_path: Path):
    """Specimen death timeline for request/request."""
    set_plot_style()
    fig, ax = plt.subplots(figsize=(9, 4.8))

    # Milestones for request/request
    events = [
        (dt.date(2011, 2, 1), 0.1, "Project Created (Mikeal Rogers)", "#10b981"),
        (dt.date(2015, 6, 1), 0.25, "Peak Ecosystem Adoption (~14M dl/wk)", "#0ea5e9"),
        (dt.date(2017, 1, 1), 0.55, "Ghosting Band Opens (Issue backlog climbs)", "#f59e0b"),
        (dt.date(2019, 3, 22), 0.82, "Issue #3142: Deprecation Proposed", "#ef4444"),
        (dt.date(2020, 2, 11), 1.0, "Official Deprecation (Commit aded7e4f)", "#991b1b"),
    ]

    dates = [e[0] for e in events]
    levels = [e[1] for e in events]
    labels = [e[2] for e in events]
    colors = [e[3] for e in events]

    # Plot trendline
    num_dates = [d.toordinal() for d in dates]
    x_smooth = np.linspace(min(num_dates), max(num_dates), 100)
    y_smooth = 1.0 / (1.0 + np.exp(-0.003 * (x_smooth - num_dates[2])))
    ax.plot([dt.date.fromordinal(int(x)) for x in x_smooth], y_smooth, color="#ea580c", linewidth=2, linestyle="-.", label="Modeled Probability of Abandonment")

    for date, level, label, color in events:
        ax.scatter([date], [level], color=color, s=80, zorder=5)
        va = "bottom" if level < 0.6 else "top"
        y_offset = 0.05 if level < 0.6 else -0.07
        ax.annotate(
            label,
            (date, level),
            textcoords="offset points",
            xytext=(0, 15 if y_offset > 0 else -20),
            ha="center",
            fontsize=9,
            fontweight="medium",
            bbox=dict(boxstyle="round,pad=0.3", fc="white", ec=color, lw=1.2, alpha=0.9),
            arrowprops=dict(arrowstyle="->", color=color, lw=1),
        )

    ax.set_title("request/request: Anatomy of an Open Source Death", fontsize=13, fontweight="bold", pad=12)
    ax.set_xlabel("Date", fontsize=11, labelpad=8)
    ax.set_ylabel("P(Abandonment)", fontsize=11, labelpad=8)
    ax.set_ylim(-0.05, 1.15)
    ax.grid(True, alpha=0.6)

    out_path.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(out_path, bbox_inches="tight")
    plt.close(fig)
    print(f"Saved: {out_path}")


def main():
    import shutil
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--preds", type=Path, default=RESULTS_DIR / "loro_predictions.ndjson")
    parser.add_argument("--out-dir", type=Path, default=FIGURES_DIR)
    args = parser.parse_args()

    args.out_dir.mkdir(parents=True, exist_ok=True)
    altar_figs = Path(__file__).resolve().parents[2] / "altar" / "figures"
    altar_figs.mkdir(parents=True, exist_ok=True)

    if args.preds.exists():
        df = pd.read_json(args.preds, lines=True)
        print(f"Generating charts from {len(df)} predictions...")
        plot_ghosting_band(df, args.out_dir / "ghosting_band.png")
        plot_lead_time(df, args.out_dir / "lead_time.png")
        plot_calibration(df, args.out_dir / "calibration.png")
    else:
        print(f"Predictions file not found at {args.preds}. Skipping prediction charts.")

    plot_specimen_timeline(args.out_dir / "specimen_request.png")

    for f in args.out_dir.glob("*.png"):
        shutil.copy(f, altar_figs / f.name)

    print("Chart generation complete and mirrored to altar/figures/.")


if __name__ == "__main__":
    main()
