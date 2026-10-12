"""Model construction and CBM SIT export smoke tests (small test model)."""

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
