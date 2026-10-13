"""Accounting invariants: telescoped conservation identity, HWP decay, and LP identity.

These tests exercise the corrected (v2) accounting (`fresh_yan.accounting`) on the real
TSA 24 model: three fast checks on a tiny hand-applied schedule, plus one LP-integration
test (a single emission-minimizing scenario) that pins the invariant
"LP objective == -(reported tracker total)".
"""

from __future__ import annotations

import pytest
import ws3.opt

from fresh_yan.accounting import cmp_c_ce_v2, track_system_emission_v2, track_system_stock_v2
from fresh_yan.cbm import plugin_c_curves
from fresh_yan.model import build_model, load_curves, sum_fluxes, sum_pools
from fresh_yan.tradeoff_grid import (
    CREDIT,
    HALF_LIFE_PAPER,
    PROPORTION_SOLID_WOOD,
    UTIL_RATE,
    build_problem,
)

NAT = ("tsa24", "1", "2402000", "100", "2402000")
MAN = ("tsa24", "1", "2402000", "100", "2422000")
SCHEDULE = [(NAT, 95, 100.0, "harvest", 1, None)]


class _Node:
    """Minimal path node stub matching ws3's node ``data()`` interface."""

    def __init__(self, data: dict) -> None:
        self._data = data

    def data(self, key=None):
        return self._data[key] if key else self._data


@pytest.fixture(scope="module")
def fm():
    model = build_model()
    model.actions["harvest"].is_harvest = True
    p, f = load_curves()
    plugin_c_curves(model, p, f, sum_pools, sum_fluxes)
    # ws3 compiles an action's operability lazily; the first apply_action call for an
    # uncompiled action returns error 3 ("not compiled yet"), so pre-compile it.
    for dtk, _age, _area, acode, *_ in SCHEDULE:
        model.dt(dtk).compile_action(acode)
    model.apply_schedule(SCHEDULE, force_integral_area=False, override_operability=False,
                         fuzzy_age=False, recourse_enabled=False, verbose=False,
                         compile_c_ycomps=True)
    return model


def test_telescoped_conservation_identity(fm) -> None:
    stock = track_system_stock_v2(fm, 100, HALF_LIFE_PAPER, PROPORTION_SOLID_WOOD, UTIL_RATE)
    emission = track_system_emission_v2(fm, 100, HALF_LIFE_PAPER, PROPORTION_SOLID_WOOD,
                                        UTIL_RATE, 1.0, CREDIT)
    e0 = fm.inventory(0, "ecosystem")
    e_t = fm.inventory(fm.periods[-1], "ecosystem")
    h_t = stock["sum_product"].iloc[-1]
    sub = emission["substitution"].sum()
    assert emission["system"].sum() == pytest.approx((e0 - e_t - h_t) * 44 / 12 - sub,
                                                     rel=1e-9)


def test_no_harvest_path_coefficient_is_ecosystem_only(fm) -> None:
    """A path without harvests must reduce to the ecosystem stock difference."""
    age0 = 65
    nodes = []
    for t in range(1, fm.periods[-1] + 1):
        age = age0 + fm.period_length * (t - 1)
        nodes.append(_Node({"dtk": NAT, "age": age, "_dtk": NAT, "_age": age,
                            "acode": "null"}))
    coeff = cmp_c_ce_v2(fm, nodes, half_life_solid_wood=100, half_life_paper=HALF_LIFE_PAPER,
                        proportion_solid_wood=PROPORTION_SOLID_WOOD, util_rate=UTIL_RATE,
                        displacement_factor_solid=1.0, credit=CREDIT)
    dt = fm.dt(NAT)
    e0 = dt.area(0, age0) * dt.ycomp("ecosystem")[age0]
    age_t = age0 + fm.period_length * fm.periods[-1]
    e_t = dt.area(fm.periods[-1], age_t - fm.period_length) * dt.ycomp("ecosystem")[age_t]
    assert coeff == pytest.approx(-(e0 - e_t) * 44 / 12, rel=1e-9)


def test_longer_half_life_stores_more(fm) -> None:
    """Longer solid-wood half-life stores more carbon -> a less negative net emission."""
    nodes = [_Node({"dtk": NAT, "age": 95, "_dtk": MAN, "_age": 0, "acode": "harvest"})]
    for t in range(2, fm.periods[-1] + 1):
        age = fm.period_length * (t - 1)
        nodes.append(_Node({"dtk": MAN, "age": age, "_dtk": MAN, "_age": age,
                            "acode": "null"}))
    common = {"half_life_paper": HALF_LIFE_PAPER,
              "proportion_solid_wood": PROPORTION_SOLID_WOOD, "util_rate": UTIL_RATE,
              "displacement_factor_solid": 1.0, "credit": CREDIT}
    short = cmp_c_ce_v2(fm, nodes, half_life_solid_wood=2, **common)
    long = cmp_c_ce_v2(fm, nodes, half_life_solid_wood=200, **common)
    assert long > short


@pytest.fixture(scope="module")
def fm_lp():
    """Fresh model for the LP-integration test (no pre-applied schedule)."""
    model = build_model()
    model.actions["harvest"].is_harvest = True
    p, f = load_curves()
    plugin_c_curves(model, p, f, sum_pools, sum_fluxes)
    return model


def test_lp_objective_equals_reported_tracker(fm_lp) -> None:
    """The solved LP objective equals the negative of the reported system emission.

    Regression test for the invariant verified in the 2026-10-11 adversarial audit:
    the emission-minimizing problem (hl=100, df=1.5) returns z = 1,586,066,278.97 and
    the reporting tracker returns exactly -z.
    """
    fm_lp.add_null_action()
    problem = build_problem(fm_lp, half_life=100, displacement=1.5)
    problem.solver("highs")
    fm_lp.reset()
    problem.solve()
    assert problem.status() == ws3.opt.STATUS_OPTIMAL

    schedule = fm_lp.compile_schedule(problem)
    fm_lp.apply_schedule(schedule, force_integral_area=False, override_operability=False,
                         fuzzy_age=False, recourse_enabled=False, verbose=False,
                         compile_c_ycomps=True)
    emission = track_system_emission_v2(fm_lp, 100, HALF_LIFE_PAPER,
                                        PROPORTION_SOLID_WOOD, UTIL_RATE, 1.5, CREDIT)
    total = float(emission["system"].sum())
    assert problem.z() == pytest.approx(-total, rel=1e-9)
    assert total == pytest.approx(-1_586_066_278.97, rel=1e-6)
