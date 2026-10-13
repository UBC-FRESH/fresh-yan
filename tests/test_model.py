"""Model construction and CBM SIT export smoke tests (small test model)."""

import pytest

from fresh_yan import model


def test_femic_period_unit_sections_and_cc_action() -> None:
    """Femic ``export ws3-sections`` contract: period-unit ages and the ``cc`` action."""
    fm = model.build_model(model_name="tsa99", model_path="tests/fixtures/cc_period_units",
                           section_units="periods")
    key = ("99", "managed", "9901000", "test_sp", "9921000")
    assert key in fm.dtypes
    assert "cc" in fm.actions
    # period-unit ages are converted to years on import (period_length 10)
    assert set(fm.dt(key)._areas[0].keys()) == {0, 10, 20}
    assert fm.dt(key).ycomp("totvol")[10] == 5.0
    mapping = model.disturbance_type_mapping(fm, harvest_acode="cc")
    assert mapping[0]["user_dist_type"] == "cc"
    assert fm.dt(key).last_pass_disturbance == "cc"


def test_model_paths_and_curves_dir_resolution() -> None:
    assert model.model_paths("tsa24") == ("tsa24", "data/woodstock_model_files_tsa24")
    assert model.model_paths("tsa08", model_path="/tmp/ws3_sections") == (
        "tsa08", "/tmp/ws3_sections")
    assert model.model_paths("tsa08", model_name="tsa08_clipped") == (
        "tsa08_clipped", "data/woodstock_model_files_tsa08")
    assert model.curves_dir_for("tsa24") == "curves"
    assert model.curves_dir_for("tsa08") == "curves/tsa08"
    assert model.curves_dir_for("tsa08", "custom/curves") == "custom/curves"


def test_build_model_and_to_cbm_sit() -> None:
    fm = model.build_model(model_name="tsa24", model_path="data/woodstock_model_files_test")
    mapping = model.disturbance_type_mapping(fm)
    _sit_config, sit_tables = model.to_cbm_sit(fm, mapping)
    assert set(sit_tables) >= {
        "sit_classifiers",
        "sit_disturbance_types",
        "sit_age_classes",
        "sit_yield",
        "sit_inventory",
        "sit_events",
        "sit_transitions",
    }
    assert len(sit_tables["sit_inventory"]) > 0
    vcols = [c for c in sit_tables["sit_yield"].columns
             if c.startswith("v") and c[1:].isdigit()]
    assert vcols and sit_tables["sit_yield"][vcols].min().min() >= 0.0


def test_regeneration_sources_legacy_layout() -> None:
    """Legacy TSA 24: harvest targets are the managed dtypes, sourced from naturals."""
    from fresh_yan.curves import _regeneration_sources

    fm = model.build_model()
    sources = _regeneration_sources(fm, "harvest")
    assert set(sources) == {k for k in fm.dtypes if k[2] != k[4]}
    for source in sources.values():
        assert source[2] == source[4]


def test_gen_scenario_rejects_unknown_harvest_acode() -> None:
    """An action code absent from the model must raise, not zero the LP coefficients."""
    from fresh_yan.scenario import gen_scenario

    fm = model.build_model(model_name="tsa24", model_path="data/woodstock_model_files_test")
    with pytest.raises(ValueError, match="harvest_acode"):
        gen_scenario(fm, harvest_acode="nonexistent_acode")


def test_plugin_c_curves_full_mask_yields() -> None:
    """Femic-style full-mask yield entries receive the plugged carbon curves (#3)."""
    import pandas as pd

    from fresh_yan.cbm import plugin_c_curves

    fm = model.build_model(model_name="tsa99", model_path="tests/fixtures/cc_period_units",
                           section_units="periods")
    key = ("99", "managed", "9901000", "test_sp", "9921000")
    dtype_str = " ".join(key)
    idx = pd.MultiIndex.from_tuples([(dtype_str, 0), (dtype_str, 1), (dtype_str, 2)],
                                    names=["dtype_key", "timestep"])
    c_p = pd.DataFrame({"ecosystem": [1.0, 2.0, 3.0]}, index=idx)
    c_f = pd.DataFrame({"total_emission": [0.1, 0.2, 0.3]}, index=idx)
    plugin_c_curves(fm, c_p, c_f, ["ecosystem"], ["total_emission"])
    dt = fm.dt(key)
    assert dt.ycomp("ecosystem") is not None
    assert dt.ycomp("total_emission") is not None
    # values are retrievable on the age axis (flat-hold beyond the last point)
    assert 1.0 <= float(dt.ycomp("ecosystem")[5]) <= 3.0
