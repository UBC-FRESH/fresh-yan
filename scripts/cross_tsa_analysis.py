"""Cross-TSA characterization of the five-TSA harvest-flip grids (issue #3).

For each management unit: normalize the emission-minimizing harvest volume of every
trade-off-grid scenario by the unit's base-scenario (max even-flow) volume, then
extract, per half-life, the displacement-factor thresholds where the optimal harvest
crosses 10/50/90% of that half-life's observed response range (flip location and
steep-band width) plus the response at reference cells.

Works on any ``<results-root>/<label>/{tradeoff_grid,base_scenario}`` pair.  The
femic campaign labels are ``femic-tsa08`` ... ``femic-tsa41``; the legacy TSA 24
records live under ``results/tradeoff_grid`` + ``results/base_scenario`` (point
``--results-root`` at a directory that mirrors the label layout to compare them).

Run from the repository root:
    python scripts/cross_tsa_analysis.py --labels femic-tsa08 femic-tsa16 femic-tsa24 \
        femic-tsa40 femic-tsa41 --out-dir results/cross-tsa
"""

from __future__ import annotations

import argparse
import os

import matplotlib
import numpy as np
import pandas as pd

matplotlib.use("Agg")
import matplotlib.pyplot as plt

REF_HL = [2, 10, 35, 100, 200]
REF_DF = [0.0, 0.5, 1.0, 1.5, 2.0, 2.4]


def _load(label: str, results_root: str) -> tuple[pd.DataFrame, float]:
    grid = pd.read_csv(os.path.join(results_root, label, "tradeoff_grid",
                                    "tradeoff_grid_summary.csv"))
    base = pd.read_csv(os.path.join(results_root, label, "base_scenario",
                                    "base_scenario.csv"))
    return grid, float(base["ohv"].sum())


def _cross(dfs: np.ndarray, r: np.ndarray, level: float) -> float:
    """First displacement factor where ``r`` reaches ``level`` (linear interpolation)."""
    idx = np.where(r >= level)[0]
    if len(idx) == 0:
        return float("nan")
    i = int(idx[0])
    if i == 0:
        return float(dfs[0])
    x0, x1 = float(dfs[i - 1]), float(dfs[i])
    y0, y1 = float(r[i - 1]), float(r[i])
    if y1 <= y0:
        return x1
    return x0 + (level - y0) * (x1 - x0) / (y1 - y0)


def thresholds_for(grid: pd.DataFrame, base_total: float) -> pd.DataFrame:
    """Per half-life flip location and steep band (fractions of the observed range)."""
    rows = []
    for hl, sub in grid.groupby("half_life"):
        sub = sub.sort_values("displacement_factor")
        dfs = sub["displacement_factor"].to_numpy()
        r = sub["total_harvested_volume_m3"].to_numpy() / base_total
        r_min, r_max = float(r.min()), float(r.max())
        r_rel = (r - r_min) / (r_max - r_min) if r_max > r_min else np.zeros_like(r)
        rows.append({
            "half_life": int(hl),
            "df10": _cross(dfs, r_rel, 0.1),
            "df50": _cross(dfs, r_rel, 0.5),
            "df90": _cross(dfs, r_rel, 0.9),
            "r_min_frac_base": r_min,
            "r_max_frac_base": r_max,
        })
    return pd.DataFrame(rows)


def reference_cells(grid: pd.DataFrame, base_total: float) -> pd.DataFrame:
    sub = grid[grid["half_life"].isin(REF_HL) & grid["displacement_factor"].isin(REF_DF)]
    out = sub[["half_life", "displacement_factor", "total_harvested_volume_m3",
               "total_net_system_emission_tco2"]].copy()
    out["harvest_frac_base"] = out["total_harvested_volume_m3"] / base_total
    return out.sort_values(["half_life", "displacement_factor"]).reset_index(drop=True)


def main(labels: list[str], results_root: str, out_dir: str) -> None:
    os.makedirs(out_dir, exist_ok=True)
    all_thr, all_ref, all_max = [], [], []
    thresholds = {}
    for label in labels:
        grid, base_total = _load(label, results_root)
        thr = thresholds_for(grid, base_total)
        thresholds[label] = thr
        thr.insert(0, "label", label)
        all_thr.append(thr)
        ref = reference_cells(grid, base_total)
        ref.insert(0, "label", label)
        all_ref.append(ref)
        all_max.append({"label": label, "base_total_m3": base_total,
                        "grid_max_m3": float(grid["total_harvested_volume_m3"].max()),
                        "grid_max_frac_base": float(
                            grid["total_harvested_volume_m3"].max() / base_total)})
        print(f"{label}: base={base_total / 1e9:.3f}e9 m3 | "
              f"grid max frac base={all_max[-1]['grid_max_frac_base']:.3f} | "
              f"df50(hl=100)={thr.loc[thr.half_life == 100, 'df50'].iloc[0]:.2f}")

    pd.concat(all_thr, ignore_index=True).to_csv(
        os.path.join(out_dir, "cross_tsa_thresholds.csv"), index=False)
    pd.concat(all_ref, ignore_index=True).to_csv(
        os.path.join(out_dir, "cross_tsa_reference_cells.csv"), index=False)
    pd.DataFrame(all_max).to_csv(
        os.path.join(out_dir, "cross_tsa_grid_maxima.csv"), index=False)

    fig, ax = plt.subplots(figsize=(7.5, 4.5))
    for label in labels:
        thr = thresholds[label]
        ax.plot(thr["half_life"], thr["df50"], label=label, lw=1.6)
        ax.fill_between(thr["half_life"], thr["df10"], thr["df90"], alpha=0.12)
    ax.set_xlabel("HWP half-life (yr)")
    ax.set_ylabel("Displacement factor (flip location, df50)")
    ax.set_ylim(0.0, 2.4)
    ax.legend(fontsize=8)
    ax.set_title("Harvest-flip displacement threshold by half-life (band: df10-df90)")
    fig.savefig(os.path.join(out_dir, "cross_tsa_thresholds.pdf"), bbox_inches="tight")
    print(f"Wrote cross-TSA tables and figure to {out_dir}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--labels", nargs="+", required=True,
                        help="Result labels (directories under --results-root).")
    parser.add_argument("--results-root", default="results")
    parser.add_argument("--out-dir", default="results/cross-tsa")
    args = parser.parse_args()
    main(args.labels, args.results_root, args.out_dir)
