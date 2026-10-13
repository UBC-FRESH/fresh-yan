"""Build the five-unit manuscript figures: study-area map, age structure, species mix.

Reads each femic instance's ws3 area section (``.are``) and boundary feather and writes:

- ``five_tsa_map.pdf``       the five TSA boundaries, labelled
- ``five_unit_age.pdf``      area by age class, as % of each unit's landbase (5 panels)
- ``five_unit_species.pdf``  area by leading-species code, as % of landbase (5 panels)

Usage:
    python scripts/five_tsa_figures.py --instances-root <femic/external> --out-dir <dir>
"""

from __future__ import annotations

import argparse
import os

import geopandas as gpd
import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import pandas as pd
from shapely import wkb

from fresh_yan.cbm import plugin_c_curves
from fresh_yan.model import build_model, load_curves, sum_fluxes, sum_pools
from fresh_yan.records import with_provenance

TSAS = ["08", "16", "24", "40", "41"]
SPECIES_NAMES = {
    "pl": "Lodgepole pine", "sx": "Hybrid spruce", "sw": "White spruce",
    "sb": "Black spruce", "se": "Engelmann spruce", "bl": "Subalpine fir",
    "at": "Trembling aspen", "fdi": "Douglas-fir",
}


def read_are(path: str) -> pd.DataFrame:
    rows = []
    with open(path) as fh:
        for line in fh:
            p = line.split()
            if len(p) >= 8 and p[0] == "*A":
                rows.append((p[4], int(p[6]), float(p[7])))
    df = pd.DataFrame(rows, columns=["stratum", "age", "area"])
    df["sp"] = df.stratum.str.split("_").str[-1].str.replace("pli", "pl", regex=False)
    return df


def read_boundary(path: str):
    df = pd.read_feather(path)
    geom = df.geometry.iloc[0]
    return wkb.loads(bytes(geom)) if isinstance(geom, (bytes, bytearray)) else geom


def main(instances_root: str, out_dir: str) -> None:
    os.makedirs(out_dir, exist_ok=True)

    # --- study-area map ---
    fig, ax = plt.subplots(figsize=(7.0, 6.0))
    for s in TSAS:
        geom = read_boundary(
            os.path.join(instances_root, f"femic-tsa{s}-instance/data/tsa_boundaries.feather"))
        gpd.GeoSeries([geom]).plot(ax=ax, alpha=0.35, edgecolor="black", linewidth=0.8)
        c = geom.representative_point()
        ax.annotate(f"TSA {s}", (c.x, c.y), ha="center", va="center", fontsize=9)
    ax.set_xlabel("Longitude")
    ax.set_ylabel("Latitude")
    ax.set_title("The five management units")
    fig.savefig(os.path.join(out_dir, "five_tsa_map.pdf"), bbox_inches="tight")
    plt.close(fig)

    # --- age + species panels ---
    fig_age, axes_age = plt.subplots(1, 5, figsize=(13, 2.8), sharey=False)
    fig_sp, axes_sp = plt.subplots(1, 5, figsize=(13, 2.8), sharey=False)
    for ax_a, ax_s, s in zip(axes_age, axes_sp, TSAS, strict=True):
        df = read_are(os.path.join(
            instances_root, f"femic-tsa{s}-instance/output/ws3/tsa{s}.are"))
        total = df.area.sum()
        age = df.groupby("age").area.sum() / total * 100
        ax_a.bar((age.index * 10 + 5), age.values, width=8, color="0.3")
        ax_a.set_title(f"TSA {s}", fontsize=9)
        ax_a.set_xlabel("Age (yr)", fontsize=8)
        ax_a.tick_params(labelsize=7)
        sp = df.groupby("sp").area.sum() / total * 100
        sp = sp.sort_values(ascending=False).head(6)
        ax_s.bar(range(len(sp)), sp.values, color="0.3")
        ax_s.set_xticks(range(len(sp)))
        ax_s.set_xticklabels([SPECIES_NAMES.get(k.split("+")[0], k) for k in sp.index],
                             rotation=45, ha="right", fontsize=6.5)
        ax_s.set_title(f"TSA {s}", fontsize=9)
        ax_s.set_xlabel("Leading species", fontsize=8)
        ax_s.tick_params(labelsize=7)
    axes_age[0].set_ylabel("% of landbase", fontsize=8)
    axes_sp[0].set_ylabel("% of landbase", fontsize=8)
    fig_age.suptitle("Age structure of the five model instances", fontsize=10)
    fig_sp.suptitle("Leading-species composition of the five model instances", fontsize=10)
    fig_age.savefig(os.path.join(out_dir, "five_unit_age.pdf"), bbox_inches="tight")
    fig_sp.savefig(os.path.join(out_dir, "five_unit_species.pdf"), bbox_inches="tight")
    plt.close("all")

    # attributes record: reproducible period-0 inventory values (manuscript Table 1)
    rows = []
    for s in TSAS:
        are = read_are(os.path.join(
            instances_root, f"femic-tsa{s}-instance/output/ws3/tsa{s}.are"))
        fm = build_model(model_name=f"tsa{s}",
                         model_path=os.path.join(
                             instances_root, f"femic-tsa{s}-instance/output/ws3"),
                         section_units="periods")
        c_p, c_f = load_curves(
            os.path.join("curves", f"femic-tsa{s}", "c_curves_p.pkl"),
            os.path.join("curves", f"femic-tsa{s}", "c_curves_f.pkl"))
        plugin_c_curves(fm, c_p, c_f, sum_pools, sum_fluxes)
        eco0 = float(fm.inventory(0, "ecosystem"))
        assert eco0 > 0, f"no ecosystem inventory for tsa{s} (curves not plugged?)"
        rows.append({"tsa": f"tsa{s}", "thlb_ha": float(are.area.sum()),
                     "dev_types": len(fm.dtypes), "initial_eco_mtc": eco0 / 1e6})
    with_provenance(pd.DataFrame(rows)).to_csv(
        os.path.join(os.path.dirname(os.path.normpath(out_dir)),
                     "five_tsa_attributes.csv"), index=False)
    print(f"Wrote five-unit figures to {out_dir} and the attributes record to "
          f"{os.path.dirname(os.path.normpath(out_dir))}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--instances-root", required=True)
    parser.add_argument("--out-dir", default="results/cross-tsa/figures")
    args = parser.parse_args()
    main(args.instances_root, args.out_dir)
