"""Robustness spot-checks for the emission-minimizing harvest flip (TSA 24).

One-at-a-time variants around the baseline grid formulation:
  - even-flow band: none / 5% (baseline) / 15%
  - utilized-fibre allocation: 50/50 paper-solid (baseline) / 100% solid
  - horizon: 15 / 20 (baseline) / 25 periods
Reference cells: half-life 100 with displacement factors 0.5, 1.0, 2.0.

Run from the repository root:
    python scripts/robustness_checks.py [--out-dir results/robustness]
"""

from __future__ import annotations

import argparse
import os
import time
from functools import partial

import pandas as pd

from fresh_yan.accounting import cmp_c_ce_v2, track_system_emission_v2
from fresh_yan.cbm import plugin_c_curves
from fresh_yan.model import build_model, load_curves, sum_fluxes, sum_pools
from fresh_yan.records import with_provenance
from fresh_yan.scenario import cmp_c_caa, compile_scenario
from fresh_yan.tradeoff_grid import CREDIT, HALF_LIFE_PAPER, UTIL_RATE

import ws3.opt

CELLS = [(100, 0.5), (100, 1.0), (100, 2.0)]
VARIANTS = [
    ("baseline", {"eps": 0.05, "prop_solid": 0.5, "horizon": 20}),
    ("no_even_flow", {"eps": None, "prop_solid": 0.5, "horizon": 20}),
    ("even_flow_15", {"eps": 0.15, "prop_solid": 0.5, "horizon": 20}),
    ("solid_only", {"eps": 0.05, "prop_solid": 1.0, "horizon": 20}),
    ("horizon_15", {"eps": 0.05, "prop_solid": 0.5, "horizon": 15}),
    ("horizon_25", {"eps": 0.05, "prop_solid": 0.5, "horizon": 25}),
]


def build_problem(fm, half_life, displacement, eps, prop_solid):
    vexpr = f"totvol * {UTIL_RATE:0.2f}"
    coeff_funcs = {
        "z": partial(cmp_c_ce_v2, half_life_solid_wood=half_life,
                     half_life_paper=HALF_LIFE_PAPER, proportion_solid_wood=prop_solid,
                     util_rate=UTIL_RATE, displacement_factor_solid=displacement,
                     credit=CREDIT),
        "cflw_ha": partial(cmp_c_caa, expr="1.", acodes=["harvest"], mask=None),
        "cflw_hv": partial(cmp_c_caa, expr=vexpr, acodes=["harvest"], mask=None),
    }
    cflw_e = {} if eps is None else {
        "cflw_ha": (dict.fromkeys(fm.periods, eps), 1),
        "cflw_hv": (dict.fromkeys(fm.periods, eps), 1),
    }
    return fm.add_problem("emission", coeff_funcs, cflw_e, cgen_data={},
                          acodes=["null", "harvest"], sense=ws3.opt.SENSE_MAXIMIZE,
                          mask=None)


def make_model(horizon):
    fm = build_model(horizon=horizon)
    fm.actions["harvest"].is_harvest = True
    p, f = load_curves()
    plugin_c_curves(fm, p, f, sum_pools, sum_fluxes)
    return fm


def solve(fm, hl, df, eps, prop_solid):
    fm.add_null_action()
    problem = build_problem(fm, hl, df, eps, prop_solid)
    problem.solver("highs")
    fm.reset()
    problem.solve()
    if problem.status() != ws3.opt.STATUS_OPTIMAL:
        raise RuntimeError(f"non-optimal ({problem.status()})")
    schedule = fm.compile_schedule(problem)
    fm.apply_schedule(schedule, force_integral_area=False, override_operability=False,
                      fuzzy_age=False, recourse_enabled=False, verbose=False,
                      compile_c_ycomps=True)
    harvest = compile_scenario(fm)
    emission = track_system_emission_v2(fm, hl, HALF_LIFE_PAPER, prop_solid, UTIL_RATE,
                                        df, CREDIT)
    return float(harvest["ohv"].sum()), float(emission["system"].sum())


def main(out_dir: str) -> None:
    os.makedirs(out_dir, exist_ok=True)
    partial_path = os.path.join(out_dir, "robustness_results.partial.csv")
    rows = []
    models = {}
    t_start = time.time()
    for name, cfg in VARIANTS:
        if cfg["horizon"] not in models:
            print(f"[{time.time() - t_start:7.0f}s] building model (horizon={cfg['horizon']})",
                  flush=True)
            models[cfg["horizon"]] = make_model(cfg["horizon"])
        fm = models[cfg["horizon"]]
        for hl, df in CELLS:
            t0 = time.time()
            vol, em = solve(fm, hl, df, cfg["eps"], cfg["prop_solid"])
            rows.append({"variant": name, "half_life": hl, "displacement_factor": df,
                         "utilized_volume_m3": vol, "net_system_emission_tco2": em,
                         "solve_s": round(time.time() - t0, 1)})
            print(f"[{time.time() - t_start:7.0f}s] {name:14s} hl={hl} df={df}: "
                  f"vol={vol / 1e9:.3f}e9 m3 em={em / 1e9:+.3f}e9 tCO2 "
                  f"({time.time() - t0:.0f}s)", flush=True)
            pd.DataFrame(rows).to_csv(partial_path, index=False)
    out_path = os.path.join(out_dir, "robustness_results.csv")
    with_provenance(pd.DataFrame(rows)).to_csv(out_path, index=False)
    os.remove(partial_path)
    print(f"Wrote {out_path} ({len(rows)} solves)", flush=True)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out-dir", default="results/robustness")
    main(parser.parse_args().out_dir)
