# fresh-yan

Open, reproducible code, data, and results for the CJFR manuscript:

> Coupland, K., Paradis, G., Ghasemi, E., Ghotb, S., & Yan, W. (in preparation).
> The climate-optimal harvest level is not identifiable from current HWP evidence:
> a five-landscape optimization test in British Columbia, Canada.
> *Canadian Journal of Forest Research*.

Built on [`ws3`](https://github.com/UBC-FRESH/ws3) (forest estate simulation and
optimization) and [`libcbm_py`](https://github.com/cat-cfs/libcbm_py) (forest carbon
budget model), using five interior British Columbia timber supply areas (TSA 08,
16, 24, 40 and 41) as the case study.

## Why this exists

The climate benefit of harvesting depends on how long harvested wood products (HWPs)
stay in use (half-life) and how strongly they displace emissions-intensive materials
(displacement factor). Both parameters are deeply uncertain, and the manuscript shows
that they drive the optimal management regime between conservation and intensive
harvest. This package makes every figure and table in the paper reproducible from
tracked records: the model code, the inputs, the scenario grids, and the analysis that
turns records into results.

## What it does

- **No-harvest validation.** Compares ws3's carbon yield-curve approach against
  direct libCBM runs on the five real model landscapes (stocks and net emissions).
- **Base scenario.** Maximizes even-flow harvest volume (harvest area, harvest volume,
  growing stock) over the 200-year horizon, for each of the five units.
- **Emission-minimizing trade-off grid.** Optimal harvest under the net-emission
  objective across HWP half-lives and displacement factors.
- **Sensitivity grids.** 5,000-cell (half-life x displacement) optimal-harvest grids
  per unit, feeding the manuscript's five-unit surface maps.
- **Cross-TSA analysis.** Flip thresholds (mid-point and 10-90% bands), reset-residual
  bounds and the literature overlay for the five units.
- **Structural robustness.** One-at-a-time variants (even-flow width, horizon, wood
  allocation) re-run on the campaign model.
- **Manuscript figures and tables** regenerate from the tracked records via tracked
  commands.

## Status

`v0.0.1`. Records complete for the five-unit campaign: no-harvest validation
(every unit vs libCBM), base scenarios, emission-minimizing grids, 5 x 5,000-cell
sensitivity grids, cross-TSA analysis (thresholds, reset residuals, overlay) and
structural robustness (`results/femic-tsa*/`, `results/cross-tsa/`). The manuscript
is in submission preparation. `v0.1.3` is released and archived on Zenodo: [doi:10.5281/zenodo.23518081](https://doi.org/10.5281/zenodo.23518081); see `ROADMAP.md`.

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
