"""Model construction and CBM SIT export smoke tests (small test model)."""

from fresh_yan import model


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
