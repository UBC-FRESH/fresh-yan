# CJFR submission - remediation status

Status of the rejection-risk worklist from the antagonistic editor / reviewer-2
simulation (2026-10-14). The source audit lived in `/tmp` and was not durable; this
page records the worklist and its resolution state.

## Done (merged)

- **P1 claim-record reconciliation** (manuscript PRs #4, #5). Five verified
  mismatches corrected (161-703 MtC; per-unit no-harvest agreement matrix; TSA 16
  cessation boundary; TSA 41 grid maximum 0.69; TSA 24 df50 range 1.47-1.79); the
  "narrow" / "near-cessation" / "near-maximum" descriptors replaced with quantified
  statements in the abstract, results, discussion and conclusion (10-90% transition
  widths, median 1.8 tC/tC of the tested 0-2.4 axis; plateaus 52-78% of the
  volume-maximizing base).
- **P2 equations.** Eq. (16) sign corrected to the stock-decrease convention, with a
  defining sentence.
- **P4 prescription/rotation text.** Curves compiled on a 120-year regeneration
  cycle; operable stands 80-400 years; median harvested ages 110-125 years.
- **P5 structural robustness** (fresh-yan PR #8). `scripts/robustness_checks.py`
  parameterized for campaign models; records at `results/femic-tsa24/robustness/`;
  the manuscript limitations report the magnitudes (2.9-10.3x low-displacement
  suppression; 3.6-14x across-variant volume range; -16% to +18% net-emission
  effect, +80% under all-solid allocation at df=2.0).
- **P13 compliance (partial).** AI declaration names the tool and model; funding
  statement and CRediT confirmation pending author input.
- **P14 polish.** Highlights removed; Boisvenue DOI corrected
  (10.1088/1748-9326/ac9919); garbled sentences; PG-TSA leftovers; roadmap ordering;
  unsourced area claim removed; the 1.4% simplification number replaced by the
  stated tolerance; handoff, README and reproducibility docs synced.

## Open - author decisions

- **P6 harvested-landscape validation.** (A) fallback: stand-level validation plus
  explicit scoping (the current text already scopes the landscape comparison as
  future work; the replay harness carries an unexplained aggregate residual);
  (B) time-boxed attempt (3-10 days) on the cohort-exact ws3<->libCBM managed-stand
  bridge.
- **P7 claim handling.** (A) restate the "not identifiable" claim (~0.5 day);
  (B) add an evidence-to-decision analysis (~1-2 days) supporting the title claim.

## Pending

- **P9/P10/P11.** Attribute analysis of the cross-unit threshold ordering; novelty
  positioning vs recent literature (Boiger 2025; Daigneault 2022; Lucey 2024;
  Yan 2025); displacement-factor convention normalization (including the 0.425x
  effective-credit axis).
- **P3 release.** Tagged releases + Zenodo DOI; regenerate derived records from a
  clean pin (current derived records carry `fy_commit=b492c7c+dirty`); final
  text-vs-record sweep; submit.

Fallback journals if CJFR declines: Ecological Modelling; Environmental Modelling &
Software; Carbon Balance and Management.
