# Species composition — VRI vs THLB (reconciling the "aspen leads 3 of 5" challenge)

Status: resolved and verified (2026-10-20). This note records the question, the
analysis, the exact sources, the results, and what remains unverified.

## Question

The 01a data-prep diagnostic for TSA 08 (`femic-tsa08-instance/plots/strata-tsa08.png`)
shows **BWBS_SB (black spruce) as the most abundant stratum**, while
`results/cross-tsa/species_composition_vri_vs_thlb.csv` reports black spruce at
only **2.7%** of the model landbase — and trembling aspen leading 3 of 5 units.
The challenge: "how can the leading species of the leading stratum be black
spruce and only constitute <3% of the total inventory?".

## Short answer (denominators)

Both numbers are correct: they describe **different populations**.

- The diagnostic plot's bars are **shares of the full VRI stand-table area**
  (`01a_run-tsa.py`: `totalarea = f_.FEATURE_AREA_SQM.sum()`;
  `plots.py::resolve_strata_plot_ordering` uses `totalarea_p`). For TSA 08 that
  is 5.19 Mha of VRI stands — black spruce leads there (29.3%).
- The species table/Figure 4 in the manuscript are **shares of the harvested
  landbase (THLB)** — the model landbase in `output/ws3/tsaXX.are`. For TSA 08
  that is 1.40 Mha (27% of the VRI area) — aspen leads there (43.0%), black
  spruce is 2.7%.

The THLB filter is strongly productivity/site selective, which is what flips
the composition: black spruce stands are almost entirely outside the THLB
(1.6/2.2/3.4% included at site classes L/M/H), while productive aspen/white
spruce stands are mostly inside it (aspen 16.8/66.1/74.9%).

## Sources (exact)

Instances (public, pinned; pins as used by the campaign):

| unit | instance repo | pin |
|---|---|---|
| TSA 08 | `UBC-FRESH/femic-tsa08-instance` | `9032dc9` |
| TSA 16 | `UBC-FRESH/femic-tsa16-instance` | `1d7f5f8` |
| TSA 24 | `UBC-FRESH/femic-tsa24-instance` | `8b29bb9` |
| TSA 40 | `UBC-FRESH/femic-tsa40-instance` | `7de7927` |
| TSA 41 | `UBC-FRESH/femic-tsa41-instance` | `efa2c0d` |

Per instance (paths relative to the instance root):

- `data/shp/tsaXX.shp/stands.shp` — stand table (VRI attributes; fields
  `theme0..theme3`, `SPECIES_CD`, `age`, `area` [ha]; EPSG:3005; e.g. TSA 08:
  457,415 stands, 5.19 Mha total). Read attributes only (`read_geometry=False`).
- `output/ws3/tsaXX.are` — model landbase as ws3 area rows
  (`*A <TSA> <theme1> <AU> <stratum> <theme3> <age class> <area ha>`).
- `data/model_input_bundle/au_table.csv` — `au_id` → `stratum_code`
  (`BEC_SPECIES[+SPECIES]`), `si_level` (L/M/H), `canfi_species`.
- `docs/data-and-provenance.rst` — source datasets: VRI 2025
  (`VEG_COMP_LYR_R1_POLY_2025` L1/R1 and `VEG_COMP_VDYP7_INPUT_POLY_AND_LAYER_2025`)
  resolved via `femic data bcdc-resolve` from the BC Data Catalogue; FADM TSA
  boundaries + SiteProd via `external/femic-public-data` (DataLad, Arbutus S3).

Species attribution (femic code, `src/femic/pipeline/vri.py`):

- `stratify_stand()` → `{BEC_zone}_{species combo}`.
- Default: the VRI `SPECIES_CD_1` (leading species); combo mode: top species by
  `SPECIES_PCT_1..6`, joined with "+". Mixed codes such as `AT+SW` mean
  aspen-leading with white spruce secondary.
- The AU table carries the same attribution (`stratum_code`) plus a CANFI code
  (`canfi_map`: AT=1201, PL=204, SX/S=100, SW=105, SB=101, SE=104, BL=304,
  EP=1303, AC=1211, FD=500, ...).

## Records (this analysis)

- `scripts/vri_vs_thlb_composition.py` — joins stand tables → AU table →
  leading species; compares VRI vs THLB shares; computes inclusion by site class.
- `results/cross-tsa/species_composition_vri_vs_thlb.csv` — per unit × scope
  (VRI/THLB) × species: area (ha) and percentage of the scope area.
- `results/cross-tsa/thlb_inclusion_by_si.csv` — per unit × leading species ×
  site class: VRI area, THLB area, inclusion percentage.

Reproduce:

```bash
python scripts/vri_vs_thlb_composition.py \
  --instances-root /srv/shared-data/gep/jupyterhub02-projects/femic/external \
  --out-dir results/cross-tsa
```

## Results

### Five units: VRI area and THLB share

| unit | VRI area (Mha) | THLB (Mha) | THLB/VRI |
|---|---:|---:|---:|
| TSA 08 | 5.19 | 1.40 | 27% |
| TSA 16 | 3.25 | 1.51 | 47% |
| TSA 24 | 6.02 | 3.31 | 55% |
| TSA 40 | 3.04 | 1.02 | 33% |
| TSA 41 | 2.26 | 0.73 | 32% |

### Leading species by scope (% of scope area; area-weighted, pooled by leading species)

| unit | VRI (top 3) | THLB (top 3) |
|---|---|---|
| TSA 08 | black spruce 29.3 · aspen 23.4 · pine 20.4 | **aspen 43.0** · pine 24.0 · white spruce 23.5 |
| TSA 16 | hybrid spruce 33.9 · subalpine fir 29.8 · pine 23.9 | **hybrid spruce 38.4** · pine 30.0 · subalpine fir 20.1 |
| TSA 24 | hybrid spruce 34.3 · subalpine fir 27.3 · pine 22.4 | **hybrid spruce 40.9** · pine 33.3 · subalpine fir 12.2 |
| TSA 40 | black spruce 30.4 · aspen 28.3 · pine 16.3 | **aspen 33.9** · pine 24.1 · white spruce 19.7 |
| TSA 41 | **aspen 26.8** · pine 21.2 · white spruce 14.3 | **aspen 35.2** · pine 20.5 · white spruce 17.0 |

So: **aspen leads the VRI in 1 unit (TSA 41) and the THLB in 3 units
(08/40/41)**; hybrid spruce leads both in TSA 16/24; black spruce leads the VRI
in TSA 08/40 but essentially disappears from the THLB.

### TSA 08 detail: inclusion by site class (pooled by leading species)

| species | VRI (ha) L / M / H | THLB (ha) L / M / H | inclusion L / M / H |
|---|---:|---:|---:|
| black spruce | 453,816 / 471,386 / 596,623 | 7,328 / 10,274 / 20,368 | **1.6% / 2.2% / 3.4%** |
| paper birch | 79,076 / 95,065 / 114,544 | 1,555 / 2,146 / 6,682 | 2.0 / 2.3 / 5.8 |
| spruce spp. (S) | 152,268 / 180,759 / 180,247 | 1,819 / 1,170 / 82,451 | 1.2 / 0.6 / 45.7 |
| lodgepole pine | 475,210 / 279,667 / 301,074 | 43,889 / 126,545 / 165,924 | 9.2 / 45.2 / 55.1 |
| white spruce | 196,005 / 195,086 / 204,125 | 61,611 / 129,178 / 137,863 | 31.4 / 66.2 / 67.5 |
| trembling aspen | 485,121 / 283,386 / 444,601 | 81,498 / 187,328 / 332,922 | 16.8 / 66.1 / 74.9 |
| **all species** | 1,841,497 / 1,505,349 / 1,841,214 | 197,699 / 456,640 / 746,210 | **10.7 / 30.3 / 40.5** |

## Verification performed

1. Recomputed the VRI totals/shares directly from the stand-table attributes
   (`area` × `SPECIES_CD`/AU mapping) — TSA 08 total 5,188,060 ha, black spruce
   29.3%.
2. Recomputed the THLB totals/shares directly from the `.are` rows, mapped
   through `au_table.csv` — TSA 08 total 1,400,549 ha, aspen 43.0%, black spruce
   2.7%.
3. Joined the AU table on `au_id` in both tables; asserts confirm every AU in
   the `.are` and every stand row maps to a stratum (no unmatched rows).
4. Compared per-AU areas: THLB ≤ VRI in every AU (inclusion ratios 0–78%,
   median 19%), i.e. the model landbase is a **subset** of the stand table, not
   a reallocation of areas.
5. Inclusion is monotone in site class (L 10.7% < M 30.3% < H 40.5%) and
   species-specific in the expected direction (black spruce 1.6–3.4%; aspen
   16.8–74.9%) — consistent with a productivity/operability-based THLB.
6. Species labels come from the same VRI-derived stratum codes in both
   populations (`stratify_stand`), and the AU table's CANFI codes match the
   stratum codes (aspen AUs carry 1201, etc.). No label/area mismatch was found.

## Not verified / open items

- **The THLB raster itself was not recomputed.** The manuscript documents the
  filter as "stand mean THLB raster signal ≥ 50%". This analysis verifies the
  *consequence* of the filter (a productivity-selective subset consistent with
  it) but not the raster-level selection per polygon. Definitive test: join the
  THLB raster (FADM/THLB layer, `femic-public-data`) to the VRI polygons and
  recompute inclusion; expected to reproduce the table above.
- **Raw VRI download hashes are not committed** per instance. The source
  datasets are named in `docs/data-and-provenance.rst`; `femic data
  bcdc-resolve` can write a resolve manifest (`write_bcdc_manifest`) but none is
  stored with the instance. Recommendation: commit the resolve manifest for
  each instance.
- The 01a diagnostic plots show the **top strata covering ≥80% of the area**
  (`target_area_coverage = 0.8` in the instance runtime config), so their bars
  sum to ≈0.8, not 1.0 — another reason their percentages are not directly
  comparable to full-inventory shares.

## Implications for the manuscript

- Figure 4 and the species sentence are **correct at the THLB denominator**;
  the figure caption already says "as a percentage of each unit's harvested
  landbase".
- To preempt the reviewer question this note arose from, add one clause to
  Methods/Results: the model landbase is the THLB (27–55% of the VRI area by
  unit), and is productivity-selective (low-site spruce/birch largely excluded;
  aspen/white spruce/pine enriched). Proposed, not yet applied.
- Related fix (2026-10-20): the species figure previously split mixed codes
  into duplicate bars and had rotated labels that bled under the leading bars;
  it now aggregates by leading species, includes the S/EP/AC codes, and uses
  print-size horizontal bars.
