# Experiment design note (v2, post-audit-1): the corrected carbon accounting

Status: formulation under second adversarial review before implementation.

## What adversarial review #1 killed in the v1 design

The v1 stock-difference ecosystem term `E_eco = S(a_t) − S_regen(0)` **double-counted
harvested carbon**: at a harvest node the eco stock drop includes the product transfer
(to HWP), and the legacy HWP ledger's gross decay/residue terms count the same carbon
again. Audit derivation: the telescoped objective overshoots true net emission by
≈ Σ new_product_stock (≈ 23 tC/ha per harvest at age 85).

Sample decomposition (dtype `tsa24 1 2402000 100 2402000`, age 85):
- pre-harvest stock: 207.14 tC/ha (biomass 70.13 + DOM 137.01)
- post-reset stock: 192.13 (slash + DOM retained + first-period establishment)
- drop = 15.01 = products (0.85 × 30.08 = 25.57) + field-loss residue (0.15 × 30.08 =
  4.51) − first-period growth (15.07)

## Corrected formulation (v2)

Objective per period, per prescription path (maximize its negative ⇒ minimize):

    E_sys(t) = [E(t) − E(t+1)] + [H(t) − H(t+1)] − sub_t

which telescopes to

    (S₀ − S_T) − H_T − Σ substitution       (× 44/12 for tCO2)

**Exact carbon conservation by construction:** the product transfer moves between the
ecosystem and HWP ledgers exactly once; the field-loss residue is an instant emission at
harvest already inside the ecosystem stock change; HWP decay is captured by the HWP
stock change (−ΔH). No gross HWP decay/residue terms.

Implementation rules:

- **Ecosystem stock differences:** standard ws3 `inventory()` (end-of-period convention,
  Woodstock-parity tested).
- **HWP ledger — products only.** Inflow = curve merchantable-stem carbon × util_rate
  (85%). **No gross decay terms, no instant-residue term** (see above).
- **HWP inflow from the curve merchantable pool** (30.08 tC/ha at age 85), not the
  volume×density conversion (23.07 tC/ha — a 23% inconsistency, flagged for Methods).
- **Substitution:** displacement factor × product stock (unchanged).
- **Decay:** exact `2^{−10/hl}` (the `(1−k)^10` approximation errs up to 3.4% at hl=4).
- **Trackers** record the same quantity the LP minimizes; stocks via standard
  end-of-period `inventory()`.
- **libCBM comparison:** sample at end-of-period instants (timesteps 10p+1,
  `n_steps ≥ 201`).

## Other audit-1 corrections incorporated

- Evidence-table alignment: `Σ_{years 1..200} net_emission = stock(0) − stock(200)`
  exactly; the flux at index x is the year ending at age x.
- `compile_scenario` typo `'total_emissions'` → `'total_emission'` (ocf was silently 0).
- `cmp_c_cs` latent decay/result bugs (decay per **period** instead of `2^{−10/hl}`;
  `result` overwritten each node).

## Open items for the second audit

- Verify the telescoped ledger's carbon balance at harvest nodes (the decomposition
  above) and confirm zero double counting / zero leakage.
- The field-loss residue treatment in the curve reset (instant emission vs retained DOM):
  baked into the curve generator; verify and state for Methods.
- Merch-carbon source for HWP inflow (curve merch vs volume conversion): confirm the
  carbon-balance argument and the side effects on substitution credit.
- Telescoping and the objective's discriminating power for the conservation-vs-harvest
  trade-off.
- Any remaining sign/unit/off-by-one errors in the formulation and its code mapping.
