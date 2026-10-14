"""Stand-level harvested-cycle validation: curve layer vs direct libCBM.

For every regeneration target (managed dtype) of a unit, the stand's carbon
trajectory is simulated directly in libCBM through three clearcut rotations
(reference, the same single-stand machinery that generates the curves). The same
trajectory is then assembled from the registered carbon yield curves exactly as
the optimizer evaluates them (one curve per dtype, reset to age 0 at harvest).
The per-rotation stock differences quantify the harvested-pathway approximation
at the stand level: the first post-harvest rotation carries the documented
first-rotation/cycle-convention residual; later rotations converge onto the
cycle curve.

Records: ``stand_validation/stand_cycle_diffs.csv`` (per dtype x rotation x
metric: mean/max absolute percent difference relative to the reference run).
"""

from __future__ import annotations

import argparse
import os

import pandas as pd

from fresh_yan.curves import (
    _clearcut_event,
    _regeneration_sources,
    _run_stand,
    _single_stand_inventory,
    _summarize,
)
from fresh_yan.model import (
    build_model,
    curves_dir_for,
    disturbance_type_mapping,
    load_curves,
    model_paths,
    to_cbm_sit,
)
from fresh_yan.records import with_provenance

ROTATION_AGE = 120
N_CUTS = 3
METRICS = ["ecosystem", "biomass", "DOM"]


def main(out_dir: str, tsa: str = "tsa24", model_name: str | None = None,
         model_path: str | None = None, curves_dir: str | None = None,
         section_units: str = "years", harvest_acode: str = "harvest") -> None:
    model_name, model_path = model_paths(tsa, model_name, model_path)
    curves_dir = curves_dir_for(tsa, curves_dir)
    fm = build_model(model_name=model_name, model_path=model_path,
                     section_units=section_units)
    mapping = disturbance_type_mapping(fm, harvest_acode=harvest_acode)
    sit_config, sit_tables = to_cbm_sit(fm, mapping)
    empty_events = sit_tables["sit_events"]
    c_curves_p, _c_curves_f = load_curves(
        os.path.join(curves_dir, "c_curves_p.pkl"),
        os.path.join(curves_dir, "c_curves_f.pkl"))

    sources = _regeneration_sources(fm, harvest_acode)
    print(f"{len(sources)} regeneration targets (managed dtypes)", flush=True)

    rows = []
    for key in sources:
        label = " ".join(key)
        parent = sources[key]
        inv = _single_stand_inventory(sit_tables, parent, age=1,
                                      historic_disturbance="fire")
        inv_managed = inv.copy()
        inv_managed.iloc[0, inv_managed.columns.get_loc("theme4")] = key[4]
        events = empty_events
        for i in range(1, N_CUTS + 1):
            src = inv if i == 1 else inv_managed
            events = _clearcut_event(events, src, ROTATION_AGE * i,
                                     harvest_acode=harvest_acode)
        total_steps = ROTATION_AGE * N_CUTS + ROTATION_AGE
        out = _run_stand(sit_config, sit_tables, inv, events, total_steps)
        pi, _fi = _summarize(out)
        curve = c_curves_p.loc[label]

        for rotation in range(0, N_CUTS + 1):
            if rotation == 0:
                seg = pi.loc[1:ROTATION_AGE - 1]
                ages = seg.index
            else:
                cut = ROTATION_AGE * rotation
                seg = pi.loc[cut:cut + ROTATION_AGE - 1]
                ages = seg.index - cut
            ref = seg[METRICS]
            cv = curve.loc[ages, METRICS]
            cv = cv.set_axis(ref.index)
            diff = (cv - ref).div(ref).mul(100)
            for metric in METRICS:
                rows.append({
                    "dtype_key": label,
                    "rotation": rotation,
                    "metric": metric,
                    "mean_pct_diff": float(diff[metric].mean()),
                    "mean_abs_pct_diff": float(diff[metric].abs().mean()),
                    "max_abs_pct_diff": float(diff[metric].abs().max()),
                })
        print(f"  {label}: rotations done", flush=True)

    df = pd.DataFrame(rows)
    os.makedirs(out_dir, exist_ok=True)
    with_provenance(df, tsa=tsa).to_csv(
        os.path.join(out_dir, "stand_cycle_diffs.csv"), index=False)
    agg = (
        df.groupby(["rotation", "metric"])["mean_abs_pct_diff"]
        .agg(["median", "mean", "max"]).reset_index()
    )
    with_provenance(agg, tsa=tsa).to_csv(
        os.path.join(out_dir, "stand_cycle_summary.csv"), index=False)
    print(f"Wrote {out_dir}/stand_cycle_diffs.csv ({len(df)} rows)", flush=True)
    print(agg.to_string(index=False), flush=True)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out-dir", default="results/stand_validation")
    parser.add_argument("--tsa", default="tsa24")
    parser.add_argument("--model-name", default=None)
    parser.add_argument("--model-path", default=None)
    parser.add_argument("--curves-dir", default=None)
    parser.add_argument("--section-units", default="years",
                        choices=["years", "periods"])
    parser.add_argument("--harvest-acode", default="harvest")
    main(**vars(parser.parse_args()))
