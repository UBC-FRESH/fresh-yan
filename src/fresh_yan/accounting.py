"""Corrected (v2) carbon accounting for the landscape LP and the records.

Conventions
-----------
Stocks follow the standard ws3 **end-of-period** inventory convention: ``E(t)`` is the
ecosystem carbon at the end of period ``t`` (``t = 0`` is the initial state), i.e. the
period-``t`` areas aged by one period (``age + period_length``) on the carbon yield
curves.  Per-period net system emission:

    em(t) = [E(t-1) - E(t)] + [H(t-1) - H(t)] - sub(t)

which telescopes to ``E(0) - E(T) - H(T) - sum(sub)`` -- exact carbon conservation by
construction.  ``H`` is the products-only HWP pool.  Per the manuscript's methods, the
utilized fibre is divided into two equal categories (paper and solid wood,
``proportion_solid_wood = 0.5``); each decays with exact per-period survival
``2**(-period_length/half_life)``.  Inflow comes from the ``merch`` carbon yield curve
(merchantable stem carbon x ``util_rate``), not from a volume x density conversion, so it
is consistent with the ecosystem ledger.  No gross decay terms and no instant-residue
term (the residue is inside the ecosystem stock change).  Substitution =
``displacement_factor_solid x solid inflow x credit`` (paper displacement is zero).
"""

from __future__ import annotations

from typing import Any

import pandas as pd


def _curve_lookup(fm: Any, dtype_key: Any, age: int, yname: str) -> float:
    """Carbon curve value (tC/ha) at ``age`` for one development type."""
    dt = fm.dt(dtype_key)
    if dt is None:
        return 0.0
    ycomp = dt.ycomp(yname)
    if not ycomp:
        return 0.0
    ymax = getattr(ycomp, "xmax", None)
    lookup_age = min(age, ymax) if ymax is not None else age
    return float(ycomp[lookup_age])


def _eco_stock(fm: Any, period: int, dtype_key: Any, age: int) -> float:
    """End-of-period ecosystem carbon for one cohort (area x curve value).

    ``period == 0`` returns the initial (unaged) value.
    """
    dt = fm.dt(dtype_key)
    if dt is None:
        return 0.0
    shift = 0 if period == 0 else fm.period_length
    area = dt.area(period, age)
    if area == 0.0:
        return 0.0
    return area * _curve_lookup(fm, dtype_key, age + shift, "ecosystem")


def _harvest_area(fm: Any, period: int, dtype_key: Any, age: int) -> float:
    """Area harvested at ``(period, dtype_key, age)`` in the current solution."""
    aa = fm.applied_actions[period].get("harvest")
    if not aa or dtype_key not in aa or age not in aa[dtype_key]:
        return 0.0
    return float(aa[dtype_key][age][0])


def _hwp_inflows(fm: Any, period: int, dtype_key: Any, age: int, util_rate: float,
                 proportion_solid_wood: float) -> tuple[float, float]:
    """Products-only HWP inflows (tC) from one harvest: (solid wood, paper)."""
    area = _harvest_area(fm, period, dtype_key, age)
    if area == 0.0:
        return 0.0, 0.0
    inflow = area * _curve_lookup(fm, dtype_key, age, "merch") * util_rate
    return inflow * proportion_solid_wood, inflow * (1.0 - proportion_solid_wood)


def cmp_c_ce_v2(fm: Any, path: Any, half_life_solid_wood: float,
                half_life_paper: float, proportion_solid_wood: float, util_rate: float,
                displacement_factor_solid: float, credit: float,
                mask: Any = None) -> float:
    """Objective coefficient: negative net system emission (tCO2) along one path.

    Implements ``sum_t em(t)`` with the end-of-period convention; the LP maximizes this
    coefficient (i.e. minimizes net system emissions).  ``mask`` is accepted for
    signature compatibility with the legacy coefficient functions.
    """
    decay_solid = 2.0 ** (-fm.period_length / half_life_solid_wood)
    decay_paper = 2.0 ** (-fm.period_length / half_life_paper)
    e_prev = 0.0
    solid_prev = 0.0
    paper_prev = 0.0
    solid = 0.0
    paper = 0.0
    total = 0.0
    for t, n in enumerate(path, start=1):
        d = n.data()
        if t == 1:
            e_prev = _eco_stock(fm, 0, d["dtk"], d["age"])
        e_t = _eco_stock(fm, t, d["_dtk"], d["_age"])
        if fm.is_harvest(d["acode"]):
            solid_in, paper_in = _hwp_inflows(fm, t, d["dtk"], d["age"], util_rate,
                                              proportion_solid_wood)
        else:
            solid_in = paper_in = 0.0
        solid = solid * decay_solid + solid_in
        paper = paper * decay_paper + paper_in
        sub = solid_in * displacement_factor_solid * credit
        total += ((e_prev - e_t) + (solid_prev - solid) + (paper_prev - paper) - sub)
        e_prev, solid_prev, paper_prev = e_t, solid, paper
    return -total * 44.0 / 12.0


def _period_inflows(fm: Any, util_rate: float, proportion_solid_wood: float):
    """Per-period (solid, paper) HWP inflows (tC) from the applied schedule."""
    solid: dict[int, float] = {p: 0.0 for p in fm.periods}
    paper: dict[int, float] = {p: 0.0 for p in fm.periods}
    for dtk, age, _area, acode, period, *_ in fm.compile_schedule():
        if acode == "harvest":
            solid_in, paper_in = _hwp_inflows(fm, period, dtk, age, util_rate,
                                              proportion_solid_wood)
            solid[period] += solid_in
            paper[period] += paper_in
    return solid, paper


def track_system_stock_v2(fm: Any, half_life_solid_wood: float, half_life_paper: float,
                          proportion_solid_wood: float, util_rate: float) -> pd.DataFrame:
    """Per-period system carbon stocks (tC): ecosystem + products-only HWP pools."""
    decay_solid = 2.0 ** (-fm.period_length / half_life_solid_wood)
    decay_paper = 2.0 ** (-fm.period_length / half_life_paper)
    inflows_solid, inflows_paper = _period_inflows(fm, util_rate, proportion_solid_wood)

    solid = 0.0
    paper = 0.0
    rows = []
    for period in fm.periods:
        eco = fm.inventory(period, "ecosystem")
        solid = solid * decay_solid + inflows_solid[period]
        paper = paper * decay_paper + inflows_paper[period]
        rows.append({"period": period, "solid_wood": solid, "paper": paper,
                     "sum_product": solid + paper, "ecosystem": eco,
                     "system": eco + solid + paper})
    return pd.DataFrame(rows)


def track_system_emission_v2(fm: Any, half_life_solid_wood: float, half_life_paper: float,
                             proportion_solid_wood: float, util_rate: float,
                             displacement_factor_solid: float, credit: float) -> pd.DataFrame:
    """Per-period net system emissions (tCO2): ecosystem + HWP - substitution."""
    decay_solid = 2.0 ** (-fm.period_length / half_life_solid_wood)
    decay_paper = 2.0 ** (-fm.period_length / half_life_paper)
    inflows_solid, inflows_paper = _period_inflows(fm, util_rate, proportion_solid_wood)

    eco_prev = fm.inventory(0, "ecosystem")
    solid_prev = 0.0
    paper_prev = 0.0
    rows = []
    for period in fm.periods:
        eco = fm.inventory(period, "ecosystem")
        solid = solid_prev * decay_solid + inflows_solid[period]
        paper = paper_prev * decay_paper + inflows_paper[period]
        sub = inflows_solid[period] * displacement_factor_solid * credit
        eco_emission = (eco_prev - eco) * 44.0 / 12.0
        solid_emission = (solid_prev - solid) * 44.0 / 12.0
        paper_emission = (paper_prev - paper) * 44.0 / 12.0
        rows.append({
            "period": period,
            "solid_wood": solid_emission,
            "paper": paper_emission,
            "sum_product": solid_emission + paper_emission,
            "ecosystem": eco_emission,
            "substitution": sub * 44.0 / 12.0,
            "system": eco_emission + solid_emission + paper_emission - sub * 44.0 / 12.0,
        })
        eco_prev, solid_prev, paper_prev = eco, solid, paper
    return pd.DataFrame(rows)
