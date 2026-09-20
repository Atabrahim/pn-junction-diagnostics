# Project progress

Updated: 2026-09-20. This file is the continuity record; inspect it and the current GitHub tree before resuming work.

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
- [x] Implement, validate and publish diode diagnostics and its 24 scientific/software tests.
- [x] Implement CLI, reproduce all three scientific figures and inspect their raster renders.
- [x] Write README, model derivation, data provenance, validation and learning notes.
- [x] Build sdist/wheel and verify the wheel in a fresh environment: API, CLI, example and full tests.
- [x] Verify expanded GitHub Actions on Linux Python 3.11–3.13 and Windows Python 3.12.
- [x] Complete all implementation and release-preparation gates. Version: `0.1.0`.

## Current state and validation

The silicon material model, analytical depletion profiles, conservative equilibrium solver and independent two-domain collocation reference are implemented. The model, units, contact conditions and references are documented in `MODEL.md`.

The scientific milestones passed 52 tests: 28 electrostatics tests and 24 diode tests. The completed implementation now passes **61 tests**, adding three full-Boltzmann first-integral checks and six CLI checks. Ruff and formatting checks pass, including the README Python example. No experimental validation is claimed.

The separate diode API is implemented. For seed 2026 synthetic voltage noise (sigma = 1.5 mV, 100 controlled currents from 1 nA to 20 mA), the fit gives Is = 9.947409e-12 A, eta = 1.599789, Rs = 4.938152 ohm and reduced chi-square = 1.044628. Truth is (1e-11 A, 1.6, 5 ohm); all recovered values are within three local standard errors. Absolute voltage uncertainties are supplied, not estimated from the residuals.

The default symmetric 300 K, 10¹⁶ cm⁻³ junction has Vbi = 0.7394037131 V. Its numerical peak field is about 4% below the depletion approximation. Strong doping asymmetry can give much larger differences because mobile charge near the interface is not negligible; the independent solution is the discretization benchmark.

The expanded wheel-install CI passed all four jobs on commit `8b1f9936927aa2955499342dc9400fe78adbf878` ([run 35481869943](https://github.com/Atabrahim/pn-junction-diagnostics/actions/runs/35481869943)). It builds distributions, installs the wheel, runs tests and Ruff, exercises API/CLI outside the checkout and reproduces all scientific results. Subsequent release-record edits do not change scientific code; the publication procedure also checks their latest CI run.

## Final implementation and QA status

**Original agreed scope: complete.** All 33 intended project files are published and the fetched GitHub tree was compared with the local contents. No model or software features remain to implement.

- 61 tests pass, zero failures/skips, with warnings treated as errors.
- Ruff lint and formatting pass, including the README Python example.
- Nine independent electrostatics cases pass: worst potential discrepancy 0.112 mV; worst interface-field discrepancy 0.155%.
- Three scientific figures were inspected visually; the installed wheel reproduces the committed synthetic CSV/metadata and three PNGs byte for byte.
- Sdist and wheel build; distribution contents and documentation links are checked.
- A fresh wheel installation passes API, CLI, example and all 61 tests outside the checkout.
- A fresh GitHub clone passes the README installation, CLI, reproduction, test, lint, formatting and build commands.
- GitHub presentation was inspected: the preview loads correctly, the description is current, and model/data limitations are explicit.

## Known issues and next action

No known release-blocking scientific or software issues remain. Documented physical limitations, synthetic-only observations and conditional fit uncertainties remain intentional limitations of this release.

The official publication record is the [v0.1.0 GitHub release](https://github.com/Atabrahim/pn-junction-diagnostics/releases/tag/v0.1.0) and its tag. This file records the completed pre-release gates: on resuming, inspect that release/tag and the latest CI before attempting any publication. If the release is present and verified, Project 2 is finished; do not restart development. If absent, publish it from the verified commit. No additional features or Project 3 work are required here.
