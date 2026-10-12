"""Trade-off grid records: emission-minimizing scenarios over (half-life, displacement).

For each (displacement factor, solid-wood half-life) pair, solve the landscape LP that
minimizes net system emissions with HWP first-order decay and substitution, under 5%
even-flow constraints on harvested area and volume. Records per-period harvest, HWP
stock, and emission trajectories plus a per-scenario summary (total harvested volume,
total net system emission), matching the legacy ``minimize_emission_loop.ipynb``
experiment but on the corrected (v2) accounting: stock-difference ecosystem term,
products-only HWP ledger, HWP inflow from the curve merchantable-carbon pool
(``src/fresh_yan/accounting.py``).
"""

from __future__ import annotations

import os
from concurrent.futures import ProcessPoolExecutor, as_completed
from functools import partial

import matplotlib.pyplot as plt
import pandas as pd
import ws3.opt

from .accounting import cmp_c_ce_v2, track_system_emission_v2, track_system_stock_v2
from .cbm import plugin_c_curves
from .model import build_model, curves_dir_for, load_curves, model_paths, sum_fluxes, sum_pools
from .records import with_provenance
from .scenario import cmp_c_caa, compile_scenario

# HWP parameters (manuscript methods): 85% utilization; utilized fibre split 50/50
# between paper (half-life 2 yr) and solid wood products (grid half-life); solid-wood
# displacement is the grid parameter, paper displacement is zero.
HALF_LIFE_PAPER = 2
PROPORTION_SOLID_WOOD = 0.5
UTIL_RATE = 0.85
CREDIT = 1.0

_FM = None  # per-worker ForestModel (initialized once per process)


def _init_worker(tsa: str = "tsa24", model_name: str | None = None,
                 model_path: str | None = None, curves_dir: str | None = None,
                 section_units: str = "years", harvest_acode: str = "harvest") -> None:
    global _FM
    name, path = model_paths(tsa, model_name, model_path)
    _FM = build_model(model_name=name, model_path=path, section_units=section_units)
    _FM.actions[harvest_acode].is_harvest = True
    # Plug in the carbon yield curves (legacy loop notebook cell 14)
    curves_dir = curves_dir_for(tsa, curves_dir)
    c_curves_p, c_curves_f = load_curves(os.path.join(curves_dir, "c_curves_p.pkl"),
                                         os.path.join(curves_dir, "c_curves_f.pkl"))
    plugin_c_curves(_FM, c_curves_p, c_curves_f, sum_pools, sum_fluxes)


def build_problem(fm, half_life: float, displacement: float,
                  harvest_acode: str = "harvest"):
    """Build the emission-minimizing scenario problem (maximize negative net emissions)."""
    vexpr = f"totvol * {UTIL_RATE:0.2f}"
    coeff_funcs = {
        "z": partial(cmp_c_ce_v2, half_life_solid_wood=half_life,
                     half_life_paper=HALF_LIFE_PAPER,
                     proportion_solid_wood=PROPORTION_SOLID_WOOD,
                     util_rate=UTIL_RATE, displacement_factor_solid=displacement,
                     credit=CREDIT),
        "cflw_ha": partial(cmp_c_caa, expr="1.", acodes=[harvest_acode], mask=None),
        "cflw_hv": partial(cmp_c_caa, expr=vexpr, acodes=[harvest_acode], mask=None),
    }
    cflw_e = {
        "cflw_ha": (dict.fromkeys(fm.periods, 0.05), 1),
        "cflw_hv": (dict.fromkeys(fm.periods, 0.05), 1),
    }
    return fm.add_problem("emission", coeff_funcs, cflw_e, cgen_data={},
                          acodes=["null", harvest_acode], sense=ws3.opt.SENSE_MAXIMIZE,
                          mask=None)


def solve_scenario(fm, half_life: float, displacement: float, solver: str = "highs",
                   harvest_acode: str = "harvest"):
    """Run one emission-minimizing scenario.

    Returns ``(harvest, stock, emission)`` frames (per-period trajectories).
    """
    fm.add_null_action()
    problem = build_problem(fm, half_life, displacement, harvest_acode=harvest_acode)
    problem.solver(solver)
    fm.reset()
    problem.solve()
    if problem.status() != ws3.opt.STATUS_OPTIMAL:
        raise RuntimeError(
            f"scenario not optimal (hl={half_life}, df={displacement}, "
            f"status={problem.status()})")
    schedule = fm.compile_schedule(problem)
    fm.apply_schedule(schedule, force_integral_area=False, override_operability=False,
                      fuzzy_age=False, recourse_enabled=False, verbose=False,
                      compile_c_ycomps=True)
    harvest = compile_scenario(fm, harvest_acode=harvest_acode)
    stock = track_system_stock_v2(fm, half_life, HALF_LIFE_PAPER, PROPORTION_SOLID_WOOD,
                                  UTIL_RATE)
    emission = track_system_emission_v2(fm, half_life, HALF_LIFE_PAPER,
                                        PROPORTION_SOLID_WOOD, UTIL_RATE, displacement,
                                        CREDIT)
    plt.close("all")  # the legacy trackers plot as a side effect; keep memory flat
    return harvest, stock, emission


def _run_pair(args: tuple[float, float, str, str]):
    half_life, displacement, solver, harvest_acode = args
    harvest, stock, emission = solve_scenario(_FM, half_life, displacement, solver=solver,
                                              harvest_acode=harvest_acode)
    return half_life, displacement, harvest, stock, emission


def _tag(df: pd.DataFrame, half_life: float, displacement: float) -> pd.DataFrame:
    out = df.copy()
    out.insert(0, "half_life", half_life)
    out.insert(0, "displacement_factor", displacement)
    return out


def generate(out_dir: str = "results/tradeoff_grid",
             displacements: list[float] | None = None,
             half_lives: list[int] | None = None,
             workers: int = 1, solver: str = "highs", tsa: str = "tsa24",
             model_name: str | None = None, model_path: str | None = None,
             curves_dir: str | None = None, section_units: str = "years",
             harvest_acode: str = "harvest") -> None:
    """Generate the trade-off grid records (long-format CSVs + summary)."""
    if displacements is None:
        displacements = [round(i * 0.1, 1) for i in range(25)]  # 0.0 .. 2.4
    if half_lives is None:
        half_lives = list(range(1, 201))  # 1 .. 200

    pairs = [(hl, df, solver, harvest_acode) for df in displacements for hl in half_lives]
    harvest_rows, stock_rows, emission_rows, summary_rows = [], [], [], []
    done = 0

    def collect(half_life, displacement, harvest, stock, emission):
        nonlocal done
        harvest_rows.append(_tag(harvest, half_life, displacement))
        stock_rows.append(_tag(stock, half_life, displacement))
        emission_rows.append(_tag(emission, half_life, displacement))
        summary_rows.append({
            "displacement_factor": displacement,
            "half_life": half_life,
            "total_harvested_volume_m3": float(harvest["ohv"].sum()),
            "total_net_system_emission_tco2": float(emission["system"].sum()),
        })
        done += 1
        if done % 50 == 0 or done == len(pairs):
            print(f"  {done}/{len(pairs)} scenarios", flush=True)

    worker_kwargs = {"tsa": tsa, "model_name": model_name, "model_path": model_path,
                     "curves_dir": curves_dir, "section_units": section_units,
                     "harvest_acode": harvest_acode}
    if workers > 1:
        with ProcessPoolExecutor(max_workers=workers,
                                 initializer=partial(_init_worker, **worker_kwargs)) as pool:
            futures = [pool.submit(_run_pair, pair) for pair in pairs]
            for future in as_completed(futures):
                collect(*future.result())
    else:
        _init_worker(**worker_kwargs)
        for pair in pairs:
            collect(*_run_pair(pair))

    harvest_all = pd.concat(harvest_rows, ignore_index=True)
    stock_all = pd.concat(stock_rows, ignore_index=True)
    emission_all = pd.concat(emission_rows, ignore_index=True)
    summary = pd.DataFrame(summary_rows).sort_values(
        ["displacement_factor", "half_life"]).reset_index(drop=True)

    os.makedirs(out_dir, exist_ok=True)
    with_provenance(harvest_all, solver=solver, tsa=tsa).to_csv(
        os.path.join(out_dir, "tradeoff_grid_harvest.csv"), index=False)
    with_provenance(stock_all, solver=solver, tsa=tsa).to_csv(
        os.path.join(out_dir, "tradeoff_grid_stock.csv"), index=False)
    with_provenance(emission_all, solver=solver, tsa=tsa).to_csv(
        os.path.join(out_dir, "tradeoff_grid_emission.csv"), index=False)
    with_provenance(summary, solver=solver, tsa=tsa).to_csv(
        os.path.join(out_dir, "tradeoff_grid_summary.csv"), index=False)
    print(f"Wrote trade-off grid records to {out_dir} ({len(pairs)} scenarios, "
          f"solver={solver})")
