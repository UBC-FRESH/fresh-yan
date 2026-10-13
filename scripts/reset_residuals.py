"""Recompute the harvested-reset residuals of the campaign carbon curves.

For every development type of a femic instance, re-simulate the rotation cycle
(five rotations at ``--rotation-age`` years) and report:

- ``documented_residual``: eco(age 0) - (eco(119) - merch(119)) - the cycle-drift
  metric used by ``tests/test_curves.py`` (age-0 of the extracted cycle vs the
  pre-cut state of the next rotation);
- ``direct_residual``: post-cut eco - (pre-cut eco - pre-cut merch) at the final cut;
- ``harvested_area_ha``: the dtype's harvested area over the horizon under the base
  scenario, and ``phantom_c`` = direct residual x harvested area (their sum per unit
  is the unit's net phantom-carbon bound).

Each run writes ``<out-dir>/reset_residuals_tsa<code>.csv`` with provenance; merging
the per-unit files gives the five-unit record.

Usage:
    python scripts/reset_residuals.py --tsa 24 [--out-dir results/cross-tsa]
"""

from __future__ import annotations

import argparse
import os

import pandas as pd

from fresh_yan.base_scenario import solve as base_solve
from fresh_yan.curves import (
    _clearcut_event,
    _regeneration_sources,
    _run_stand,
    _single_stand_inventory,
    _summarize,
)
from fresh_yan.model import build_model, disturbance_type_mapping, to_cbm_sit
from fresh_yan.records import with_provenance

ROTATION_AGE = 120
N_ROT = 5
N_STEPS = 700


def _merch(row) -> float:
    return float(row["SoftwoodMerch"] + row["HardwoodMerch"])


def main(tsa: str, out_dir: str, instances_root: str) -> None:
    model_path = os.path.join(instances_root, f"femic-tsa{tsa}-instance/output/ws3")
    fm = build_model(model_name=f"tsa{tsa}", model_path=model_path, section_units="periods")
    fm.actions["cc"].is_harvest = True
    eco0 = float(fm.inventory(0, "ecosystem"))
    mapping = disturbance_type_mapping(fm, harvest_acode="cc")
    sit_config, sit_tables = to_cbm_sit(fm, mapping)

    # Base-scenario harvested area per development type (200-year horizon).
    base_solve(fm, solver="highs", harvest_acode="cc")
    area_by_dtype: dict[tuple, float] = {}
    for dtk, _age, area, acode, *_ in fm.compile_schedule():
        if acode == "cc":
            area_by_dtype[dtk] = area_by_dtype.get(dtk, 0.0) + float(area)

    sources = _regeneration_sources(fm, "cc")
    cut = ROTATION_AGE * N_ROT
    rows = []
    for key in fm.dtypes:
        parent = sources.get(key, key)
        inv = _single_stand_inventory(sit_tables, parent, historic_disturbance="fire")
        inv_managed = inv.copy()
        inv_managed.iloc[0, inv_managed.columns.get_loc("theme4")] = key[4]
        events = sit_tables["sit_events"]
        for i in range(1, N_ROT + 1):
            src = inv if i == 1 else inv_managed
            events = _clearcut_event(events, src, ROTATION_AGE * i, harvest_acode="cc")
        out = _run_stand(sit_config, sit_tables, inv, events, cut + N_STEPS)
        pi, _ = _summarize(out)
        post, pre = pi.loc[cut], pi.loc[cut - 1]
        next_pre = pi.loc[cut + ROTATION_AGE - 1]
        direct = float(post["ecosystem"] - (pre["ecosystem"] - _merch(pre)))
        documented = float(pi.loc[cut]["ecosystem"]
                           - (next_pre["ecosystem"] - _merch(next_pre)))
        area = area_by_dtype.get(key, 0.0)
        rows.append({
            "tsa": f"tsa{tsa}",
            "dtype": " ".join(key),
            "documented_residual_tc_ha": documented,
            "direct_residual_tc_ha": direct,
            "harvested_area_ha": area,
            "phantom_c_tc": direct * area,
        })
        print(f"  {key}: direct {direct:+.2f} | documented {documented:+.2f}", flush=True)

    df = pd.DataFrame(rows)
    phantom = float(df["phantom_c_tc"].sum())
    print(f"tsa{tsa}: max |direct| {df['direct_residual_tc_ha'].abs().max():.2f} tC/ha | "
          f"net phantom {phantom:,.0f} tC "
          f"({phantom / eco0 * 100:.3f}% of initial ecosystem carbon)", flush=True)
    os.makedirs(out_dir, exist_ok=True)
    with_provenance(df, tsa=f"tsa{tsa}").to_csv(
        os.path.join(out_dir, f"reset_residuals_tsa{tsa}.csv"), index=False)
    print(f"Wrote {out_dir}/reset_residuals_tsa{tsa}.csv", flush=True)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--tsa", required=True)
    parser.add_argument("--out-dir", default="results/cross-tsa")
    parser.add_argument("--instances-root",
                        default="/srv/shared-data/gep/jupyterhub02-projects/femic/external")
    args = parser.parse_args()
    main(args.tsa, args.out_dir, args.instances_root)
