# Roadmap

| Phase | Scope | Status |
|---|---|---|
| P1 | Scaffold: repo, package skeleton, CLI, CI, inputs (`data/`, `curves/`) | done (2026-10-11) |
| P2 | Records: no-harvest comparison; base max even-flow harvest scenario | done (2026-10-11) |
| P3 | Harvest-consistent carbon curves + corrected (v2) accounting (issue #1) | active (grid re-run) |
| P3b | Records: trade-off grid (bi-objective loop over half-life x displacement) | next |
| P4 | Records: sensitivity grid (3D-map inputs) + analysis scripts | planned |
| P5 | `supplementary/` tree + manuscript figure/table builders (one command each) | planned |
| P6 | Release `v0.1.0` + Zenodo DOI + manuscript availability statement | planned |

Pipeline orchestration: the full modelling pipeline runs as a FreshForge workflow
(`workflows/pipeline.yaml`; provider `fresh_yan.pipeline`); record-only regeneration in
`workflows/records.yaml`.

Issue map: tracked in GitHub issues on this repository.
