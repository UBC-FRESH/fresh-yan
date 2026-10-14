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
| Max-harvest stocks/emissions vs libCBM (old Figs. 8–9, removed) | — | — | Removed from the manuscript; harvested-landscape validation scoped as future work (ws3<->libCBM managed-stand age offset open) |
| Figs. 8 — five-unit optimization surface (3D + orthographic views) | `results/femic-tsa*/tradeoff_grid/tradeoff_grid_summary.csv` + `results/cross-tsa/figures/five_tsa_surfaces.pdf` | `scripts/tsa_campaign_figures.py` | OK |
| Fig. 9 — flip mid-point and 10–90% bands by half-life | `results/cross-tsa/cross_tsa_thresholds.pdf` (+ `.csv`) | `scripts/cross_tsa_analysis.py` | OK |
| Reset-residual record (curve QA; manuscript bound) | `results/cross-tsa/reset_residuals_tsa*.csv` | `scripts/reset_residuals.py` | OK |
| Structural robustness spot-checks (limitations) | `results/femic-tsa24/robustness/robustness_results.csv` | `scripts/robustness_checks.py` (femic args) | OK |
| Fig. 10 — uncertainty overlay (literature ranges vs thresholds) | `results/cross-tsa/figures/tsa_overlay.pdf` | `scripts/tsa_campaign_figures.py` | OK |

The removed legacy items (bi-objective trade-off curves; unmanaged/managed split figures;
the max-harvest comparison) are superseded and no longer referenced by the manuscript.

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
2. **Uncertainty overlay figure.** Built: `results/cross-tsa/figures/tsa_overlay.pdf`
   (`scripts/tsa_campaign_figures.py`; range data: `planning/df_hl_ranges.csv` in the
   manuscript repository).
3. **Reset-residual bound.** Complete: the five-unit record bounds the first-rotation
   residual at 2.3% of initial ecosystem carbon in the worst unit (TSA 24: 1.6%).
