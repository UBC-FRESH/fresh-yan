"""Base scenario records: maximize even-flow harvest volume over the horizon."""

from __future__ import annotations

import os
import time

import ws3.opt

from .cbm import plugin_c_curves
from .model import build_model, load_curves, sum_fluxes, sum_pools
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


def generate(out_dir: str = "results/base_scenario", solver: str = "highs") -> None:
    """Generate the base scenario records (CSV + four-panel figure)."""
    fm = build_model()
    fm.actions["harvest"].is_harvest = True  # required for cmp_c_z (notebook cell 40)
    # Plug in the carbon yield curves so the record's carbon columns are populated.
    c_curves_p, c_curves_f = load_curves()
    plugin_c_curves(fm, c_curves_p, c_curves_f, sum_pools, sum_fluxes)
    df, _problem, elapsed = solve(fm, solver=solver)
    os.makedirs(out_dir, exist_ok=True)
    fig, _axes = plot_scenario(df)
    fig.savefig(os.path.join(out_dir, "base_scenario.pdf"), bbox_inches="tight")
    with_provenance(df, solver=solver).to_csv(
        os.path.join(out_dir, "base_scenario.csv"), index=False)
    print(f"Wrote base scenario records to {out_dir} (solver={solver}, solve {elapsed:.1f}s)")
