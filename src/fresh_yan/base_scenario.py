"""Base scenario records: maximize even-flow harvest volume over the horizon."""

from __future__ import annotations

import os
import time

import ws3.opt

from .cbm import plugin_c_curves
from .model import build_model, curves_dir_for, load_curves, model_paths, sum_fluxes, sum_pools
from .records import with_provenance
from .scenario import compile_scenario, gen_scenario, plot_scenario


def solve(fm, solver: str = "highs"):
    """Build and solve the base scenario (max even-flow harvest volume).

    Even-flow constraints limit period-over-period variation of harvested area and
    harvested volume to 5%. Returns ``(df, problem, solve_seconds)``.
    """
    cflw_ha = (dict.fromkeys(fm.periods, 0.05), 1)
    cflw_hv = (dict.fromkeys(fm.periods, 0.05), 1)
    problem = gen_scenario(fm=fm, name="base", cflw_ha=cflw_ha, cflw_hv=cflw_hv,
                           cgen_ha={}, cgen_hv={}, cgen_gs={})
    problem.solver(solver)
    fm.reset()
    start = time.time()
    problem.solve()
    elapsed = time.time() - start
    if problem.status() != ws3.opt.STATUS_OPTIMAL:
        raise RuntimeError(f"base scenario not optimal (status={problem.status()})")
    schedule = fm.compile_schedule(problem)
    fm.apply_schedule(schedule, force_integral_area=False, override_operability=False,
                      fuzzy_age=False, recourse_enabled=False, verbose=False,
                      compile_c_ycomps=True)
    return compile_scenario(fm), problem, elapsed


def generate(out_dir: str = "results/base_scenario", solver: str = "highs",
             tsa: str = "tsa24", model_name: str | None = None,
             model_path: str | None = None, curves_dir: str | None = None,
             section_units: str = "years", harvest_acode: str = "harvest") -> None:
    """Generate the base scenario records (CSV + four-panel figure)."""
    model_name, model_path = model_paths(tsa, model_name, model_path)
    curves_dir = curves_dir_for(tsa, curves_dir)
    fm = build_model(model_name=model_name, model_path=model_path,
                     section_units=section_units)
    fm.actions[harvest_acode].is_harvest = True  # required for cmp_c_z (notebook cell 40)
    # Plug in the carbon yield curves so the record's carbon columns are populated.
    c_curves_p, c_curves_f = load_curves(os.path.join(curves_dir, "c_curves_p.pkl"),
                                         os.path.join(curves_dir, "c_curves_f.pkl"))
    plugin_c_curves(fm, c_curves_p, c_curves_f, sum_pools, sum_fluxes)
    df, _problem, elapsed = solve(fm, solver=solver)
    os.makedirs(out_dir, exist_ok=True)
    fig, _axes = plot_scenario(df)
    fig.savefig(os.path.join(out_dir, "base_scenario.pdf"), bbox_inches="tight")
    with_provenance(df, solver=solver, tsa=tsa).to_csv(
        os.path.join(out_dir, "base_scenario.csv"), index=False)
    print(f"Wrote base scenario records to {out_dir} (solver={solver}, solve {elapsed:.1f}s)")
