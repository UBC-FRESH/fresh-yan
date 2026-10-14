"""Cross-unit threshold attributes: what orders the flip mid-point across units?

The manuscript reports that the emission-minimizing flip's location is a property
of the landscape as much as of the parameters. This script assembles per-unit
attributes (size, initial carbon, carbon density, productivity proxy, age
structure from the model instances' ``.are`` files) and computes rank (Spearman)
associations between each attribute and the displacement-factor mid-point
threshold, at a 100-year half-life and as the median across half-lives.

Records:
- ``threshold_attributes.csv`` (per unit: attributes + thresholds)
- ``threshold_attribute_correlations.csv`` (Spearman associations vs df50)

Usage:
    python scripts/threshold_attributes.py --instances-root <femic/external> \
        --out-dir results/cross-tsa
"""

from __future__ import annotations

import argparse
import os

import pandas as pd
from five_tsa_figures import read_are
from scipy.stats import spearmanr

from fresh_yan.records import with_provenance

UNITS = ["08", "16", "24", "40", "41"]
ATTRS = [
    "thlb_Mha", "dev_types", "eco_MtC", "eco_density_tC_ha", "base_vol_per_ha",
    "young_lt50_pct", "old_ge105_pct", "mean_age",
]


def main(instances_root: str, out_dir: str = "results/cross-tsa",
         results_root: str = "results") -> None:
    attrs = pd.read_csv(
        os.path.join(results_root, "cross-tsa", "five_tsa_attributes.csv"),
        index_col=0)
    thr = pd.read_csv(
        os.path.join(results_root, "cross-tsa", "cross_tsa_thresholds.csv"))

    rows = []
    for code in UNITS:
        are_path = os.path.join(
            instances_root, f"femic-tsa{code}-instance", "output", "ws3",
            f"tsa{code}.are")
        df = read_are(are_path)
        total = float(df["area"].sum())
        mid = df["age"] * 10 + 5
        label = f"femic-tsa{code}"
        t = thr[thr.label == label]
        base = pd.read_csv(
            os.path.join(results_root, label, "base_scenario", "base_scenario.csv"))
        base_vol = float(base["ohv"].sum())
        a = attrs.loc[f"tsa{code}"]
        rows.append({
            "unit": f"tsa{code}",
            "thlb_Mha": a["thlb_ha"] / 1e6,
            "dev_types": a["dev_types"],
            "eco_MtC": a["initial_eco_mtc"],
            "eco_density_tC_ha": a["initial_eco_mtc"] * 1e6 / a["thlb_ha"],
            "base_vol_per_ha": base_vol / a["thlb_ha"],
            "young_lt50_pct": float(df.loc[mid <= 45, "area"].sum()) / total * 100,
            "old_ge105_pct": float(df.loc[mid >= 105, "area"].sum()) / total * 100,
            "mean_age": float((df["area"] * mid).sum()) / total,
            "df50_hl100": float(t[t.half_life == 100]["df50"].iloc[0]),
            "df50_median_hl50_200": float(t[t.half_life >= 50]["df50"].median()),
        })
    per_unit = pd.DataFrame(rows)

    corr_rows = []
    for attr in ATTRS:
        rho100, p100 = spearmanr(per_unit[attr], per_unit["df50_hl100"])
        rho_med, p_med = spearmanr(per_unit[attr], per_unit["df50_median_hl50_200"])
        corr_rows.append({
            "attribute": attr,
            "rho_vs_df50_hl100": float(rho100),
            "p_vs_df50_hl100": float(p100),
            "rho_vs_df50_median_hl50_200": float(rho_med),
            "p_vs_df50_median_hl50_200": float(p_med),
        })
    corr = pd.DataFrame(corr_rows)

    os.makedirs(out_dir, exist_ok=True)
    with_provenance(per_unit).to_csv(
        os.path.join(out_dir, "threshold_attributes.csv"), index=False)
    with_provenance(corr).to_csv(
        os.path.join(out_dir, "threshold_attribute_correlations.csv"), index=False)
    print(f"Wrote {out_dir}/threshold_attributes.csv ({len(per_unit)} rows) and "
          f"threshold_attribute_correlations.csv ({len(corr)} rows)", flush=True)
    print(per_unit.round(3).to_string(index=False))
    print(corr.round(3).to_string(index=False))


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--instances-root", required=True)
    parser.add_argument("--out-dir", default="results/cross-tsa")
    parser.add_argument("--results-root", default="results")
    args = parser.parse_args()
    main(args.instances_root, args.out_dir, args.results_root)
