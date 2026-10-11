"""Corrected (v2) carbon accounting for the landscape LP and the records.

Conventions
-----------
Stocks follow the standard ws3 **end-of-period** inventory convention: ``E(t)`` is the
ecosystem carbon at the end of period ``t`` (``t = 0`` is the initial state), i.e. the
period-``t`` areas aged by one period (``age + period_length``) on the carbon yield
curves.  Per-period net system emission:

    em(t) = [E(t-1) - E(t)] + [H(t-1) - H(t)] - sub(t)

which telescopes to ``E(0) - E(T) - H(T) - sum(sub)`` -- exact carbon conservation by
construction.  ``H`` is the products-only HWP pool: inflow = curve merchantable-stem
carbon x ``util_rate`` at each harvest, survival per period ``2**(-10/half_life)``.
No gross decay terms and no instant-residue term (the residue is inside the ecosystem
stock change).  Substitution = ``displacement x inflow x credit``.

The HWP inflow comes from the ``merch`` carbon yield curve (merchantable stem carbon),
not from a volume x density conversion, so it is consistent with the ecosystem ledger.
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


def _hwp_inflow(fm: Any, period: int, dtype_key: Any, age: int, util_rate: float) -> float:
    """Products-only HWP inflow (tC) from one harvest: merch carbon x util_rate."""
    area = _harvest_area(fm, period, dtype_key, age)
    if area == 0.0:
        return 0.0
    return area * _curve_lookup(fm, dtype_key, age, "merch") * util_rate


def cmp_c_ce_v2(fm: Any, path: Any, half_life: float, util_rate: float,
                displacement_factor: float, credit: float, mask: Any = None) -> float:
    """Objective coefficient: negative net system emission (tCO2) along one path.

    Implements ``sum_t em(t)`` with the end-of-period convention; the LP maximizes
    this coefficient (i.e. minimizes net system emissions).  ``mask`` is accepted for
    signature compatibility with the legacy coefficient functions.
    """
    decay = 2.0 ** (-fm.period_length / half_life)
    e_prev = 0.0
    h_prev = 0.0
    hwp = 0.0
    total = 0.0
    for t, n in enumerate(path, start=1):
        d = n.data()
        if t == 1:
            e_prev = _eco_stock(fm, 0, d["dtk"], d["age"])
        e_t = _eco_stock(fm, t, d["_dtk"], d["_age"])
        inflow = (_hwp_inflow(fm, t, d["dtk"], d["age"], util_rate)
                  if fm.is_harvest(d["acode"]) else 0.0)
        hwp = hwp * decay + inflow
        sub = inflow * displacement_factor * credit
        total += (e_prev - e_t) + (h_prev - hwp) - sub
        e_prev, h_prev = e_t, hwp
    return -total * 44.0 / 12.0


def track_system_stock_v2(fm: Any, half_life: float, util_rate: float) -> pd.DataFrame:
    """Per-period system carbon stocks (tC): ecosystem + products-only HWP pool."""
    decay = 2.0 ** (-fm.period_length / half_life)
    schedule = fm.compile_schedule()
    inflows: dict[int, float] = {p: 0.0 for p in fm.periods}
    for dtk, age, _area, acode, period, *_ in schedule:
        if acode == "harvest":
            inflows[period] += _hwp_inflow(fm, period, dtk, age, util_rate)

    hwp = 0.0
    rows = []
    for period in fm.periods:
        eco = fm.inventory(period, "ecosystem")
        hwp = hwp * decay + inflows[period]
        rows.append({"period": period, "ecosystem": eco, "hwp": hwp,
                     "system": eco + hwp})
    return pd.DataFrame(rows)


def track_system_emission_v2(fm: Any, half_life: float, util_rate: float,
                             displacement_factor: float, credit: float) -> pd.DataFrame:
    """Per-period net system emissions (tCO2): ecosystem + HWP - substitution."""
    decay = 2.0 ** (-fm.period_length / half_life)
    schedule = fm.compile_schedule()
    inflows: dict[int, float] = {p: 0.0 for p in fm.periods}
    for dtk, age, _area, acode, period, *_ in schedule:
        if acode == "harvest":
            inflows[period] += _hwp_inflow(fm, period, dtk, age, util_rate)

    eco_prev = fm.inventory(0, "ecosystem")
    hwp_prev = 0.0
    rows = []
    for period in fm.periods:
        eco = fm.inventory(period, "ecosystem")
        hwp = hwp_prev * decay + inflows[period]
        sub = inflows[period] * displacement_factor * credit
        eco_emission = (eco_prev - eco) * 44.0 / 12.0
        hwp_emission = (hwp_prev - hwp) * 44.0 / 12.0
        rows.append({
            "period": period,
            "ecosystem": eco_emission,
            "hwp": hwp_emission,
            "substitution": sub * 44.0 / 12.0,
            "system": eco_emission + hwp_emission - sub * 44.0 / 12.0,
        })
        eco_prev, hwp_prev = eco, hwp
    return pd.DataFrame(rows)
