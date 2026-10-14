"""Harvested-landscape replay validation: ws3 carbon curves vs a direct libCBM run.

Replays the base-scenario harvest schedule in libCBM as cohort-exact disturbance
events and compares per-period stocks against the estate model's own curve-based
carbon accounting (the same comparison layout as the no-harvest validation).

Conventions (see ``planning/ws3-libcbm-replay-findings.md``):
- one event per scheduled cut ``(dtype, age, area, period)``;
- event year ``10 * (period - 1) + 1`` and age window ``min = max = age`` (the
  schedule's own cut age; first-rotation and managed cohorts share this rule);
- ``sit_transitions`` is emptied in the replay input (otherwise libCBM fires
  spontaneous off-schedule harvests from the model's transition table);
- per-period stocks are compared, not disturbance merch (ws3 uses the cycle curve for
  initial stands while libCBM carries the spun-up stand states - a documented
  initial-stand convention, not a replay defect).

Usage:
    python scripts/replay_validation.py --tsa 24 [--out-dir results/femic-tsa24/replay]
"""

from __future__ import annotations

import argparse
import os

import pandas as pd

from fresh_yan.base_scenario import solve as base_solve
from fresh_yan.cbm import plugin_c_curves, run_cbm
from fresh_yan.curves import _single_stand_inventory
from fresh_yan.model import (
    biomass_pools,
    build_model,
    disturbance_type_mapping,
    dom_pools,
    gross_growth,
    load_curves,
    sum_fluxes,
    sum_pools,
    to_cbm_sit,
    total_emission,
)
from fresh_yan.noharvest import compare_ws3_libcbm, pct_diff
from fresh_yan.records import with_provenance


def _event_rows(base_events: pd.DataFrame, sit_tables: dict, sched: list) -> pd.DataFrame:
    rows = []
    for dtk, a, area, p in sched:
        r = _single_stand_inventory(sit_tables, dtk).iloc[0]
        row = {c: r[c] for c in base_events.columns if c.startswith("theme")}
        row.update({"species": r["species"], "using_age_class": "FALSE",
                    "min_softwood_age": a, "max_softwood_age": a,
                    "min_hardwood_age": a, "max_hardwood_age": a})
        mid = base_events.columns[
            base_events.columns.get_loc("MinYearsSinceDist"):
            base_events.columns.get_loc("efficiency")]
        for c in mid:
            row[c] = -1
        row.update({"efficiency": 1, "sort_type": 3, "target_type": "A", "target": area,
                    "disturbance_type": "cc", "disturbance_year": 10 * (p - 1) + 1})
        rows.append(row)
    return pd.DataFrame(rows)[base_events.columns]


def main(tsa: str, out_dir: str, instances_root: str) -> None:
    model_path = os.path.join(instances_root, f"femic-tsa{tsa}-instance/output/ws3")
    fm = build_model(model_name=f"tsa{tsa}", model_path=model_path, section_units="periods")
    c_p, c_f = load_curves(os.path.join("curves", f"femic-tsa{tsa}", "c_curves_p.pkl"),
                           os.path.join("curves", f"femic-tsa{tsa}", "c_curves_f.pkl"))
    plugin_c_curves(fm, c_p, c_f, sum_pools, sum_fluxes)
    fm.actions["cc"].is_harvest = True
    base_solve(fm, solver="highs", harvest_acode="cc")  # applies the schedule to fm
    sched = [(dtk, a, area, p)
             for dtk, a, area, acode, p, *_ in fm.compile_schedule() if acode == "cc"]
    print(f"tsa{tsa}: {len(sched)} scheduled cuts, {sum(r[2] for r in sched):,.0f} ha",
          flush=True)

    mapping = disturbance_type_mapping(fm, harvest_acode="cc")
    sit_config, sit_tables = to_cbm_sit(fm, mapping)
    base_events = sit_tables["sit_events"]
    tables = dict(sit_tables)
    tables["sit_events"] = pd.concat(
        [base_events, _event_rows(base_events, sit_tables, sched)], ignore_index=True)
    tables["sit_transitions"] = sit_tables["sit_transitions"].iloc[0:0]
    cbm_output = run_cbm(sit_config, tables, n_steps=fm.horizon * fm.period_length)

    os.makedirs(out_dir, exist_ok=True)
    df_cbm, df_ws3 = compare_ws3_libcbm(
        fm, cbm_output, mapping, biomass_pools, dom_pools, total_emission, gross_growth,
        plots="whole", filename=os.path.join(out_dir, "replay_carbon_stock_whole_st.pdf"))
    df_cbm, df_ws3 = compare_ws3_libcbm(
        fm, cbm_output, mapping, biomass_pools, dom_pools, total_emission, gross_growth,
        plots="individual",
        filename=os.path.join(out_dir, "replay_carbon_dynamics_individual_st.pdf"))
    df_diff = pct_diff(df_ws3, df_cbm)
    summary = (df_diff.set_index("period").abs().mean().to_frame("mean_abs_pct_diff")
               .rename_axis("metric").reset_index())

    with_provenance(df_cbm, tsa=f"tsa{tsa}").to_csv(
        os.path.join(out_dir, "replay_cbm.csv"), index=False)
    with_provenance(df_ws3, tsa=f"tsa{tsa}").to_csv(
        os.path.join(out_dir, "replay_ws3.csv"), index=False)
    with_provenance(df_diff, tsa=f"tsa{tsa}").to_csv(
        os.path.join(out_dir, "replay_pct_diff.csv"), index=False)
    with_provenance(summary, tsa=f"tsa{tsa}").to_csv(
        os.path.join(out_dir, "replay_pct_diff_summary.csv"), index=False)
    print(f"tsa{tsa}: mean abs diff " + " | ".join(
        f"{r.metric}={r.mean_abs_pct_diff:.2f}%" for r in summary.itertuples()), flush=True)
    print(f"Wrote replay validation records to {out_dir}", flush=True)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--tsa", required=True)
    parser.add_argument("--out-dir", default="")
    parser.add_argument("--instances-root",
                        default="/srv/shared-data/gep/jupyterhub02-projects/femic/external")
    args = parser.parse_args()
    out = args.out_dir or f"results/femic-tsa{args.tsa}/replay"
    main(args.tsa, out, args.instances_root)
