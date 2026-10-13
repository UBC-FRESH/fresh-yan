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

## Remaining implementation (this branch)

- `scripts/replay_validation.py`: build model + curves; solve the base scenario; emit
  cohort events per (dtk, age, area, period) with the rules above; run libCBM
  (`sit_transitions` emptied); verify the area ledger from the state table; compare
  per-period stocks vs `fm.inventory(...)`; write provenance records per unit
  (`results/femic-tsa<code>/replay/`).
- Then: five units, figures (ws3 vs libCBM under active harvest), manuscript updates
  (replace the "future work" scope with the corrected harvested-landscape validation).

Evidence scratch (session): `/tmp/opencode/replay_test2.py`, `debug_missing.py`,
`debug_full.py`, `calib_managed_ages.py`, `debug_tsl.py`, `debug_species_ages.py`.
