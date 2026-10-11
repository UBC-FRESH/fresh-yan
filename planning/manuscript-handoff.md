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

## Convention history (superseded by the corrected accounting)

The legacy `minimize_emission_loop.ipynb` objective (`cmp_c_ce`) evaluated the ecosystem
term as `fm.inventory(t, 'net_emission', age=d['_age'], dtype_keys=[d['_dtk']])`. Under
ws3 ≥ 1.0.5 (end-of-period inventory reporting), that call returns **zero for every
lookup** (909,980/909,980 observed during problem compilation), silently dropping the
ecosystem-emission term. The published numbers were reproduced under current ws3 by
computing the start-of-period values directly (`fresh_yan.hwp`), and the natural
end-of-period adaptation did not reproduce them either.

Both are now superseded: the corrected (v2) accounting (`src/fresh_yan/accounting.py`)
uses the standard end-of-period `inventory()` with the harvest-consistent curves, the
products-only HWP ledger split 50/50 (manuscript methods), and exact per-period decay.
The trade-off/sensitivity records therefore do **not** reproduce the published numbers by
design; see `planning/curve-generation-and-reset-findings.md`.

## Draft methods text (corrected curves and accounting)

Replacement for the carbon-yield-curve paragraph (manuscript line 257) and additions for
the limitation, to apply in the post-grid manuscript pass:

> Carbon yield curves were created following \citep{neilson2008optimal}, integrating
> carbon into the \ac{SFMM} alongside the timber yield curves. Forest carbon was modelled
> with libCBM, the open-source implementation of \ac{CBM-CFS3} \citep{KURZ2009480},
> across 21 carbon pools (10 biomass and 11 \ac{DOM}) and 52 carbon fluxes. For each
> analysis unit, a one-hectare stand was simulated on its natural trajectory to the
> model's typical harvest age (120 years; the area-weighted median harvest age measured
> under the even-flow scenarios), at which point a clearcut harvest event transferred the
> carbon pools according to CBM's disturbance matrix (merchantable carbon removed;
> slash and dead roots to the dead organic matter pools) and the stand regrew on its
> managed yield curve. Repeating the harvest at the rotation age until the dead organic
> matter pools reached their cycle equilibrium, and extracting the post-harvest
> trajectory, yielded the managed carbon yield curves; the natural curves are the
> no-management trajectories. The projections were aggregated into biomass,
> merchantable, \ac{DOM}, and ecosystem stock curves and one net emission flux curve.
>
> Dead organic matter initialization in \ac{CBM} is known to produce upward-biased
> initial pools (deterministic disturbance-interval spin-up relative to stochastic
> disturbance; \citealp{boisvenue2022managing, metsaranta2017} and systematic
> initialization errors in \citealp{oberpriller2021}), and the post-harvest reset
> inherits that bias. This study therefore generates the managed curves by simulating
> the harvest itself, so that post-harvest carbon states are conservation-consistent
> with the harvested stand's pre-harvest state; the residual difference between
> first-rotation and steady-state harvest histories is about 1% of landscape carbon.

Also to state in the methods: the accounting is a stock-difference formulation
(`E_sys(t) = [E(t)-E(t+1)] + [H(t)-H(t+1)] - sub(t)`, exact carbon conservation) with a
products-only HWP ledger and the manuscript's 50/50 paper/solid-wood split.

## Open questions for the authors

1. **Trade-off curves (Fig. 12).** The curve labels are (displacement factor, half-life)
   pairs (`1.0_30`, `1.2_50`, `1.5_60`, `1.2_40`, `1.2_30`, `1.5_50`, `0.0_30`,
   `1.5_55`, `0.5_30`), suggesting a harvest-volume ε-constraint sweep per pair (points
   = emission-minimizing solves under a sweep of volume targets). No committed code in
   `msc_walter_yan` generates this figure. Options: recover the original generator
   (thesis/Overleaf) or reconstruct the sweep (needs the volume-target grid used). Any
   reconstruction must use the convention choice above.
2. **HWP allocation in the sensitivity experiments (resolved).** The legacy loop set
   `proportion_solid_wood = 1.0` ("all harvested wood is made into a single type of HWP
   to simplify the experiment"), contradicting the manuscript's Methods ("the utilized
   fibre was divided into two equal categories of HWPs: paper and solid wood products").
   The corrected grid now follows the Methods: 50/50 split, paper half-life 2 yr,
   solid-wood half-life = the grid parameter, substitution on the solid-wood inflow only.
3. **Max-harvest carbon comparison (Figs. 10–11).** The legacy generator is in
   `generate_c_curves_tsa24.ipynb` cells 43–53 (compile events from the base scenario
   schedule, run libCBM, compare). Reconstruct as `fresh-yan max-harvest-carbon`.
