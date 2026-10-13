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


def test_femic_campaign_records_have_provenance_and_shape() -> None:
    """The five-TSA campaign records (when present) carry provenance and expected shapes."""
    summaries = sorted(Path("results").glob("femic-tsa*/tradeoff_grid/tradeoff_grid_summary.csv"))
    for summary_path in summaries:
        df = pd.read_csv(summary_path)
        assert len(df) == 5000, summary_path
        assert not df.isna().any().any(), summary_path
        for column in PROVENANCE_COLUMNS:
            assert column in df.columns and df[column].notna().all(), summary_path
    for base_path in sorted(Path("results").glob("femic-tsa*/base_scenario/base_scenario.csv")):
        df = pd.read_csv(base_path)
        assert len(df) == 20, base_path
        assert (df["ohv"] >= 0).all(), base_path
