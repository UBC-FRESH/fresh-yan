# Manuscript hand-off

Maps every figure and table in the CJFR manuscript (reframed, five-TSA campaign) to its
source record and regeneration command in this package.

Status: **OK** (record exists) · **RUNNING** (record being generated) · **TODO**
(record/command to be built) · **MISSING** (no known generator; author input needed).

| Manuscript item | Source record | Regenerate with | Status |
|---|---|---|---|
| Fig. 1 — modeling framework (schematic) | drawn manually | — | n/a |
| Fig. 2 — study area (five-unit map) | `results/cross-tsa/figures/five_tsa_map.pdf` | `scripts/five_tsa_figures.py` | OK |
| Fig. 3 — age structure, five units | `results/cross-tsa/figures/five_unit_age.pdf` | `scripts/five_tsa_figures.py` | OK |
| Fig. 4 — species composition, five units | `results/cross-tsa/figures/five_unit_species.pdf` | `scripts/five_tsa_figures.py` | OK |
| Table — units (THLB, dtypes, initial C, base, flip) | `results/cross-tsa/five_tsa_attributes.csv` + `cross_tsa_thresholds.csv` | `scripts/five_tsa_figures.py` + `scripts/cross_tsa_analysis.py` | OK |
| Fig. 5 — base-scenario area/volume/stock (TSA 24) | `results/femic-tsa24/base_scenario/` | `fresh-yan base-scenario` (femic args) | OK |
| Table — no-harvest stocks vs libCBM (TSA 24) | `results/femic-tsa24/no_harvest/no_harvest_pct_diff_summary.csv` (+ cbm/ws3) | `fresh-yan no-harvest` (femic args) | OK |
| Fig. 6 — no-harvest stocks vs libCBM | `results/femic-tsa24/no_harvest/no_harvest_carbon_stock_whole_st.pdf` | same | OK |
| Fig. 7 — no-harvest net emissions vs libCBM | `results/femic-tsa24/no_harvest/no_harvest_carbon_dynamics_individual_st.pdf` | same | OK |
| Figs. 8–9 — max-harvest stocks/emissions vs libCBM | legacy import (pre-correction); no fresh-yan record | `fresh-yan max-harvest-carbon` (TODO; blocked on the ws3<->libCBM managed-stand age offset) | MISSING (legacy, scoped in text) |
| Fig. 10 — 3D sensitivity map (TSA 24) | `results/femic-tsa24/tradeoff_grid/tradeoff_grid_summary.csv` | `fresh-yan trade-off-grid` + `scripts/analyze_sensitivity.py` | OK |
| Fig. 11 — orthographic views | same summary | same | OK |
| Fig. 12 — cross-TSA flip thresholds | `results/cross-tsa/cross_tsa_thresholds.csv` | `scripts/cross_tsa_analysis.py` | OK |
| Reset-residual record (curve QA; manuscript bound) | `results/cross-tsa/reset_residuals_tsa*.csv` | `scripts/reset_residuals.py` | RUNNING |
| Structural robustness spot-checks (limitations) | `results/robustness/robustness_results.csv` | `scripts/robustness_checks.py` | RUNNING |
| Uncertainty overlay figure (literature ranges vs threshold) | `planning/df_hl_ranges.csv` + thresholds | not yet built | TODO |

The removed legacy items (bi-objective trade-off curves, Fig. 12-old; unmanaged/managed
split figures) are superseded and no longer referenced by the manuscript.

## Convention history (superseded by the corrected accounting)

The legacy `minimize_emission_loop.ipynb` objective (`cmp_c_ce`) evaluated the ecosystem
term as `fm.inventory(t, 'net_emission', ...)`, which under ws3 >= 1.0.5 returns zero for
every lookup, silently dropping the ecosystem term; the published numbers were
reproduced with start-of-period values (`fresh_yan.hwp`), now itself superseded. The
corrected (v2) accounting (`src/fresh_yan/accounting.py`) uses the standard
end-of-period `inventory()` with the harvest-consistent curves, the products-only HWP
ledger split 50/50, and exact per-period decay. The corrected curves/accounting are
implemented in the manuscript methods; the legacy `hwp.py` carries a superseded banner.

## Open items for the authors

1. **Max-harvest carbon comparison (Figs. 8-9).** Still no corrected record: the
   harvested-landscape cross-validation is blocked on the ws3<->libCBM managed-stand
   age offset. The manuscript scopes these figures as pre-correction and lists the
   corrected validation as future work.
2. **Uncertainty overlay figure.** The literature-range argument (df/half-life ranges
   vs the threshold surface) is textual only; a figure would strengthen it.
   `planning/df_hl_ranges.csv` in the manuscript repository has the range data.
3. **Reset-residual bound.** The five-unit record (running) will replace the
   legacy-calibrated "up to about 1.6% of landscape carbon" statement with a per-unit
   phantom-carbon bound.
