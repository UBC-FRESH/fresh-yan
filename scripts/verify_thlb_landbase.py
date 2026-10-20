"""Verify the THLB landbase rule for a femic instance.

Recomputes the per-stand mean THLB value from the legacy THLB raster using the
same rule as the femic pipeline (``mean_thlb_for_geometry``: mean of raster
values >= 0 over each polygon), sweeps the managed threshold, and checks which
rule reproduces the instance's landbase (``output/woodstock/woodstock_areas.csv``
and the ws3 ``.are`` sections).

For TSA 08 (2026-10-20 run): ``mean THLB >= 50%`` reproduces the landbase
exactly in stand count (112,488) and to 2.05 ha in area (1,400,547.40 vs
1,400,549.45 ha, 0.00015%), with per-species shares identical to two decimals;
``> 50`` and the proportional area-share interpretation do not match.

Inputs:
- ``--instance``: path to a ``femic-tsaXX-instance`` checkout (stand table at
  ``data/shp/tsaXX.shp/stands.shp``, sections at ``output/ws3/tsaXX.are``).
- ``--raster``: path to the legacy THLB raster (``misc.thlb.tif``; EPSG:3005,
  100 m, int16, nodata < 0, values 0-100 percent).

Records (per unit):
- ``thlb_threshold_sweep_<tsa>.csv`` — threshold vs selected stands/area.
- ``thlb_landbase_verification_<tsa>.csv`` — selected vs recorded landbase,
  per-AU and per-species agreement, and borderline exact-mask check results.

Usage:
    python scripts/verify_thlb_landbase.py \
        --instance /path/to/femic-tsa08-instance \
        --raster /path/to/misc.thlb.tif --out-dir results/cross-tsa \
        --check-borderline
"""

from __future__ import annotations

import argparse
import os
import re

import geopandas as gpd
import numpy as np
import pandas as pd
import rasterio
from rasterio.features import rasterize
from rasterio.mask import mask as rio_mask
from rasterio.windows import Window, from_bounds

from fresh_yan.records import with_provenance

SWEEP = [0, 10, 20, 30, 40, 45, 50, 55, 60, 70, 80]


def unit_from_instance(instance: str) -> str:
    match = re.search(r"femic-tsa(\d+)-instance", os.path.normpath(instance))
    assert match, f"cannot infer TSA code from instance path: {instance}"
    return f"tsa{match.group(1)}"


def mean_thlb_from_raster(geometry_file: str, raster_path: str) -> gpd.GeoDataFrame:
    """Per-polygon mean THLB (cells with value >= 0), rasterized on the raster grid."""
    gdf = gpd.read_file(geometry_file)
    with rasterio.open(raster_path) as src:
        assert str(gdf.crs) == str(src.crs), f"CRS mismatch: {gdf.crs} vs {src.crs}"
        xmin, ymin, xmax, ymax = gdf.total_bounds
        win = from_bounds(xmin - 500, ymin - 500, xmax + 500, ymax + 500, src.transform)
        win = win.round_offsets().round_lengths()
        win = win.intersection(Window(0, 0, src.width, src.height))
        arr = src.read(1, window=win)
        transform = src.window_transform(win)
    ids = rasterize(
        ((geom, i + 1) for i, geom in enumerate(gdf.geometry)),
        out_shape=arr.shape, transform=transform, fill=0, dtype="int32",
        all_touched=False)
    flat_ids = ids.ravel()
    flat_vals = arr.ravel()
    valid = (flat_ids > 0) & (flat_vals >= 0)
    sums = np.bincount(flat_ids[valid], weights=flat_vals[valid].astype(np.float64),
                       minlength=len(gdf) + 1)
    counts = np.bincount(flat_ids[valid], minlength=len(gdf) + 1)
    means = np.full(len(gdf) + 1, np.nan)
    has = counts > 0
    means[has] = sums[has] / counts[has]
    gdf["thlb_mean"] = means[1:]
    return gdf


def main(instance: str, raster_path: str, out_dir: str, threshold: float = 50.0,
         check_borderline: bool = False) -> None:
    tsa = unit_from_instance(instance)
    gdf = mean_thlb_from_raster(
        os.path.join(instance, "data", "shp", f"{tsa}.shp", "stands.shp"),
        raster_path)
    areas = gdf["area"].to_numpy(float)

    sweep_rows = []
    for t in SWEEP:
        gt = (gdf.thlb_mean > t).to_numpy()
        ge = (gdf.thlb_mean >= t).to_numpy()
        sweep_rows.append({
            "threshold": t,
            "stands_gt": int(gt.sum()), "area_gt_ha": float(areas[gt].sum()),
            "stands_ge": int(ge.sum()), "area_ge_ha": float(areas[ge].sum()),
        })
    sweep = pd.DataFrame(sweep_rows)

    selected = (gdf.thlb_mean >= threshold).to_numpy()
    sel_stands = int(selected.sum())
    sel_area = float(areas[selected].sum())

    are_rows = []
    are_path = os.path.join(instance, "output", "ws3", f"{tsa}.are")
    with open(are_path) as fh:
        for line in fh:
            parts = line.split()
            if len(parts) >= 8 and parts[0] == "*A":
                are_rows.append((parts[3], parts[4], float(parts[7])))
    are = pd.DataFrame(are_rows, columns=["au", "stratum", "area_ha"])
    are_total = float(are.area_ha.sum())

    sel_au = gdf[selected].groupby(gdf.loc[selected, "theme2"].astype(str)).area.sum()
    are_au = are.groupby("au").area_ha.sum()
    au_cmp = pd.concat([are_au.rename("are_ha"), sel_au.rename("selected_ha")],
                       axis=1).fillna(0.0)
    au_cmp["diff_ha"] = au_cmp.selected_ha - au_cmp.are_ha
    max_abs = float(au_cmp.diff_ha.abs().max())
    max_rel = float((au_cmp.diff_ha.abs() / au_cmp.are_ha).max() * 100)

    au_table = pd.read_csv(os.path.join(instance, "data", "model_input_bundle",
                                        "au_table.csv"))
    au_table["au_id"] = au_table.au_id.astype(str)
    species = dict(zip(
        au_table.au_id,
        au_table.stratum_code.str.split("_").str[-1].str.split("+").str[0]
        .str.lower().str.replace("pli", "pl"), strict=False))
    sel_sp = gdf[selected].groupby(gdf.loc[selected, "theme2"].astype(str).map(species)).area.sum()
    are["sp"] = are.au.map(species)
    are_sp = are.groupby("sp").area_ha.sum()
    sp_shares = pd.DataFrame({
        "selected_pct": 100 * sel_sp / sel_sp.sum(),
        "are_pct": 100 * are_sp / are_sp.sum(),
    }).fillna(0.0)
    sp_shares["abs_diff_pp"] = (sp_shares.selected_pct - sp_shares.are_pct).abs()

    ws_path = os.path.join(instance, "output", "woodstock", "woodstock_areas.csv")
    ws_stands = ws_area = np.nan
    if os.path.exists(ws_path):
        ws = pd.read_csv(ws_path)
        ws_stands = len(ws)
        ws_area = float(ws.area_ha.sum())

    border = flips = np.nan
    if check_borderline:
        near = gdf[(gdf.thlb_mean >= threshold - 3) & (gdf.thlb_mean <= threshold + 3)].copy()
        exact = []
        with rasterio.open(raster_path) as src:
            for geom in near.geometry:
                try:
                    arr, _ = rio_mask(src, [geom], crop=True)
                except Exception:
                    exact.append(np.nan)
                    continue
                valid = arr[arr >= 0]
                exact.append(float(np.mean(valid)) if valid.size else np.nan)
        near["exact"] = exact
        flips = int(((near.thlb_mean >= threshold) != (near.exact >= threshold)).sum())
        border = len(near)

    summary = pd.DataFrame([
        {"metric": "selected_threshold_pct", "value": threshold},
        {"metric": "selected_stands", "value": sel_stands},
        {"metric": "selected_area_ha", "value": sel_area},
        {"metric": "woodstock_areas_stands", "value": ws_stands},
        {"metric": "woodstock_areas_area_ha", "value": ws_area},
        {"metric": "are_stands_na", "value": np.nan},
        {"metric": "are_area_ha", "value": are_total},
        {"metric": "per_au_max_abs_diff_ha", "value": max_abs},
        {"metric": "per_au_max_rel_diff_pct", "value": max_rel},
        {"metric": "species_share_max_abs_diff_pp", "value": float(sp_shares.abs_diff_pp.max())},
        {"metric": "borderline_stands_checked", "value": border},
        {"metric": "borderline_exact_flips", "value": flips},
    ])

    os.makedirs(out_dir, exist_ok=True)
    with_provenance(sweep).to_csv(
        os.path.join(out_dir, f"thlb_threshold_sweep_{tsa}.csv"), index=False)
    with_provenance(summary).to_csv(
        os.path.join(out_dir, f"thlb_landbase_verification_{tsa}.csv"), index=False)
    print(f"{tsa}: threshold >={threshold:g}% -> {sel_stands:,} stands, "
          f"{sel_area:,.2f} ha (recorded {ws_stands:,} stands / {ws_area:,.2f} ha; "
          f".are {are_total:,.2f} ha)")
    print(f"per-AU max |diff| {max_abs:.2f} ha ({max_rel:.4f}%); "
          f"species share max |diff| {sp_shares.abs_diff_pp.max():.4f} pp; "
          f"borderline flips {flips}")
    print(f"Wrote {out_dir}/thlb_threshold_sweep_{tsa}.csv and "
          f"thlb_landbase_verification_{tsa}.csv")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--instance", required=True)
    parser.add_argument("--raster", required=True)
    parser.add_argument("--out-dir", default="results/cross-tsa")
    parser.add_argument("--threshold", type=float, default=50.0)
    parser.add_argument("--check-borderline", action="store_true")
    args = parser.parse_args()
    main(args.instance, args.raster, args.out_dir, args.threshold,
         args.check_borderline)
