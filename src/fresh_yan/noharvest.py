"""No-harvest comparison records: ws3 carbon yield curves vs a direct libCBM run.

Compares the ws3 model (real TSA 24 landscape, carbon yield curves plugged in) with a
direct libCBM simulation of the same landscape over the model horizon, both under
no-harvest dynamics.
"""

from __future__ import annotations

import os

import pandas as pd

from .cbm import compare_ws3_libcbm, plugin_c_curves, run_cbm
from .model import (
    biomass_pools,
    build_model,
    curves_dir_for,
    disturbance_type_mapping,
    dom_pools,
    gross_growth,
    load_curves,
    model_paths,
    sum_fluxes,
    sum_pools,
    to_cbm_sit,
    total_emission,
)
from .records import with_provenance


def pct_diff(df_ws3: pd.DataFrame, df_cbm: pd.DataFrame, timestep: str = "period",
             metrics: list[str] | None = None) -> pd.DataFrame:
    """Period-wise percent difference (libCBM as benchmark)."""
    if metrics is None:
        metrics = ["biomass_stock", "dom_stock", "eco_stock", "net_emission"]
    a = df_ws3.set_index(timestep)[metrics]
    b = df_cbm.set_index(timestep)[metrics]
    diff = (a - b).div(b).mul(100)
    return diff.reset_index()


def generate(out_dir: str = "results/no_harvest", tsa: str = "tsa24",
             model_name: str | None = None, model_path: str | None = None,
             curves_dir: str | None = None, section_units: str = "years",
             harvest_acode: str = "harvest") -> None:
    """Generate the no-harvest comparison records (CSVs and figures)."""
    model_name, model_path = model_paths(tsa, model_name, model_path)
    curves_dir = curves_dir_for(tsa, curves_dir)
    fm = build_model(model_name=model_name, model_path=model_path,
                     section_units=section_units)
    mapping = disturbance_type_mapping(fm, harvest_acode=harvest_acode)
    sit_config, sit_tables = to_cbm_sit(fm, mapping)

    # libCBM: real landscape inventory, no-harvest dynamics over the model horizon
    cbm_output = run_cbm(sit_config, sit_tables, n_steps=fm.horizon * fm.period_length)

    # ws3: plug in the carbon yield curves and compile landscape carbon indicators
    c_curves_p, c_curves_f = load_curves(os.path.join(curves_dir, "c_curves_p.pkl"),
                                         os.path.join(curves_dir, "c_curves_f.pkl"))
    plugin_c_curves(fm, c_curves_p, c_curves_f, sum_pools, sum_fluxes)

    os.makedirs(out_dir, exist_ok=True)

    df_cbm, df_ws3 = compare_ws3_libcbm(
        fm, cbm_output, mapping, biomass_pools, dom_pools,
        total_emission, gross_growth, plots="whole",
        filename=os.path.join(out_dir, "no_harvest_carbon_stock_whole_st.pdf"))
    df_cbm, df_ws3 = compare_ws3_libcbm(
        fm, cbm_output, mapping, biomass_pools, dom_pools,
        total_emission, gross_growth, plots="individual",
        filename=os.path.join(out_dir, "no_harvest_carbon_dynamics_individual_st.pdf"))

    df_diff = pct_diff(df_ws3, df_cbm)
    summary = (
        df_diff.set_index("period").abs().mean()
        .to_frame("mean_abs_pct_diff")
        .rename_axis("metric")
        .reset_index()
    )

    with_provenance(df_cbm, tsa=tsa).to_csv(
        os.path.join(out_dir, "no_harvest_cbm.csv"), index=False)
    with_provenance(df_ws3, tsa=tsa).to_csv(
        os.path.join(out_dir, "no_harvest_ws3.csv"), index=False)
    with_provenance(df_diff, tsa=tsa).to_csv(
        os.path.join(out_dir, "no_harvest_pct_diff.csv"), index=False)
    with_provenance(summary, tsa=tsa).to_csv(
        os.path.join(out_dir, "no_harvest_pct_diff_summary.csv"), index=False)

    print(f"Wrote no-harvest comparison records to {out_dir}")
