"""VRI vs THLB species composition and THLB inclusion by site class.

Purpose
-------
Reconcile two populations that are easy to confuse:

- the **full VRI stand table** (the population behind the 01a data-prep
  diagnostic plots, whose abundance bars are shares of the VRI area), and
- the **model landbase** (the THLB-filtered, age-classed stands exported to
  ``output/ws3/*.are`` and used by the manuscript).

For every femic instance it computes, area-weighted and aggregated by leading
species (first token of each mixed stratum code):

1. species composition of the full VRI stand table,
2. species composition of the model landbase (THLB),
3. THLB inclusion rates by (species, site-index class),

so that figure/table denominators can be checked against the source data rather
than argued from expectation.

Inputs (per unit, under ``--instances-root``):
- ``femic-tsaXX-instance/data/shp/tsaXX.shp/stands.shp``
  (stand table; ``theme2`` = AU id, ``SPECIES_CD``, ``age``, ``area`` in ha)
- ``femic-tsaXX-instance/output/ws3/tsaXX.are``
  (model landbase; AU, stratum, age class, area in ha)
- ``femic-tsaXX-instance/data/model_input_bundle/au_table.csv``
  (``au_id`` -> ``stratum_code``, ``si_level``)

Records:
- ``cross-tsa/species_composition_vri_vs_thlb.csv``
- ``cross-tsa/thlb_inclusion_by_si.csv``

Usage:
    python scripts/vri_vs_thlb_composition.py \
        --instances-root /path/to/femic/external --out-dir results/cross-tsa
"""

from __future__ import annotations

import argparse
import os

import pandas as pd
import pyogrio

from fresh_yan.records import with_provenance

UNITS = ["08", "16", "24", "40", "41"]

SPECIES_NAMES = {
    "at": "Trembling aspen", "pl": "Lodgepole pine", "sx": "Hybrid spruce",
    "sw": "White spruce", "sb": "Black spruce", "se": "Engelmann spruce",
    "s": "Spruce spp.", "bl": "Subalpine fir", "fdi": "Douglas-fir",
    "fd": "Douglas-fir", "ep": "Paper birch", "ac": "Black cottonwood",
}


def leading_species(stratum_code: str) -> str:
    """First-listed (leading) species of a stratum code, normalized (pli -> pl)."""
    token = str(stratum_code).split("_")[-1].split("+")[0].lower()
    return "pl" if token == "pli" else token


def read_are(path: str) -> pd.DataFrame:
    """Parse ws3 ``.are`` rows: (AU, stratum, age class, area ha)."""
    rows = []
    with open(path) as fh:
        for line in fh:
            parts = line.split()
            if len(parts) >= 8 and parts[0] == "*A":
                rows.append((parts[3], parts[4], int(parts[6]), float(parts[7])))
    df = pd.DataFrame(rows, columns=["au_id", "stratum", "age_class", "area_ha"])
    df["au_id"] = df.au_id.astype(str)
    return df


def main(instances_root: str, out_dir: str = "results/cross-tsa") -> None:
    composition_rows = []
    inclusion_rows = []

    for unit in UNITS:
        base = os.path.join(instances_root, f"femic-tsa{unit}-instance")
        stands = pyogrio.read_dataframe(
            os.path.join(base, "data", "shp", f"tsa{unit}.shp", "stands.shp"),
            read_geometry=False)
        stands = stands.rename(columns={"area": "area_ha"})
        stands["au_id"] = stands.theme2.astype(str)
        are = read_are(os.path.join(base, "output", "ws3", f"tsa{unit}.are"))
        au = pd.read_csv(os.path.join(
            base, "data", "model_input_bundle", "au_table.csv"))
        au["au_id"] = au.au_id.astype(str)

        au_map = au[["au_id", "stratum_code", "si_level"]].copy()
        au_map["species"] = au_map.stratum_code.map(leading_species)

        vri = stands.merge(au_map, on="au_id", how="left")
        assert vri.species.notna().all(), f"unmatched AU ids in tsa{unit}"
        thlb = are.merge(au_map, on="au_id", how="left")
        assert thlb.species.notna().all(), f"unmatched AU ids in tsa{unit} .are"

        for scope, df in (("VRI", vri), ("THLB", thlb)):
            total = float(df.area_ha.sum())
            g = df.groupby("species").area_ha.sum().sort_values(ascending=False)
            for sp, area in g.items():
                composition_rows.append({
                    "unit": f"tsa{unit}", "scope": scope, "species": sp,
                    "species_name": SPECIES_NAMES.get(sp, sp),
                    "area_ha": float(area), "pct": 100.0 * float(area) / total,
                })

        inc = (vri.groupby(["species", "si_level"]).area_ha.sum()
               .rename("vri_ha").to_frame()
               .join(thlb.groupby(["species", "si_level"]).area_ha.sum()
                     .rename("thlb_ha"), how="outer")
               .fillna(0.0).reset_index())
        inc["inclusion_pct"] = 100.0 * inc.thlb_ha / inc.vri_ha
        inc.insert(0, "unit", f"tsa{unit}")
        inclusion_rows.extend(inc.to_dict("records"))

        vri_total = float(vri.area_ha.sum())
        thlb_total = float(thlb.area_ha.sum())
        print(f"tsa{unit}: VRI {vri_total/1e6:.2f} Mha -> THLB {thlb_total/1e6:.2f} Mha "
              f"({100*thlb_total/vri_total:.0f}%)", flush=True)

    comp = pd.DataFrame(composition_rows)
    incl = pd.DataFrame(inclusion_rows)
    os.makedirs(out_dir, exist_ok=True)
    with_provenance(comp).to_csv(
        os.path.join(out_dir, "species_composition_vri_vs_thlb.csv"), index=False)
    with_provenance(incl).to_csv(
        os.path.join(out_dir, "thlb_inclusion_by_si.csv"), index=False)
    print(f"Wrote {out_dir}/species_composition_vri_vs_thlb.csv "
          f"({len(comp)} rows) and thlb_inclusion_by_si.csv ({len(incl)} rows)",
          flush=True)

    print("\n=== leading species by scope (pct of scope area) ===")
    for unit in UNITS:
        for scope in ("VRI", "THLB"):
            d = comp[(comp.unit == f"tsa{unit}") & (comp.scope == scope)]
            top = d.sort_values("pct", ascending=False).head(4)
            print(f"tsa{unit} {scope:4s}: " + " | ".join(
                f"{r.species_name} {r.pct:.1f}%" for r in top.itertuples()))


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--instances-root", required=True)
    parser.add_argument("--out-dir", default="results/cross-tsa")
    args = parser.parse_args()
    main(args.instances_root, args.out_dir)
