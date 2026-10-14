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
- **P13 compliance.** AI declaration names the tool and model; funding statement
  (NSERC Discovery Grant RGPIN-2023-04197) and CRediT (first-author order and roles)
  complete.
- **P14 polish.** Highlights removed; Boisvenue DOI corrected
  (10.1088/1748-9326/ac9919); garbled sentences; PG-TSA leftovers; roadmap ordering;
  unsourced area claim removed; the 1.4% simplification number replaced by the
  stated tolerance; handoff, README and reproducibility docs synced.

## Resolved author decisions (2026-10-14)

- **P6 - fallback selected.** The stand-level harvested-cycle check is delivered
  (`results/femic-tsa24/stand_validation/`); the cohort-exact landscape comparison
  remains future work (unresolved replay residual, not yet at record quality).
- **P7 - evidence-to-decision analysis delivered** (record:
  `results/cross-tsa/decision_under_evidence.csv`; reported in the discussion).
- **Author side.** Gregory Paradis is first author with an expanded CRediT set;
  funding statement: NSERC Discovery Grant RGPIN-2023-04197. Zenodo: tagged release
  at freeze, DOI via the GitHub integration.

## Pending

- **P9/P10/P11 - done.** Threshold-attribute analysis
  (`results/cross-tsa/threshold_attributes.csv`); novelty positioning vs Boiger
  2025 / Daigneault 2022 / Lucey 2024 and the Yan 2025 precursor (manuscript
  introduction, verified citations); displacement-factor convention mapping
  (`results/cross-tsa/df_convention_mapping.csv`; 0.425x effective-credit axis).
- **Post-release correction (2026-10-14).** The no-harvest comparison sampled libCBM
  at the start of each period (t = 10(p-1)+1) while ws3 inventories are end-of-period
  (t = 10p); fixed to the end-of-period pairing, records regenerated, and the
  manuscript validation numbers updated (stock agreement now 0.2-5.4% period-mean;
  fluxes with no sign flips).
- **P3 release - done (2026-10-14).** fresh-yan `v0.1.0` tagged + released,
  archived on Zenodo (doi:10.5281/zenodo.23357325, cited in the data statement);
  manuscript repo tagged `cjfr-submission-1`; derived records regenerated from a
  clean pin (values identical); CI green after landing pre-existing lint fixes;
  text-vs-record sweep re-run. Remaining: author read-through and submission.

Fallback journals if CJFR declines: Ecological Modelling; Environmental Modelling &
Software; Carbon Balance and Management.
