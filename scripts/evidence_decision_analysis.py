"""Evidence -> decision analysis: what the published HWP parameter ranges imply.

Reads the per-unit emission-minimizing grids (5,000 cells each) and the base
scenarios, and summarizes the decision consequence of the displacement-factor
ranges reported in the literature: for each unit and each published range, the
minimum / median / maximum optimal harvested volume as a fraction of the
volume-maximizing base scenario, over the full tested half-life span (1-200 yr).

Records: ``cross-tsa/decision_under_evidence.csv``.
"""

from __future__ import annotations

import argparse
import os

import pandas as pd

from fresh_yan.records import with_provenance

CASES = [
    ("Leskinen et al. 2018 (all categories, 95% range)", -0.7, 5.1),
    ("Sathre and O'Connor 2010 (middle estimates)", 0.4, 6.0),
    ("Smyth et al. 2017 (general end-use basket)", 0.45, 0.54),
    ("Smyth et al. 2017 (building-only high case)", 2.1, 2.2),
    ("Smyth et al. 2020 (low/high cases)", 0.45, 2.2),
]
UNITS = ["femic-tsa08", "femic-tsa16", "femic-tsa24", "femic-tsa40", "femic-tsa41"]
DF_MIN, DF_MAX = 0.0, 2.4  # tested displacement-factor axis


def main(out_dir: str = "results/cross-tsa", results_root: str = "results") -> None:
    rows = []
    for unit in UNITS:
        grid = pd.read_csv(
            os.path.join(results_root, unit, "tradeoff_grid",
                         "tradeoff_grid_summary.csv"))
        base = pd.read_csv(
            os.path.join(results_root, unit, "base_scenario", "base_scenario.csv"))
        base_total = float(base["ohv"].sum())
        grid = grid.copy()
        grid["frac_base"] = grid["total_harvested_volume_m3"] / base_total
        for case, lo, hi in CASES:
            lo_c = max(lo, DF_MIN)
            hi_c = min(hi, DF_MAX)
            sub = grid[(grid["displacement_factor"] >= lo_c - 1e-9)
                       & (grid["displacement_factor"] <= hi_c + 1e-9)]
            assert len(sub) > 0, f"empty case {case} for {unit}"
            rows.append({
                "unit": unit,
                "case": case,
                "df_low_reported": lo,
                "df_high_reported": hi,
                "df_low_tested": lo_c,
                "df_high_tested": hi_c,
                "n_cells": len(sub),
                "vol_min_frac_base": float(sub["frac_base"].min()),
                "vol_median_frac_base": float(sub["frac_base"].median()),
                "vol_max_frac_base": float(sub["frac_base"].max()),
            })
        print(f"{unit}: base total {base_total:.3g} m3, grids aggregated", flush=True)

    df = pd.DataFrame(rows)
    os.makedirs(out_dir, exist_ok=True)
    out = os.path.join(out_dir, "decision_under_evidence.csv")
    with_provenance(df).to_csv(out, index=False)
    print(f"Wrote {out} ({len(df)} rows)", flush=True)
    print(df.to_string(index=False), flush=True)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out-dir", default="results/cross-tsa")
    parser.add_argument("--results-root", default="results")
    main(**vars(parser.parse_args()))
