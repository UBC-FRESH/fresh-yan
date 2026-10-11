# Manuscript hand-off

Maps every figure and table in the CJFR manuscript to its source record and regeneration
command in this package.

Status: **OK** (record exists) · **PENDING** (record command exists, full grid not yet
run) · **TODO** (record/command to be built) · **MISSING** (no known generator; author
input needed).

| Manuscript item | Source record | Regenerate with | Status |
|---|---|---|---|
| Fig. 1 — modeling framework (schematic) | drawn manually (no record) | — | n/a |
| Fig. 2 — study area (TSA 24 map) | external GIS map | — | n/a |
| Fig. 3–4 — species composition, unmanaged / managed | TSA 24 inventory summary | `fresh-yan inventory-figures` (TODO) | TODO |
| Fig. 5–6 — age structure, unmanaged / managed | TSA 24 inventory summary | `fresh-yan inventory-figures` (TODO) | TODO |
| Fig. 7 — max-harvest volume / area / stock | `results/base_scenario/base_scenario.csv` | `fresh-yan base-scenario` | OK |
| Table 1 — no-harvest carbon stocks vs libCBM | `results/no_harvest/no_harvest_pct_diff_summary.csv` (+ cbm/ws3) | `fresh-yan no-harvest` | OK |
| Fig. 8 — no-harvest carbon stocks vs libCBM | `results/no_harvest/no_harvest_carbon_stock_whole_st.pdf` | `fresh-yan no-harvest` | OK |
| Fig. 9 — no-harvest net emissions vs libCBM | `results/no_harvest/no_harvest_carbon_dynamics_individual_st.pdf` | `fresh-yan no-harvest` | OK |
| Fig. 10 — max-harvest carbon stocks vs libCBM | max-harvest carbon comparison record | `fresh-yan max-harvest-carbon` (TODO) | TODO |
| Fig. 11 — max-harvest emissions vs libCBM | max-harvest carbon comparison record | `fresh-yan max-harvest-carbon` (TODO) | TODO |
| Fig. 12 — trade-off curves (curves named `df_hl`) | bi-objective ε-constraint sweep record | generator unknown | **MISSING** |
| Fig. 13 — 3D sensitivity map | `results/tradeoff_grid/tradeoff_grid_summary.csv` | `fresh-yan trade-off-grid` + `scripts/analyze_sensitivity.py` | PENDING |
| Fig. 14 — orthographic views | same summary | same | PENDING |

## Convention finding: the legacy loop code vs ws3 ≥ 1.0.5 (verified 2026-10-11)

The legacy `minimize_emission_loop.ipynb` objective (`cmp_c_ce`) evaluated the ecosystem
term as `fm.inventory(t, 'net_emission', age=d['_age'], dtype_keys=[d['_dtk']])`. Under
ws3 ≥ 1.0.5 (end-of-period inventory reporting), that call returns **zero for every
lookup** (909,980/909,980 observed during problem compilation), silently dropping the
ecosystem-emission term; the reproduced scenario then harvests everywhere (1.55 × 10⁹ m³
even at df = 0.5, hl = 200). Under ws3 1.0.0 the same code returns nonzero and reproduces
the manuscript's behaviour (0.084 × 10⁹ m³ at df = 1.0, hl = 30; 0.173 × 10⁹ m³ at
df = 0.5, hl = 200 — low harvest, consistent with the manuscript's description).

The natural end-of-period adaptation (`age + period_length`) does **not** reproduce the
published results (1.30 × 10⁹ / 1.33 × 10⁹ m³): the one-period shift moves the regime
boundary. `fresh_yan.hwp` therefore computes the start-of-period values directly
(`_legacy_inventory_lookup` / `_legacy_inventory_total`), which reproduces the published
numbers exactly under current ws3 (verified).

**Author decision:** keep reproducing the published (start-of-period) experiments, or
regenerate the trade-off/sensitivity figures under the end-of-period convention and
update the manuscript accordingly.

## Open questions for the authors

1. **Trade-off curves (Fig. 12).** The curve labels are (displacement factor, half-life)
   pairs (`1.0_30`, `1.2_50`, `1.5_60`, `1.2_40`, `1.2_30`, `1.5_50`, `0.0_30`,
   `1.5_55`, `0.5_30`), suggesting a harvest-volume ε-constraint sweep per pair (points
   = emission-minimizing solves under a sweep of volume targets). No committed code in
   `msc_walter_yan` generates this figure. Options: recover the original generator
   (thesis/Overleaf) or reconstruct the sweep (needs the volume-target grid used). Any
   reconstruction must use the convention choice above.
2. **HWP allocation in the sensitivity experiments.** The legacy loop sets
   `proportion_solid_wood = 1.0` ("all harvested wood is made into a single type of HWP
   to simplify the experiment"), while the manuscript's Methods describe a 50/50
   paper/solid-wood split. The grid records here follow the legacy loop (proportion 1.0);
   confirm whether the manuscript's sensitivity section should state this simplification.
3. **Max-harvest carbon comparison (Figs. 10–11).** The legacy generator is in
   `generate_c_curves_tsa24.ipynb` cells 43–53 (compile events from the base scenario
   schedule, run libCBM, compare). Reconstruct as `fresh-yan max-harvest-carbon`.
