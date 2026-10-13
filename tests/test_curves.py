"""Curve invariants: the committed pickles conserve carbon and carry managed merch.

These checks are pure pickle-level (no model build): the ``ecosystem = biomass + DOM``
identity for every dtype, the simulated-clearcut reset consistency of the managed
dtypes (age-0 equals the pre-harvest state minus merch, within the documented
rotation-cycle residual), and the non-negativity of the HWP inflow source ``merch``.
See ``planning/curve-generation-and-reset-findings.md`` for the defect these curves fix
and the residual bounds.
"""

from __future__ import annotations

import pandas as pd
import pytest

from fresh_yan.curves import _clearcut_event
from fresh_yan.model import load_curves

ROTATION_AGE = 120
MAX_RESET_RESIDUAL = 5.0  # tC/ha; audit range -0.87 .. +3.74 (old defect: ~ -13 .. -31)


@pytest.fixture(scope="module")
def curves():
    c_p, c_f = load_curves()
    return c_p, c_f


def _managed_dtypes(c_p) -> list[str]:
    return [d for d in c_p.index.get_level_values(0).unique()
            if d.split()[4] != d.split()[2]]


def test_ecosystem_is_biomass_plus_dom(curves) -> None:
    """The pickle identity ``ecosystem = biomass + DOM`` holds for every dtype."""
    c_p, _ = curves
    for dtk in c_p.index.get_level_values(0).unique():
        df = c_p.loc[dtk]
        assert (df["ecosystem"] - df["biomass"] - df["DOM"]).abs().max() < 1e-6, dtk


def test_managed_reset_is_conservation_consistent(curves) -> None:
    """Managed age-0 equals the simulated clearcut state (pre - merch) at rotation."""
    c_p, _ = curves
    managed = _managed_dtypes(c_p)
    assert len(managed) == 13  # 24 natural + 13 managed dtypes
    for dtk in managed:
        df = c_p.loc[dtk]
        residual = float(df["ecosystem"].iloc[0]
                         - (df["ecosystem"].iloc[ROTATION_AGE - 1]
                            - df["merch"].iloc[ROTATION_AGE - 1]))
        assert abs(residual) < MAX_RESET_RESIDUAL, (dtk, residual)


def test_managed_merch_is_nonnegative(curves) -> None:
    """The HWP inflow source (``merch``) is non-negative on the managed dtypes."""
    c_p, _ = curves
    for dtk in _managed_dtypes(c_p):
        assert c_p.loc[dtk]["merch"].min() > -1e-6, dtk


_EVENT_COLS = [
    "theme0", "theme1", "theme2", "theme3", "theme4", "species", "using_age_class",
    "min_softwood_age", "max_softwood_age", "min_hardwood_age", "max_hardwood_age",
    "MinYearsSinceDist", "MaxYearsSinceDist", "LastDistTypeID", "MinTotBiomassC",
    "MaxTotBiomassC", "MinSWMerchBiomassC", "MaxSWMerchBiomassC", "MinHWMerchBiomassC",
    "MaxHWMerchBiomassC", "MinTotalStemSnagC", "MaxTotalStemSnagC", "MinSWStemSnagC",
    "MaxSWStemSnagC", "MinHWStemSnagC", "MaxHWStemSnagC", "MinTotalStemSnagMerchC",
    "MaxTotalStemSnagMerchC", "MinSWMerchStemSnagC", "MaxSWMerchStemSnagC",
    "MinHWMerchStemSnagC", "MaxHWMerchStemSnagC", "efficiency", "sort_type",
    "target_type", "target", "disturbance_type", "disturbance_year",
]


def test_clearcut_event_uses_harvest_acode() -> None:
    """The clearcut event's SIT disturbance id follows ``harvest_acode`` (#3).

    Regression test for the femic failure: the event row used the hardcoded
    ``"harvest"`` id, which is undefined in SIT tables whose mapping uses ``"cc"``.
    """
    events = pd.DataFrame(columns=_EVENT_COLS)
    inv = pd.DataFrame([{"theme0": "24", "theme1": "managed", "theme2": "2401000",
                         "theme3": "sbs_sx", "theme4": "2421000", "species": "SX"}])
    cc = _clearcut_event(events, inv, 120, harvest_acode="cc")
    assert cc.iloc[-1]["disturbance_type"] == "cc"
    legacy = _clearcut_event(events, inv, 120)
    assert legacy.iloc[-1]["disturbance_type"] == "harvest"
