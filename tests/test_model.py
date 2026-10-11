"""Model construction and CBM SIT export smoke tests (small test model)."""

from fresh_yan import model


def test_build_model_and_to_cbm_sit() -> None:
    fm = model.build_model(model_name="tsa24", model_path="data/woodstock_model_files_test")
    mapping = model.disturbance_type_mapping(fm)
    sit_config, sit_tables = model.to_cbm_sit(fm, mapping)
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
