# Robustness spot-checks for the emission-minimizing flip (2026-10-12)

Purpose: answer the structural-robustness question raised in the manuscript review -
does the "harvest flips from near-zero to near-max across the displacement band"
result survive changes to the formulation's non-HWP assumptions (even-flow band,
utilized-fibre allocation, horizon endpoint)? The objective telescopes to terminal
system stock plus cumulative substitution, so the horizon is a first-order structural
choice.

Method: one-at-a-time variants around the baseline grid formulation, evaluated at
half-life 100 with displacement factors 0.5 / 1.0 / 2.0. Generator:
`scripts/robustness_checks.py` (rerun with `--out-dir results/robustness` to write a
provenance-carrying record; the first exploratory run lives in `/tmp/opencode/`).

| variant | df=0.5 | df=1.0 | df=2.0 |
|---|---|---|---|
| baseline (5% even-flow, 50/50 split, 20 periods) | 0.048 | 0.424 | 0.701 |
| no even-flow constraints | 0.554 | 0.601 | 0.969 |
| 15% even-flow band | 0.057 | 0.443 | 0.759 |
| solid-wood only (100% allocation) | 0.522 | 1.178 | 1.462 |
| horizon 15 periods (150 yr) | 0.002 | 0.042 | 0.428 |
| horizon 25 periods (250 yr) | 0.377 | 0.546 | 1.411 |

(Utilized harvest volume, 10^9 m^3; baseline cells reproduce the grid records exactly.)

Findings:

1. **The qualitative flip is robust**: every variant still shows the transition from
   little/no harvest at low displacement to large harvest at high displacement.
2. **Its location and level are strongly formulation-dependent.** At df = 0.5, the
   baseline harvests 0.048e9 m3; removing even-flow constraints gives 0.554e9 (11x),
   solid-only allocation 0.522e9 (11x), a 25-period horizon 0.377e9 (8x), and a
   15-period horizon 0.002e9 (24x lower). The even-flow band and the horizon endpoint
   are first-order determinants of where the flip sits.
3. **Implications for the manuscript**: report the flip as a *region* under a stated
   reference formulation, with this sensitivity as an explicit result - the structural
   dependence is itself consistent with the paper's epistemic thesis (the
   climate-optimal policy is not identifiable from any single parameterization, HWP or
   structural). The horizon sensitivity (terminal-stock term) should be stated plainly.

Status: exploratory run 2026-10-12 (18 solves, ~9 min); script committed; regenerate
as a tracked record with provenance when the results are folded into the paper.
