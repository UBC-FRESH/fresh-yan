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
