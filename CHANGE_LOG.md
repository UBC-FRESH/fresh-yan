# 2026-10-12 — Femic curve generation: `cc` acodes + transition-graph classification (#3)

- Fixed three hardcoded `"harvest"` acodes that broke (or silently zeroed) the femic
  `cc` models: `curves._clearcut_event` now writes the model's stand-replacing action
  as the SIT `disturbance_type` id (was `"harvest"`, undefined in the `cc`/`fire`
  mapping, so every managed curve crashed); `accounting._harvest_area` and
  `_period_inflows` identify harvest actions via the model's `is_harvest` flags
  (was a fixed acode, silently zeroing HWP inflows); `scenario.compile_scenario` takes
  `harvest_acode` (was zeroing the harvested-area/volume columns for `cc` models).
- Curve dtype classification now follows the model's transition graph
  (`curves._regeneration_sources`): every harvest-transition target gets a
  simulated-clearcut (cycle) curve, with the natural parent as the pre-harvest source in
  the legacy sections and the dtype itself in models that regenerate in place (femic:
  all 27 THLB dtypes, including 11 natural-curve targets that previously got spun-up
  curves and with them the post-reset DOM inconsistency). Legacy regeneration nodes and
  parents are unchanged (regenerated managed dtype reproduces the committed pickle with
  max abs diff 0).
- Regression tests: `tests/test_curves.py` (event id follows the acode),
  `tests/test_accounting.py` (harvest area follows `is_harvest`),
  `tests/test_model.py` (legacy regeneration graph).
- All five femic instances materialized from the new Arbutus cloud and updated to the
  p113_5 "campaign config" re-export (THLB-filtered `.are`, period-age-fixed `.yld`,
  reference baselines in `evidence/campaign_baseline_2026-10-12/`); pins and notes in
  `planning/multi-tsa-extension.md`. Curve regeneration for the five-TSA campaign runs
  on the fixed path.

# 2026-10-12 — Multi-TSA parameterization + femic section support (#3)

- The pipeline runs per management unit: `--tsa/--model-name/--model-path/--curves-dir`
  across the CLI and FreshForge provider nodes; `curves/<tsa>` and `results/<tsa>/...`
  defaults; a `tsa` provenance column on records.
- Femic `export ws3-sections` exports are consumable directly: `--section-units periods`
  applies ws3's period-to-years conversion on import (`.are` ages, `.act` timing,
  `.yld` ages), and `--harvest-acode` selects the stand-replacing action (`harvest`
  for the legacy TSA 24 sections; `cc` for femic exports).
- Curve generation writes `provenance.json`; provenance is captured before the
  generated files are written so `fy_commit` is not polluted by the outputs themselves.
- Verified against the public TSA29 femic export and the wbi-birds `tsa24_clipped`
  fixture; findings and the five-TSA campaign checklist in
  `planning/multi-tsa-extension.md`.

# 2026-10-11 — Corrected trade-off grid records + adversarial audit (#1)

- Generated the full corrected trade-off grid: 5,000 scenarios (25 displacement
  factors x 200 solid-wood half-lives), emission-minimizing LP on the v2 accounting and
  rotation-cycle curves; HiGHS, 48 workers, 2 h 46 min. Records in
  `results/tradeoff_grid/` (harvest/stock/emission trajectories + summary, provenance
  on all files); sensitivity figures regenerated (`results/sensitivity/3d.pdf`,
  `xyz.pdf`; the 3D filename now matches the manuscript and pipeline artifact).
- Pre-run adversarial audit (independent agent) of the corrected accounting: PASS — no
  counterexample. LP objective == -(tracker total) to ~2e-15 relative on all spot
  scenarios (target 1,586,066,278.97 reproduced exactly; 119/119 per-path coefficients
  of a real tract match an independent telescoping); DOM inside the ecosystem term;
  exact 2**(-10/hl); 50/50 split with inflow-only substitution; boundary scenarios
  (hl 1/2/200 x df 0/2.4) all optimal and finite. Post-run checks: 5,000 rows,
  25 x 200 unique, no NaN/inf; spot cells match to float precision (hl=100/df=1.5:
  530,250,376.82 m3 utilized volume, -1,586,066,278.9708 tCO2).
- Audit follow-ups: added the LP-integration test for the z <-> tracker invariant
  (`tests/test_accounting.py`); provenance helpers now run git from the repository root
  and flag `src/`, `curves/`, and `data/` changes; lint clean; planning docs updated
  with the current reset-residual numbers (base +1.35 MtC; worst spot -20.19 MtC =
  1.63% of landscape C).

# 2026-10-11 — FreshForge pipeline, record fixes, and validation notes (#1)

- Added `src/fresh_yan/providers.py`: a FreshForge provider (entry point
  `freshforge.providers` -> `fresh_yan.pipeline`) exposing `generate_curves`,
  `no_harvest`, `base_scenario`, `trade_off_grid`, and `sensitivity_figures` nodes, so
  the full modelling pipeline runs as a reproducible FreshForge workflow
  (`workflows/pipeline.yaml`; record-only regeneration in `workflows/records.yaml`;
  per-case grid expansion example in `workflows/tradeoff_matrix.yaml`). The no-harvest
  and base-scenario records were regenerated through the workflow.
- Fixed the base scenario records: the carbon columns (`ocp`/`ocf`) were silently zero
  because the curves were never plugged into the model in `base_scenario.generate`.
- Added `tests/test_accounting.py` (telescoped conservation identity, no-harvest path
  coefficient, half-life monotonicity) and a cohort-level validation note in
  `planning/curve-generation-and-reset-findings.md` (biomass exact vs libCBM; DOM
  residual documented).

# 2026-10-11 — HWP allocation corrected to the manuscript's 50/50 split (#1)

- The legacy loop silently used a single solid-wood product type
  (`proportion_solid_wood = 1.0`), contradicting the manuscript methods ("the utilized
  fibre was divided into two equal categories of HWPs: paper and solid wood products").
  `accounting.py` and `tradeoff_grid.py` now split the HWP inflow 50/50 (paper half-life
  2 yr, solid-wood = grid half-life; substitution on the solid-wood inflow only).
- Re-verified: LP objective equals exactly the negative of the reported tracker total;
  telescoped conservation identity closes to 0.0.

# 2026-10-11 — Harvest-consistent curves and corrected carbon accounting (#1)

- **Managed carbon curves are now generated by simulating the clearcut** in libCBM
  (`src/fresh_yan/curves.py`): the stand grows on its natural trajectory to the model's
  typical rotation age (120; measured area-weighted medians 110 base / 120-125
  trade-off), a harvest event transfers the pools per CBM's disturbance matrix (age-0
  conservation-consistent by construction), and the stand regrows on the managed yield
  curve. The official curves in `curves/` use the rotation-cycle equilibrium
  (`mode='cycle'`); `merch` (merchantable-stem carbon) is added as the HWP inflow source.
  Aggregate phantom carbon (reset error x harvested area) over the base-scenario
  schedule: +96.6 MtC with the old spun-up curves, +1.35 MtC with the cycle curves
  (updated 2026-10-11 on the regenerated base records).
- **Corrected (v2) accounting** (`src/fresh_yan/accounting.py`): end-of-period
  stock-difference ecosystem term, products-only HWP ledger (inflow = curve merch x
  util_rate, survival = 2**(-10/hl)), substitution = df x inflow x credit. The LP
  objective equals exactly the negative of the reported tracker total, and the
  telescoped conservation identity closes to 0.0.
- The trade-off grid (`trade-off-grid`) now uses the corrected accounting and the
  corrected curves.
- Fixed the `'total_emissions'` -> `'total_emission'` typo in `compile_scenario`
  (the `ocf` column silently returned zero).
- Findings and method: `planning/curve-generation-and-reset-findings.md`.

# 2026-10-11 — Trade-off grid command and convention fix (P3)

- Added `fresh-yan trade-off-grid` (`src/fresh_yan/tradeoff_grid.py`):
  emission-minimizing scenarios over (displacement factor, solid-wood half-life) with HWP
  decay and substitution, 5% even-flow constraints, parallel workers, and long-format
  records (harvest/stock/emission trajectories + per-scenario summary) with provenance.
- Added `src/fresh_yan/hwp.py` (HWP coefficient functions and trackers extracted from
  `msc_walter_yan/util.py`).
- **Convention fix (verified).** The legacy `cmp_c_ce` used
  `fm.inventory(..., age=d['_age'])`, which under ws3 >= 1.0.5 (end-of-period inventory)
  silently returns zero, dropping the ecosystem-emission term (full harvest everywhere).
  The coefficient functions and trackers now compute the start-of-period values directly
  (`_legacy_inventory_lookup` / `_legacy_inventory_total`), reproducing the published
  experiments: verified against ws3 1.0.0 for (df=1.0, hl=30) -> 0.084e9 m3 and
  (df=0.5, hl=200) -> 0.173e9 m3, matched exactly under current ws3. The natural
  end-of-period adaptation (`age + period_length`) does not reproduce the published
  numbers; see `planning/manuscript-handoff.md` for the evidence and the open author
  decision.
- Added `scripts/analyze_sensitivity.py` (3D + orthographic figures from the summary
  record).
- Added `planning/manuscript-handoff.md`: figure/table-to-record map and open questions.

# 2026-10-11 — Base scenario records (P2)

- Added `fresh-yan base-scenario` (`src/fresh_yan/base_scenario.py`): maximizes even-flow
  harvest volume over the 200-year horizon and records per-period harvest area/volume,
  growing stock, ecosystem carbon, and emissions; the solver is recorded in provenance.
- Added `src/fresh_yan/scenario.py`: ws3 optimization helpers (objective/constraint
  coefficient functions, `gen_scenario`, `compile_scenario`, `plot_scenario`) extracted
  from `msc_walter_yan/util.py` and cleaned to pass lint.
- Records: `results/base_scenario/base_scenario.csv` + figure. Harvest area
  368,874-407,702 ha/period; harvest volume 7.45-8.24 x 10^7 m3/period; growing stock
  decreases 7.21 x 10^8 -> 4.68 x 10^8 m3 (the manuscript's reported ranges reproduce).
- CI: the validated dependency pins require Python >= 3.12, so `requires-python` and the
  CI matrix are now 3.12-only (the 3.11 leg failed on `numpy==2.5.4`).

# 2026-10-11 — Repository scaffold (P1)

- Created `UBC-FRESH/fresh-yan` and the initial package scaffold: `src/fresh_yan/`
  (model construction, extracted libCBM utilities, no-harvest record generation, CLI),
  `data/` + `curves/` inputs, `tests/`, CI, `README.md`, `AGENTS.md`, `ROADMAP.md`,
  `CHANGE_LOG.md`.
- Pipeline extracted from `UBC-FRESH/msc_walter_yan` (`util.py` and
  `generate_c_curves_tsa24.ipynb`). `ws3` is pinned to commit `a267f02`, which carries
  the `to_cbm_sit` fix (UBC-FRESH/ws3#155).
- Generated the first tracked record set, `results/no_harvest/*`, via
  `fresh-yan no-harvest`. Values reproduce the legacy committed outputs exactly; the
  records add provenance columns (`fy_commit`, `fy_version`, `ws3_version`,
  `libcbm_version`).
