# Project progress

Updated: 2026-09-19. This file is the continuity record; inspect it and the current GitHub tree before resuming work.

## Original objectives and fixed first-release scope

Recovered from the saved Semiconductor Portfolio Plan: **PN-Junction Electrostatics and Diode Diagnostics**, repository `pn-junction-diagnostics`.

1. One abrupt silicon homojunction family at thermal equilibrium.
2. Numerical potential, electric field, carrier densities, space charge and band profiles.
3. Depletion-approximation comparison, boundary checks, mesh/domain convergence and independent numerical validation.
4. A separate compact forward diode model and one reproducible parameter-extraction case study with residuals and uncertainty.
5. Reusable Python API, CLI, examples, scientific figures, tests, documentation, installable package and working GitHub Actions.

Excluded: self-consistent biased transport, capacitance, arbitrary materials, process simulation, machine learning, dashboards and experimental claims without a licensed measured dataset.

## Lessons retained from Project 1

- Small `src` package; thin CLI; plotting outside the solver; explicit units.
- Scale nonlinear residuals and verify physical limits with independent methods.
- Test scientific relationships and failure paths, with warnings treated as errors.
- Label analytical, numerical and synthetic results separately; inspect every figure.
- Build distributions and test a clean wheel installation, including outside the source tree.
- Verify actual GitHub Actions runs and the release commit, not just workflow files.
- Publish early and after every substantial milestone to survive interrupted sessions.

The silicon parameter relations will follow the same cited model as Project 1. A small independent Boltzmann material layer keeps this package installable without a GitHub-only runtime dependency. Project 1's Fermi–Dirac integrator and neutrality solver will not be copied.

## Milestones

- [x] Recover the original project selection and scope.
- [x] Inspect Project 1 architecture, validation, packaging, CI and release lessons.
- [x] Inspect the authenticated GitHub account; no duplicate Project 2 repository found.
- [x] Publish and verify the initial root scaffold on GitHub.
- [x] Implement and validate equilibrium electrostatics (milestone publication in progress).
- [ ] Implement and validate diode diagnostics; publish milestone.
- [ ] Produce and visually inspect scientific figures and finish documentation.
- [ ] Verify clean installed package, API, CLI, README commands and full tests.
- [ ] Verify GitHub Actions on supported Python versions.
- [ ] Publish a versioned release from the verified commit.

## Current state and validation

The silicon material model, analytical depletion profiles, conservative equilibrium solver and independent two-domain collocation reference are implemented. The model, units, contact conditions and references are documented in `MODEL.md`.

Local milestone check: **28 tests pass** on Python 3.12, including the Project 1 silicon parameter reference, charge balance, mass action, bandgap consistency, discrete Gauss law, symmetric reflection, contact padding, independent collocation agreement and second-order potential convergence. Failure paths and invalid inputs are checked. No experimental validation is claimed.

The default symmetric 300 K, 10¹⁶ cm⁻³ junction has Vbi = 0.7394037131 V. Its numerical peak field is about 4% below the depletion approximation. Strong doping asymmetry can give much larger differences because mobile charge near the interface is not negligible; the independent solution is the discretization benchmark.

A wheel-install CI workflow is being published. Remote CI success has not yet been verified.

## Known issues / remaining tasks

Diode fitting, CLI, examples, figures, full documentation and final QA remain. The first release is planned as `v0.1.0`. No release has been created.

**Next action:** verify this electrostatics milestone on GitHub, then implement the separate diode fit and uncertainty diagnostics.
