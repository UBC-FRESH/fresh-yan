"""Record provenance and shape checks for the tracked records under results/."""

from pathlib import Path

import pandas as pd

RECORDS = Path("results/no_harvest")
PROVENANCE_COLUMNS = ["fy_commit", "fy_version", "ws3_version", "libcbm_version"]


def test_no_harvest_records_have_provenance_and_shape() -> None:
    df = pd.read_csv(RECORDS / "no_harvest_cbm.csv")
    assert len(df) == 20
    for column in PROVENANCE_COLUMNS:
        assert column in df.columns
        assert df[column].notna().all()


def test_no_harvest_summary_metrics() -> None:
    summary = pd.read_csv(RECORDS / "no_harvest_pct_diff_summary.csv")
    assert set(summary["metric"]) == {"biomass_stock", "dom_stock", "eco_stock", "net_emission"}
    assert (summary["mean_abs_pct_diff"] >= 0).all()
