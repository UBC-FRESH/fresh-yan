# Harvest-consistent carbon yield curves: findings and method (2026-10-11)

Status: complete (curves, corrected accounting, grid, and independent verification; see the Update sections below).

## The defect: post-harvest reset applies a spun-up age-0 state

The model resets every harvested stand to the transition (managed) dtype at **age 0**
(`*ACTION harvest Y` → `targetage=0`; transitions map `2402000 → 2422000` with no `_AGE`
override), so the stand's carbon becomes `curve_managed(0)`. That age-0 state comes from
libCBM's spin-up (equilibrium under a periodic disturbance regime), which is known to
over-accumulate dead organic matter (Boisvenue et al. 2022: deterministic-interval burns
vs stochastic fire; Metsaranta et al. 2017; Oberpriller et al. 2021).

Conservation requires the post-harvest state to be `pre_harvest_eco − merch −
disturbance_emissions`. Measured on the committed curves across all 37 dtypes, the reset
error (conservation-implied post state minus the applied `curve(0)`) is **−31 tC/ha
(median) at age 80, −20 at 100, −13 at 120** — i.e. every harvest injects tens of tC/ha
of phantom carbon, correlated with harvest age (a decision variable), so it biases the
LP's schedule choice as well as the reported stocks/emissions. No spin-up configuration
fixes this: fire-spun `curve(0)=190.97`, clearcut-spun `205.62`, conservation-implied
~177 for the sample dtype.

## The fix: simulate the clearcut

`src/fresh_yan/curves.py` now generates **managed curves by simulating the harvest**:

- the stand grows on its natural trajectory to `rotation_age`;
- a libCBM harvest event transfers the pools per CBM's disturbance matrix (merch removed,
  slash to dead pools, disturbance emissions) — age-0 is conservation-consistent by
  construction (verified: drop = merch + disturbance emissions, all dtypes);
- the stand regrows on the managed yield curve; the post-event trajectory is extracted
  as the managed curve.

Two variants are generated:
- `mode='single'`: one clearcut → age-0 = first-rotation post-harvest state;
- `mode='cycle'`: clearcut repeated every `rotation_age`, last cycle extracted → age-0 =
  rotation-cycle equilibrium.

Natural curves are unchanged (spun-up; initial-landscape convention, shared across
scenarios, documented).

`rotation_age = 120`: measured area-weighted median harvest age is 110 (base max
even-flow scenario) and 120–125 (emission-minimizing trade-off scenarios at df=1.5/2.0).

## Variant comparison (sample dtype; reset error, tC/ha; + = reset adds carbon)

| harvest age | first-harvest err (single) | first (cycle) | repeat err (single) | repeat (cycle) |
|---|---|---|---|---|
| 80 | +8.9 | −1.8 | +30.6 | +27.0 |
| 100 | +4.6 | −6.2 | +17.2 | +13.0 |
| 120 | −0.8 | −11.5 | +5.2 | +0.3 |
| 150 | −9.3 | −20.0 | −10.4 | −16.0 |
| 200 | −21.6 | −32.3 | −30.6 | −37.1 |

Aggregate phantom carbon over the actual schedules (Σ area × reset error):

| schedule | committed (spun-up) | single | cycle |
|---|---|---|---|
| base scenario (7.7 Mha) | **+96.6 MtC** | +33.1 | **+1.35** |
| trade-off df=1.5 hl=100 | **+82.5 MtC** | +20.6 | **+0.57** |

The committed/single columns were computed on the legacy (pre-50/50) schedules; the
cycle column is updated to the current schedules (verified 2026-10-11). Current spot
scenarios on the corrected (v2, 50/50) schedules (net phantom, MtC): (100, 1.5) +0.57 ·
(100, 2.4) −9.55 · (200, 2.4) −20.19 (1.63% of landscape C) · (2, 2.4) +3.95. The net
aggregate artifact falls ~70x (base +96.6 -> +1.35 MtC); the residual is the
first-harvest vs repeat-harvest inconsistency (a single managed curve cannot represent
all harvest histories), with cohort-level residuals up to ±44 tC/ha at off-rotation ages
that largely cancel in aggregate. Optional refinement: age-class transition routing
(ws3 transitions are age-keyed; SIT transitions carry age bounds) — multiplies managed
dtypes.

## ws3 → libCBM bridge notes (for the direct-run validation)

- Default `_cbm_sit_events` exports min/max age = −1, so libCBM harvests "oldest first"
  within a dtype instead of the scheduled cohort — a confound for direct comparisons.
- Event age bounds match the **CBM stand age at the event year**: for a stand with
  inventory age A and an event at year y, the matching bound is `A + y − 1` (calibrated;
  e.g. inventory age 1 + year 110 → bound 110; inventory age 205 + year 10 → bound 214).
  Managed (post-reset) stands follow a different offset; exact landscape-level
  validation is still being finalized.

## Open items

- Landscape-level validation (curve accounting vs direct CBM run with cohort-exact
  events) — in progress (first-harvest cohort validation is exact; the managed-stand
  age offset is still open).
- Update the design note and the manuscript methods (curve generation; merch-based HWP
  inflow vs Eq. 10; exact 2**(-10/hl) vs Eq. 12; inflow-based substitution vs Eq. 18;
  utilized-volume naming; DOM initialization caveat with citations; the reset-residual
  bound — worst spot −20.19 MtC = 1.63% of landscape C).

## Cohort-level validation vs a direct libCBM simulation

For the sample dtype (`tsa24 1 2402000 100 2402000`, harvested at model age 120) the
curve-based trajectory was compared against a single-stand libCBM run harvesting the
identical stand state (event age bound calibrated; alignment: model end-of-period p <->
CBM timestep 10p+1):

- **Biomass: exact agreement (0.00 tC/ha difference across all periods)** -- the
  managed yield-curve regrowth reproduces CBM exactly.
- **DOM/ecosystem: -11.05 tC/ha at 10 years post-harvest, converging to -4.19 at 200
  years.** The residual is the documented first-harvest vs rotation-cycle difference
  (the cycle curve's age-0 is 174.28 vs 185.03 for a first-rotation clearcut of a
  natural stand at 120); it decays as the stands converge on the same trajectory.
- Aggregate effect on real schedules: ~1% of landscape carbon (cycle variant).

## Update: official curves + corrected accounting (same day)

- Official curves in `curves/` are the `cycle` variant (rotation age 120; `merch`
  column added as the HWP inflow source).
- `src/fresh_yan/accounting.py` implements the corrected (v2) accounting: end-of-period
  stock differences, products-only HWP ledger (inflow = curve merch x util_rate;
  survival = 2**(-10/hl); substitution = df x inflow x credit). Verified on a scenario:
  the LP objective equals exactly the negative of the reported tracker total (same
  accounting), and the telescoped conservation identity closes to 0.0.
- HWP allocation follows the manuscript methods: utilized fibre split 50/50 between
  paper (half-life 2 yr) and solid wood (grid half-life). The legacy loop silently used a
  single solid-wood product type (proportion_solid_wood = 1.0), which contradicts the
  methods and roughly doubles the substitution credit.
- The corrected accounting + 50/50 split shifts the trade-off: harvest rises smoothly
  with displacement (129k ha at df=0, 207k at df=0.5 -- both at hl=200; 1.42M ha at
  df=1.0, 2.59M at df=2.0, 3.39M at df=2.4 -- hl=100/50). The abrupt "cliff" of the
  published result does not appear in these spot checks. The full grid (2026-10-11)
  confirms: utilized harvest volume rises monotonically with displacement at every
  half-life; the steep transition band sits around df ~0.6-1.2 (top adjacent jumps
  252-261 x 10^6 m3); the surface is smooth/nonlinear, slightly non-monotone in
  half-life; range 72,684 -> 1,223,841,156 m3. Independent verification (adversarial
  audit + post-run checks): LP objective == -(tracker total) to ~1e-15 relative; 5,000
  rows, no NaN, provenance complete; spot cells exact (hl=100/df=1.5: 530,250,376.82
  m3, -1,586,066,278.9708 tCO2).
