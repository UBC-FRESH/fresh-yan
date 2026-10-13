# ws3 → libCBM harvested-landscape replay: conventions pinned (2026-10-13)

Investigation of the "managed-stand age offset" that blocked the harvested-landscape
cross-validation. Outcome: the blocker was accounting bookkeeping, now pinned;
the replay harness is faithful and only needs packaging into records.

## Verified conventions

1. **Event year**: `year = 10 * (period - 1) + 1` (the first year of the scheduled
   period).
2. **First-rotation age window**: `min = max = inventory_age + year - 1`; with the
   year mapping above this equals **the schedule's own cut age** `a`
   (verified: stand A0=210 fires at y=1/bound 210, y=11/bound 220, y=21/bound 230).
3. **Managed-stand window**: after a reset event at year `y1`, a stand's libCBM age at
   year `y2` is `y2 - y1` (verified by two-cut experiments: reset at 81 -> bounds 80 at
   y=161 and 120 at y=201 fire exactly). With ws3 aging managed cohorts 10 yr/period,
   this also equals the schedule's cut age for regenerated cohorts.
4. **`sit_transitions` must be emptied in the replay input.** libCBM ingests the
   model's transition table and generates spontaneous harvest handling from it, firing
   stands at off-schedule years on wrong cohorts (the historical "age-offset"
   confound). With `sit_transitions` emptied, every fire lands on its scheduled year.
5. **Replay fidelity**: with 1-4 applied, the period-1 area ledger closes to 99.91%
   (residual = LP area slivers on 30 rows, 309 ha of 343,356 ha).
6. **Basis note**: CBM's disturbance merch production will not equal
   `area x curve_merch[age]` for *initial* stands (~0.85 of it at TSA 24 t=1), because
   ws3's books use the cycle (regeneration-target) curve for initial stands while
   libCBM carries the spun-up stand states. This is the model's documented initial-stand
   convention, not a replay defect; the validation therefore compares per-period
   **stocks** (ecosystem/biomass/DOM) against the libCBM run, as in the no-harvest
   comparison.

## Derived decomposition (2026-10-13, later)

Key-agnostic cohort matching (libCBM identifiers paired to ws3 cohorts by exact area
within dtype; libCBM per-identifier areas read from ``cbm_vars.inventory["area"]`` via a
wrapped reporting function; ws3 area tables self-checked against
``fm.inventory(period, "biomass")`` to 0.3%) gives a deterministic decomposition:

- **Same cohorts, same areas.** For every sampling tested, the unmatched area totals are
  *identical on both sides* (e.g. p=1: 588,469 ha on each side - area-tie artifacts of
  the matcher, not missing stands). Every cohort appears in both accounts.
- **A uniform -1-year age offset identifies the sampling.** At p=1 the pairs carry
  ``age_cbm - age_ws3 = -1`` uniformly at t=9, and ``frac(age match) = 0.94`` at **t=10**;
  the age-exact pairing is t = 10p (end of period, the convention documented in the
  curve-generation note), not the start-of-period sample used by
  ``compare_ws3_libcbm`` (``iloc[1::10]`` -> t = 10(p-1)+1).
- **At the age-exact pairing the biomass gap is +3.3%** (p=1, paired 2.43M ha:
  ws3 149.43 vs libCBM 144.63 e6 tC) - the same order as the no-harvest agreement
  (3.84% mean) and consistent with the audited bounds (curve simplification <=1.4%;
  first-rotation vs cycle residual <=~1.6% of landscape C; both documented in
  ``planning/curve-generation-and-reset-findings.md``).
- **The 14-38% aggregates are a comparison-sampling artifact.** Sampling t at
  start-of-period vs end-of-period changes the aggregate gap by factors of 2-3
  (p=1: +2.6% at t=9, +7.4% at t=11 with fixed pair sets); the old comparison's
  sampling lands where biomass has just been cut and not yet regrown - maximal
  divergence under harvest, negligible under no-harvest (why the no-harvest comparison
  was insensitive and the harvested one was not).
- **No hardwood anomaly exists**: the matched set spans all dtypes uniformly; the
  earlier "hardwood" suspicion came from an inconclusive single test and the
  fire-count pattern (a stand-splitting artifact) and is retracted.

Consequences: (1) the harvested-landscape comparison must sample at t = 10p (age-exact)
and use a tie-robust cohort matcher (area-only matching degenerates at late periods as
multi-rotation splits create duplicate area values); (2) the replay's structural
agreement is ~few %, so the manuscript's harvested-landscape validation can report
O(3-5%) stock agreement once the comparison convention is fixed; (3) nothing in the
14-38% was structural - it is entirely bookkeeping (sampling convention).

## Status after the first harness run (2026-10-13)

- `scripts/replay_validation.py` runs end-to-end; TSA 24 records in
  `results/femic-tsa24/replay/` (cbm/ws3 per-period stocks, pct diffs, figures).
- **Single-cut end-to-end test** (softwood dtype 2401000, one scheduled cut at a real
  cohort age): ws3 and libCBM cut effects agree on biomass (-0.382 vs -0.388e6 tC,
  ~1.5%), and the ecosystem effect converges as the slash/DOM transition settles.
  The per-cut bookkeeping is exact.
- **Landscape-level comparison** still shows a residual divergence under active
  harvest (biomass 14-38% mean vs 3.84% in the no-harvest comparison; grows with
  cumulative harvest, insensitive to start- vs end-of-period sampling). Open
  suspects, in order: (1) hardwood-tagged dtypes' stand age/tsl initialization (the
  hardwood single-cut test was inconclusive - needs a no-cut-baseline comparison);
  (2) the documented first-rotation vs rotation-cycle residual compounding over the
  ~2 rotations (6.85M ha cut on a 3.31M ha landscape); (3) multi-rotation area
  bookkeeping on the ws3 side. **Do not use the harness for manuscript numbers until
  this is closed.**

Evidence scratch (session): `/tmp/opencode/replay_test2.py`, `debug_missing.py`,
`debug_full.py`, `calib_managed_ages.py`, `debug_tsl.py`, `debug_species_ages.py`.
