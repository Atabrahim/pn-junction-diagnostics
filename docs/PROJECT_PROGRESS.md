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
- [x] Implement, validate and publish equilibrium electrostatics, scientific tests and model documentation.
- [x] Implement and validate diode diagnostics (milestone publication in progress).
- [ ] Produce and visually inspect scientific figures and finish documentation.
- [ ] Verify clean installed package, API, CLI, README commands and full tests.
- [ ] Verify GitHub Actions on supported Python versions.
- [ ] Publish a versioned release from the verified commit.

## Current state and validation

The silicon material model, analytical depletion profiles, conservative equilibrium solver and independent two-domain collocation reference are implemented. The model, units, contact conditions and references are documented in `MODEL.md`.

Local milestone check: **52 tests pass** on Python 3.12. The original 28 tests cover the Project 1 silicon parameter reference, charge balance, mass action, bandgap consistency, discrete Gauss law, symmetric reflection, contact padding, independent collocation agreement and second-order potential convergence. The additional 24 cover implicit diode inversion, the Shockley limit, noiseless recovery at three temperatures, noisy parameter recovery, covariance scaling, weak resistance identifiability, rank deficiency, active bounds and invalid inputs. Ruff and formatting checks pass. No experimental validation is claimed.

The separate diode API is implemented. For seed 2026 synthetic voltage noise (sigma = 1.5 mV, 100 controlled currents from 1 nA to 20 mA), the fit gives Is = 9.947409e-12 A, eta = 1.599789, Rs = 4.938152 ohm and reduced chi-square = 1.044628. Truth is (1e-11 A, 1.6, 5 ohm); all recovered values are within three local standard errors. Absolute voltage uncertainties are supplied, not estimated from the residuals.

The default symmetric 300 K, 10¹⁶ cm⁻³ junction has Vbi = 0.7394037131 V. Its numerical peak field is about 4% below the depletion approximation. Strong doping asymmetry can give much larger differences because mobile charge near the interface is not negligible; the independent solution is the discretization benchmark.

A wheel-install CI workflow is published. Remote CI success has not yet been verified.

## Known issues / remaining tasks

CLI, examples, figures, full documentation and final QA remain. The first release is planned as `v0.1.0`. No release has been created. The interrupted upload was recovered from intact local files; no scientific work was lost.

**Next action:** verify this diode milestone on GitHub, then add reproducible CLI/examples/figures and complete release QA.
