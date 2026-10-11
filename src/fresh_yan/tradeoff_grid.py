"""Trade-off grid records: emission-minimizing scenarios over (half-life, displacement).

For each (displacement factor, solid-wood half-life) pair, solve the landscape LP that
maximizes negative net system emissions (equivalently, minimizes net system emissions)
with HWP first-order decay and substitution, under 5% even-flow constraints on harvested
area and volume. Records per-period harvest, HWP stock, and emission trajectories plus a
per-scenario summary (total harvested volume, total net system emission), matching the
legacy ``minimize_emission_loop.ipynb`` experiment.
"""

from __future__ import annotations

import os
from concurrent.futures import ProcessPoolExecutor, as_completed
from functools import partial

import matplotlib.pyplot as plt
import pandas as pd
import ws3.opt

from .cbm import plugin_c_curves
from .hwp import cmp_c_ce, track_system_emission, track_system_stock
from .model import build_model, load_curves, sum_fluxes, sum_pools
from .records import with_provenance
from .scenario import cmp_c_caa, compile_scenario

# HWP parameters (legacy notebook cell 3): all harvested wood is treated as a single
# solid-wood product type; paper half-life is fixed but irrelevant at this proportion.
HALF_LIFE_PAPER = 2
PROPORTION_SOLID_WOOD = 1.0
UTIL_RATE = 0.85
CREDIT = 1.0

_FM = None  # per-worker ForestModel (initialized once per process)


def _init_worker() -> None:
    global _FM
    _FM = build_model()
    _FM.actions["harvest"].is_harvest = True
    # Plug in the carbon yield curves (legacy loop notebook cell 14)
    c_curves_p, c_curves_f = load_curves()
    plugin_c_curves(_FM, c_curves_p, c_curves_f, sum_pools, sum_fluxes)


def build_problem(fm, half_life: float, displacement: float):
    """Build the emission-minimizing scenario problem (maximize negative net emissions)."""
    vexpr = f"totvol * {UTIL_RATE:0.2f}"
    coeff_funcs = {
        "z": partial(cmp_c_ce, expr=vexpr, half_life_solid_wood=half_life,
                     half_life_paper=HALF_LIFE_PAPER,
                     proportion_solid_wood=PROPORTION_SOLID_WOOD,
                     util_rate=UTIL_RATE, displacement_factor_solid=displacement,
                     credit=CREDIT),
        "cflw_ha": partial(cmp_c_caa, expr="1.", acodes=["harvest"], mask=None),
        "cflw_hv": partial(cmp_c_caa, expr=vexpr, acodes=["harvest"], mask=None),
    }
    cflw_e = {
        "cflw_ha": (dict.fromkeys(fm.periods, 0.05), 1),
        "cflw_hv": (dict.fromkeys(fm.periods, 0.05), 1),
    }
    return fm.add_problem("emission", coeff_funcs, cflw_e, cgen_data={},
                          acodes=["null", "harvest"], sense=ws3.opt.SENSE_MAXIMIZE,
                          mask=None)


def solve_scenario(fm, half_life: float, displacement: float, solver: str = "highs"):
    """Run one emission-minimizing scenario.

    Returns ``(harvest, stock, emission)`` frames (per-period trajectories).
    """
    fm.add_null_action()
    problem = build_problem(fm, half_life, displacement)
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
    harvest = compile_scenario(fm)
    stock = track_system_stock(fm, half_life, HALF_LIFE_PAPER, PROPORTION_SOLID_WOOD,
                               UTIL_RATE)
    emission = track_system_emission(fm, half_life, HALF_LIFE_PAPER, PROPORTION_SOLID_WOOD,
                                     UTIL_RATE, displacement, CREDIT)
    plt.close("all")  # the legacy trackers plot as a side effect; keep memory flat
    return harvest, stock, emission


def _run_pair(args: tuple[float, float, str]):
    half_life, displacement, solver = args
    harvest, stock, emission = solve_scenario(_FM, half_life, displacement, solver=solver)
    return half_life, displacement, harvest, stock, emission


def _tag(df: pd.DataFrame, half_life: float, displacement: float) -> pd.DataFrame:
    out = df.copy()
    out.insert(0, "half_life", half_life)
    out.insert(0, "displacement_factor", displacement)
    return out


def generate(out_dir: str = "results/tradeoff_grid",
             displacements: list[float] | None = None,
             half_lives: list[int] | None = None,
             workers: int = 1, solver: str = "highs") -> None:
    """Generate the trade-off grid records (long-format CSVs + summary)."""
    if displacements is None:
        displacements = [round(i * 0.1, 1) for i in range(25)]  # 0.0 .. 2.4
    if half_lives is None:
        half_lives = list(range(1, 201))  # 1 .. 200

    pairs = [(hl, df, solver) for df in displacements for hl in half_lives]
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

    if workers > 1:
        with ProcessPoolExecutor(max_workers=workers, initializer=_init_worker) as pool:
            futures = [pool.submit(_run_pair, pair) for pair in pairs]
            for future in as_completed(futures):
                collect(*future.result())
    else:
        _init_worker()
        for pair in pairs:
            collect(*_run_pair(pair))

    harvest_all = pd.concat(harvest_rows, ignore_index=True)
    stock_all = pd.concat(stock_rows, ignore_index=True)
    emission_all = pd.concat(emission_rows, ignore_index=True)
    summary = pd.DataFrame(summary_rows).sort_values(
        ["displacement_factor", "half_life"]).reset_index(drop=True)

    os.makedirs(out_dir, exist_ok=True)
    with_provenance(harvest_all, solver=solver).to_csv(
        os.path.join(out_dir, "tradeoff_grid_harvest.csv"), index=False)
    with_provenance(stock_all, solver=solver).to_csv(
        os.path.join(out_dir, "tradeoff_grid_stock.csv"), index=False)
    with_provenance(emission_all, solver=solver).to_csv(
        os.path.join(out_dir, "tradeoff_grid_emission.csv"), index=False)
    with_provenance(summary, solver=solver).to_csv(
        os.path.join(out_dir, "tradeoff_grid_summary.csv"), index=False)
    print(f"Wrote trade-off grid records to {out_dir} ({len(pairs)} scenarios, "
          f"solver={solver})")
