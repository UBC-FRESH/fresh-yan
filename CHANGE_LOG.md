# 2026-10-20 — Evidence standard + VRI/THLB species reconciliation

- Amended `AGENTS.md`: new "Evidence standard — no hand-waving, ever" section
  (reproduce before explaining; name denominators/units; falsifiable checks;
  explicit unverified status; figures must be opened and checked).
- Added `planning/species-composition-vri-vs-thlb.md`: reconciliation of the
  full-VRI species composition (01a diagnostic population) with the model
  landbase (THLB) composition — the source of the "aspen leads 3 of 5"
  question, with the TSA 08 site-class inclusion detail and an explicit list of
  unverified items (THLB raster not re-derived; no committed BCDC resolve
  manifest).
- Added `scripts/vri_vs_thlb_composition.py` +
  `results/cross-tsa/species_composition_vri_vs_thlb.csv` and
  `results/cross-tsa/thlb_inclusion_by_si.csv`.

# 2026-10-20 - Species-composition figure correction

- The five-unit species figure aggregated by raw stratum token, so mixed strata
  ("at+sw") appeared as duplicate bars with the same label, unmapped BC codes
  ("s", "ep", "ac") were shown as raw tokens, and the rotated right-aligned tick
  labels bled under the leading bars (the figure read as aspen-led in every unit).
- Now: area is aggregated by the leading species (first token of each mixed
  stratum), the full code map covers S/EP/AC, and the panels use horizontal bars
  authored at print width (6.9 in) with legible label sizes.
- Underlying leading species by area: TSA 08 aspen 43%, TSA 16 hybrid spruce 38%,
  TSA 24 hybrid spruce 41%, TSA 40 aspen 34%, TSA 41 aspen 35%.

# 2026-10-14 — Femic structural robustness records

- Parameterized `scripts/robustness_checks.py` for campaign models (`--tsa`,
  `--model-name`, `--model-path`, `--curves-dir`, `--section-units`,
  `--harvest-acode`; previously legacy-only with the `harvest` action code hardcoded).
- Added `results/femic-tsa24/robustness/robustness_results.csv`: six one-at-a-time
  structural variants (even-flow width 5/15/none; allocation 50/50 vs solid-only;
  horizon 15/20/25 periods) x three reference cells (hl=100; df=0.5/1.0/2.0), 18
  solves. Low-displacement suppression persists in every variant (2.9-10.3x less
  volume at df=0.5 than df=2.0); across-variant volume range at a cell 3.6-14x; net
  emission effect within -16%..+18% of the baseline except the all-solid allocation
  (+80% at df=2.0).
- Added `planning/cjfr-remediation-status.md` (rejection-sim worklist status and
  open author decisions) and linked it from the handoff.
- Synced `planning/manuscript-handoff.md`, `README.md` and
  `results/experiments/REPRODUCIBILITY.md`; the manuscript limitations now report the
  robustness magnitudes.
- Added `scripts/stand_validation.py` + `results/femic-tsa24/stand_validation/`
  (stand-level harvested-cycle check: curve layer vs direct libCBM over three
  rotations; biomass exact, DOM/ecosystem converging from 3.7%/4.9% mean abs in the
  first rotation to 1.4%/1.8% by the third).
- Added `scripts/evidence_decision_analysis.py` +
  `results/cross-tsa/decision_under_evidence.csv` (optimal harvest as a share of
  base across published displacement-factor ranges; TSA 24 spans 1-76% over the
  Leskinen 95% range; Smyth et al. 2017 general vs building-only cases: 3-7% vs
  36-71%).
- Manuscript PR #7 (author side): Gregory Paradis first author with the full CRediT
  role set; NSERC Discovery Grant RGPIN-2023-04197 funding statement.
- Added `scripts/threshold_attributes.py` + `results/cross-tsa/threshold_attributes.csv`
  (and correlations): the flip mid-point ranks exactly with the young-stand share
  (rho = 1.0 at hl=100); size, carbon and density do not order it.
- Added `scripts/df_convention.py` + `results/cross-tsa/df_convention_mapping.csv`:
  effective-credit axis (0.425x df per tC of harvested merchantable carbon).
- Regenerated the cross-TSA derived records (thresholds, grid maxima, reference cells,
  threshold figure) from a clean pin: values identical, provenance only
  (b492c7c+dirty -> 2f7ce49).
- Fixed the no-harvest comparison sampling (`compare_ws3_libcbm`: end-of-period
  pairing, libCBM timestep 10p, replacing the start-of-period sample that shifted
  libCBM one period earlier) and regenerated the five units' no-harvest records from
  the fixed pin 501db3a; a single-panel net-emissions figure was added. Stock
  agreement is now 0.2-5.4% period-mean (was 0.9-6.2%); fluxes show no sign flips.

# 2026-10-13 — Five-TSA grid wave complete + cross-TSA flip analysis (#3)

- All five emission-minimizing grids finished (identical 25 x 200, HiGHS; 5,000 cells
  each; 8-14 workers per TSA, ~12 h wall on the shared box). Validation: unique
  (df, hl) keys, no NaNs, no cell over the base scenario, cross-file emission sums
  exact, provenance `1f50ce4`. Records commit `4eb3e71` (~44 MB per TSA).
- Cross-TSA flip characterization (`scripts/cross_tsa_analysis.py`; `results/cross-tsa/`,
  commit `40d115d`): df50(hl=100) spans 0.95 (tsa08) to 1.61 (tsa24); grid maxima
  0.57-0.78 of each unit's base-scenario volume. tsa16 is the outlier: 1,446/5,000
  cells are full-cessation optima (zero harvest) for df <= ~0.5, sharing the exact
  no-harvest emission (-3.856e8 tCO2) - the strongest form of the flip in the set;
  tsa08 never fully stops (min 25.3M m3).

# 2026-10-13 — Adversarial audit remediation (code + manuscript)

- Third adversarial audit (`/tmp/opencode/audit_code_manuscript.md`) re-solved four
  committed grid cells end-to-end (exact harvest; ~1e-16 relative emission agreement)
  and reproduced all cross-TSA numbers, the ledger identity, and the 25,000-cell QA;
  it found packaging defects, all now fixed:
  - manuscript: fatal preamble corruption (duplicated AI declaration) removed - build
    is clean (0 errors); "(CITATION)" placeholders replaced with real citations;
    units-table "Initial C" now traceable (`results/cross-tsa/five_tsa_attributes.csv`,
    period-0 inventory 353.9/296.6/703.4/223.0/160.9 MtC); no-harvest convergence
    wording corrected to the actual per-unit matrix; df50 range, harvested-area ratio,
    age-structure shares, conclusion range wording, highlights, and legacy scoping of
    the max-harvest comparison fixed; `leskinen2018` added to the bibliography.
  - fresh-yan: `scripts/five_tsa_figures.py` writes the attributes record (curves
    plugged - the silent-zero class caught in the audit); `scripts/cross_tsa_analysis.py`
    outputs carry provenance; new `scripts/reset_residuals.py` (per-unit residual +
    phantom-carbon record; running); records-tests cover the femic campaign; `hwp.py`
    carries a superseded banner; `REPRODUCIBILITY.md` rewritten with the five-TSA
    commands and current numbers; `manuscript-handoff.md` refreshed.
- Pending: reset-residual and robustness records (background), the two manuscript
  sentences that cite them, and PR merges before the Zenodo release (main is stale).

# 2026-10-12 — Femic curve generation: `cc` acodes + transition-graph classification (#3)

- Fixed three hardcoded `"harvest"` acodes that broke (or silently zeroed) the femic
  `cc` models: `curves._clearcut_event` now writes the model's stand-replacing action
  as the SIT `disturbance_type` id (was `"harvest"`, undefined in the `cc`/`fire`
  mapping, so every managed curve crashed); `accounting._harvest_area` and
  `_period_inflows` identify harvest actions via the model's `is_harvest` flags
  (was a fixed acode, silently zeroing HWP inflows); `scenario.compile_scenario` takes
  `harvest_acode` (was zeroing the harvested-area/volume columns for `cc` models).
- `model.to_cbm_sit` clamps tiny negative yield artifacts from ws3's SIT conversion
  to 0 (the TSA 41 export hits -8.9e-16 at an age class and fails libCBM's parser);
  genuinely negative yields raise instead of being silently clamped.
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
- Generated the campaign carbon curves for all five instances (`curves/femic-tsa<code>/`;
  32/49/27/30/38 regeneration-target dtypes; provenance pinned to `b4bad00`/`df83ab6`).
  QA and the tsa08 slow-pool residual note in `planning/multi-tsa-extension.md`.
- `base_scenario.solve` now threads `harvest_acode` into `gen_scenario` (the default
  `harvest` silently zeroed the base-scenario LP on `cc` models - caught by the
  zero-harvest first run); `gen_scenario` raises on an acode absent from the model.
  The five femic base scenarios were regenerated with nonzero harvest.
- `cbm.plugin_c_curves` now mirrors ws3's yield-mask matching instead of requiring the
  legacy `('?','?',AU,'?',curve)` mask: femic `export ws3-sections` sections register
  yields under the full dtype key, so the old lookup silently skipped every dtype,
  zeroing all carbon columns and the grid objective (caught in the tsa24 grid pilot -
  5,000 degenerate cells). Plugged curves verified against the pickles; regression
  test with the femic-style fixture; base records and grids regenerated.

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
