# PN-Junction Electrostatics and Diode Diagnostics

One-dimensional silicon junction electrostatics and compact diode I–V parameter extraction, with explicit model assumptions and numerical validation.

**Status: implementation in progress.** The initial scope is preserved here before model development. No release has been validated yet.

## Scientific scope

- Solve equilibrium Poisson–Boltzmann electrostatics for an abrupt silicon PN junction.
- Calculate potential, electric field, carrier densities, space charge and energy bands.
- Compare with the analytical depletion approximation and an independent boundary-value solver; study grid and domain convergence.
- Separately fit a compact diode model with saturation current, ideality factor and series resistance to current-controlled I–V data.
- Report residuals, local parameter uncertainty and identifiability diagnostics using a reproducible, explicitly synthetic case study.

The equilibrium calculation does **not** predict biased diode current. Coupled transport, capacitance, incomplete ionization, degenerate statistics and industrial TCAD are outside this first release.

This is Project 2 of a semiconductor scientific-computing portfolio, following [Semiconductor Carrier Statistics](https://github.com/Atabrahim/semiconductor-carrier-statistics). It adds spatial boundary-value problems, conservative discretization, nonlinear systems and parameter estimation.

See [the progress record](docs/PROJECT_PROGRESS.md) for completed work, checks and the next action. Installation and usage instructions will be added when they have been executed successfully.

## License

MIT for original code, documentation and generated figures. Scientific references retain their own licenses; no external experimental data are included.
