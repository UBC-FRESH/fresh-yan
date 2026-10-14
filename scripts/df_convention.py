"""Displacement-factor convention mapping: the effective-credit axis.

The model applies each displacement factor to the solid-wood inflow, which is the
utilized merchantable carbon: 0.85 utilization rate times the 50/50 paper--solid
allocation = 0.425 of merchantable carbon. One unit of displacement factor
(tC per tC of solid-wood product carbon) therefore provides 0.425 tC of effective
credit per tC of harvested merchantable carbon - the basis on which some
published factors are expressed. This script maps the per-unit flip thresholds
(10th/50th/90th response percentiles at a 100-year half-life) onto both bases.

Record: ``cross-tsa/df_convention_mapping.csv``.
"""

from __future__ import annotations

import argparse
import os

import pandas as pd

from fresh_yan.records import with_provenance

UTIL_RATE = 0.85
SOLID_SHARE = 0.5
FACTOR = UTIL_RATE * SOLID_SHARE  # 0.425 tC credit per tC of merch carbon


def main(out_dir: str = "results/cross-tsa", results_root: str = "results",
         half_life: int = 100) -> None:
    thr = pd.read_csv(
        os.path.join(results_root, "cross-tsa", "cross_tsa_thresholds.csv"))
    t = thr[thr.half_life == half_life].copy()
    t["unit"] = t["label"].str.replace("femic-", "", regex=False)
    out = pd.DataFrame({
        "unit": t["unit"],
        "half_life": t["half_life"],
        "df10_product_carbon": t["df10"],
        "df50_product_carbon": t["df50"],
        "df90_product_carbon": t["df90"],
        "credit10_merch_carbon": t["df10"] * FACTOR,
        "credit50_merch_carbon": t["df50"] * FACTOR,
        "credit90_merch_carbon": t["df90"] * FACTOR,
        "utilization_rate": UTIL_RATE,
        "solid_share": SOLID_SHARE,
        "effective_credit_factor": FACTOR,
    })
    os.makedirs(out_dir, exist_ok=True)
    out_path = os.path.join(out_dir, "df_convention_mapping.csv")
    with_provenance(out).to_csv(out_path, index=False)
    print(f"Wrote {out_path} ({len(out)} rows)", flush=True)
    print(out.round(3).to_string(index=False), flush=True)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out-dir", default="results/cross-tsa")
    parser.add_argument("--results-root", default="results")
    parser.add_argument("--half-life", type=int, default=100)
    args = parser.parse_args()
    main(args.out_dir, args.results_root, args.half_life)
