# Multi-TSA carbon experiment: extension plan and prototype (issue #3)

Status: plumbing complete (prototype verified 2026-10-11/12); the campaign is gated on
the femic section exports (`UBC-FRESH/femic#316`).

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

## Campaign checklist (when the exports land)

1. Stage each `femic-tsa<code>-instance` ws3 export; run a `build_model` + `to_cbm_sit`
   smoke (operability and build-time checks per finding 1).
2. Generate curves per TSA (`generate-curves --tsa <code> --model-path <export>`);
   check per-dtype conservation (pre - post = merch + disturbance emissions) and the
   first-harvest cohort validation against a direct libCBM run.
3. Base scenario per TSA (max even-flow) - also yields the area-weighted median harvest
   age for the rotation-age rule.
4. Trade-off grid per TSA (identical 25 x 200 design; HiGHS; 48 workers).
5. Cross-TSA analysis: threshold displacement factor vs half-life; steep-band location
   and width; maximum utilized volume relative to each unit's even-flow capacity;
   response at reference cells; relate to TSA attributes (area, species mix, age
   structure, initial carbon).
