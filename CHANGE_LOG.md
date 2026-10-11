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
