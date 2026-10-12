# Multi-TSA carbon experiment: extension plan and prototype (issue #3)

Status: campaign live (2026-10-12). All five femic instances are materialized from the
new Arbutus cloud; curve regeneration runs on the fixed acode path (see
"Materialization and pins" below).

## Purpose

Extend the corrected carbon experiment (5,000-scenario emission-minimizing grid) from
TSA 24 to the five management units of the Boisvenue et al. (2022) AOI (TSA 08, 16, 24,
40, 41) built with the femic + FreshForge pipeline (2025 VRI), and compare the
half-life/displacement response across management units (spatial replication).

## Parameterization (implemented)

- `model.model_paths(tsa, model_name, model_path)`: resolves the Woodstock section stem
  and directory (defaults reproduce the TSA 24 layout; other TSAs follow the femic
  export naming `tsa<code>.{lan,are,yld,act,trn}`).
- `model.curves_dir_for(tsa, curves_dir)`: `curves` for TSA 24, `curves/<tsa>` otherwise.
- `model.record_dir_for(tsa, folder, out_dir)`: TSA 24 keeps the legacy record layout;
  other TSAs nest under `results/<tsa>/`.
- CLI (`no-harvest`, `base-scenario`, `generate-curves`, `trade-off-grid`): new options
  `--tsa`, `--model-name`, `--model-path`, `--curves-dir`; `--out-dir` defaults follow
  the same rules.
- FreshForge provider nodes: same parameters; `model_path` is validated for existence.
- Provenance: record CSVs gain a `tsa` column; curve generation writes
  `provenance.json` (tsa, model_name, model_path, rotation_age, n_steps, mode, fy/ws3/
  libcbm versions).

## Prototype (wbi-birds `tsa24_clipped` fixture)

Verified end to end: curve generation (12 dtypes; per-dtype conservation checks pass),
a 2-scenario grid and a base scenario through the CLI with per-model curves, records
with `tsa` provenance, and the curves `provenance.json`.

Two findings that matter for the campaign:

1. **ws3 path-space explosion for low minimum harvest ages.** The `tsa24_clipped`
   example has `*OPERABLE harvest _AGE >= 8 AND _AGE <= 99`; with 10-year periods a
   stand is operable in essentially every period, so ws3's Model I path enumeration
   explodes (~2^20 action sequences per root) and `build_problem` never finishes.
   Patching the operability to a realistic range (`_AGE >= 80 AND _AGE <= 999`, as in
   TSA 24) makes the build 0.6 s. **Requirement for the femic exports: realistic
   minimum harvest ages (well above the period length); verify build time / path count
   per TSA at the validation gate.**
2. **Even-flow anchoring on period 1.** The 5% even-flow bands anchor on the first
   period's harvest; a landscape with no operable stands at t = 0 (the fixture's young
   inventory) locks harvest to zero for the whole horizon. Realistic TSA inventories
   (like TSA 24's) have operable stands at t = 0; still, check per TSA that the base
   scenario harvests a nonzero first period.

## Materialization and pins (2026-10-12)

- All five instances fully materialized from the new Arbutus cloud (`datalad get .`,
  ~12.8 GB total; `arbutus-s3` endpoint `object-arbutus.alliancecan.ca`, tenant-prefixed
  public URLs). Clone paths: `femic/external/femic-tsa<code>-instance/`; ws3 sections at
  `output/ws3/tsa<code>.{lan,are,yld,act,trn}`.
- **V2 re-export adopted (p113_5 "campaign config"):** THLB-filtered `.are` (stands with
  `thlb_raw >= 50`; no unmanaged state remains), regenerated `.yld` (period-unit ages,
  collapsed to one sample per period), unchanged `.lan/.act/.trn`; per-TSA dtype counts
  27, 30, 32, 38, 49. Pins: tsa08 `9032dc9`, tsa16 `1d7f5f8`, tsa24 `8b29bb9`, tsa40
  `7de7927`, tsa41 `efa2c0d` (v1 pins for reference: `814c4ca`/`c5bca92`/`9a4a1f5`/
  `5a2dc99`/`46e494d`; v1 sections snapshotted session-locally at
  `/tmp/opencode/femic_v1_snapshot/`). Reference baselines (even-flow epsilon 0.1, no
  bird floors) in each instance's `evidence/campaign_baseline_2026-10-12/`; the locked
  config in `evidence/p113_5_campaign_config_2026-10-12.md`.
- Spec: 200-year horizon, 10-year periods, clearcut operability 80-400 years, stands
  regenerate to age 0 (`*ACTION cc Y` -> targetage 0; self-transitions, no
  natural->managed reclassification).
- Campaign artifact convention: curves in `curves/femic-tsa<code>/`, records in
  `results/femic-tsa<code>/<record>/` (explicit `--out-dir`), keeping the legacy TSA 24
  `curves/` + `results/` untouched as the data-vintage baseline.
- Curve-generation fixes needed for the femic section contract (this branch):
  `curves._clearcut_event` writes the model's stand-replacing action as the SIT
  `disturbance_type` id; dtype classification follows the transition graph
  (`curves._regeneration_sources`) so every regeneration target (including natural-curve
  self-targets) gets a simulated-clearcut curve; `accounting._harvest_area` /
  `_period_inflows` follow `is_harvest`; `scenario.compile_scenario` takes
  `harvest_acode`.

## Curve generation (2026-10-12)

- Generated with `generate-curves --section-units periods --harvest-acode cc
  --out-dir curves/femic-tsa<code>` (rotation 120, 5-rotation cycle, 700 steps).
  Every femic dtype is a self-regenerating harvest target, so all dtypes receive
  simulated-clearcut curves (`0 initial-only dtypes, N regeneration targets`).
- Sets: tsa08 32 dtypes / tsa16 49 / tsa24 27 / tsa40 30 / tsa41 38 (701 rows per
  dtype). QA: ecosystem identity exact (<=1.5e-13), merch floor 0. Worst reset
  residual per TSA: +5.12 / -3.62 / +4.45 / +4.25 / +4.31 tC/ha.
- Reset-residual note: the legacy TSA 24 audit calibrated the bound at +/-5 tC/ha
  (-0.87..+3.74). The tsa08 outlier (+5.12, `8 managed 803001 bwbs_at 803001`) is
  still-drifting slow-DOM convergence: the post-cut state rises ~+2.9/+2.0/+1.3/+0.9
  tC/ha per rotation through cut 8 (equilibrium a few tC/ha higher; horizon-scale
  effect <=~2 tC/ha). Accepted for method parity with the legacy 5-rotation cycle and
  documented here rather than spun up further.

## Campaign checklist

1. Build smoke per instance — done 2026-10-12 (TSA24 gate: 54 dtypes, `cc` action,
   20 x 10-year periods, SIT in 33 s).
2. Generate curves per TSA (`generate-curves --tsa <code> --model-path <export>
   --section-units periods --harvest-acode cc --out-dir curves/femic-tsa<code>`);
   check per-dtype conservation (pre - post = merch + disturbance emissions) and the
   first-harvest cohort validation against a direct libCBM run.
3. Base scenario per TSA (max even-flow) - also yields the area-weighted median harvest
   age for the rotation-age rule.
4. Trade-off grid per TSA (identical 25 x 200 design; HiGHS; 48 workers).
5. Cross-TSA analysis: threshold displacement factor vs half-life; steep-band location
   and width; maximum utilized volume relative to each unit's even-flow capacity;
   response at reference cells; relate to TSA attributes (area, species mix, age
   structure, initial carbon).
