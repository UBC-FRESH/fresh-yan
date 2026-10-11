# fresh-yan

Open, reproducible code, data, and results for the CJFR manuscript:

> Coupland, K., Paradis, G., Ghasemi, E., Ghotb, S., & Yan, W. (in preparation).
> The role of harvested wood product half-life and displacement uncertainty in
> forest management decision trade-offs and carbon dynamics in British Columbia.
> *Canadian Journal of Forest Research*.

Built on [`ws3`](https://github.com/UBC-FRESH/ws3) (forest estate simulation and
optimization) and [`libcbm_py`](https://github.com/cat-cfs/libcbm_py) (forest carbon
budget model), with the Prince George Timber Supply Area (TSA 24, British Columbia)
as the case study.

## Why this exists

The climate benefit of harvesting depends on how long harvested wood products (HWPs)
stay in use (half-life) and how strongly they displace emissions-intensive materials
(displacement factor). Both parameters are deeply uncertain, and the manuscript shows
that they drive the optimal management regime between conservation and intensive
harvest. This package makes every figure and table in the paper reproducible from
tracked records: the model code, the inputs, the scenario grids, and the analysis that
turns records into results.

## What it does

- **No-harvest validation.** Compares ws3's carbon yield-curve approach against a
  direct libCBM run on the real TSA 24 landscape (stocks and net emissions).
- **Base scenario.** Maximizes even-flow harvest volume (harvest area, harvest volume,
  growing stock) over the 200-year horizon.
- **Trade-off grid.** Bi-objective harvest-volume vs net-emission frontiers across HWP
  half-lives and displacement factors.
- **Sensitivity grid.** Optimal harvest volume over the (half-life, displacement)
  plane, feeding the manuscript's 3D and orthographic maps.
- **Manuscript figures and tables** regenerate from the tracked records via tracked
  commands.

## Status

`v0.0.1` (scaffold). Records generated so far: no-harvest comparison
(`results/no_harvest/`). Base scenario, trade-off and sensitivity grids are in
progress; see `ROADMAP.md`.

## Quick start

```bash
pip install -e ".[dev]"
fresh-yan --help
fresh-yan no-harvest          # regenerates results/no_harvest/*
```

## Related

- [`msc_walter_yan`](https://github.com/UBC-FRESH/msc_walter_yan) — the original MSc
  modelling repository (TSA 24 ws3 model, carbon yield curve generation, notebooks).
- [`ws3`](https://github.com/UBC-FRESH/ws3) — wood supply simulation and optimization.
- [`yan-yancun-masc-thesis-paper`](https://github.com/UBC-FRESH/yan-yancun-masc-thesis-paper)
  — manuscript sources.

## License

MIT, Copyright (c) 2026 UBC FRESH Lab.
