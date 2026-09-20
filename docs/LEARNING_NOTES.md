# Explaining the project in an interview

## Thirty seconds

“I developed a Python tool for equilibrium silicon PN-junction electrostatics and a separate diode I–V fitting workflow. I solved nonlinear Poisson's equation using a conservative spatial discretization and damped Newton iteration, then checked it against an independent boundary-value solver and analytical limits. The fitting workflow estimates saturation current, ideality factor and series resistance, and reports uncertainty and weak identifiability. All included observations are synthetic; I have not validated a fabricated device experimentally.”

## Concepts to understand

| Term | Plain meaning | Scientific meaning and example |
|---|---|---|
| Built-in potential | Internal voltage created when p and n regions equilibrate | Charge redistribution creates a potential difference; it is not a battery voltage measurable without including contacts. The default model gives 0.7394 V. |
| Depletion approximation | Treat part of a junction as emptied of mobile carriers | Retain ionized dopants as space charge. Analytical widths/fields can differ from the full Boltzmann model, especially under strong asymmetry. |
| Boundary condition | Physics specified at the edges of a calculation | Neutral p/n bulks fix two potentials. Check contact positions so the finite domain does not distort the junction. |
| Finite volume | Balance an equation over small spatial regions | Charge in each control volume equals electric-field flux difference, making conservation directly testable. |
| Newton iteration | Improve a trial solution using local sensitivity | Solve a tridiagonal Jacobian system for a correction; damping controls steps. A small residual does not replace mesh convergence. |
| Fermi level | Equilibrium carrier energy reference | It stays constant while conduction/valence bands bend. Separate quasi-Fermi levels would be needed in biased transport. |
| Identifiability | Whether observations actually constrain a parameter | Low-current points can fit well while providing almost no information about series resistance. Inspect errors, bounds and correlations. |
| Weighted least squares | Respect each observation's uncertainty in fitting | Voltage residuals are divided by their standard deviations. Reversing axes does not preserve the observation model. |
| Jacobian/SVD | Sensitivity and independent information in a fit | Derivatives describe parameter sensitivity; singular values expose redundant combinations and stabilize covariance calculation. |
| Verification versus validation | Correct numerical solution versus agreement with the world | Independent solvers and synthetic truth verify implementation. Device measurements are needed for experimental validation. |

## Technical explanation

Start with Poisson's equation and equilibrium Boltzmann densities. Explain the cm⁻³ to m⁻³ conversion and why the p-to-n potential rises while the field points oppositely. Derive neutral-contact `asinh` values instead of assuming minority carriers are identically zero. Show the control-volume balance and its tridiagonal derivative. Explain residual versus grid convergence, and why interface fields converge more slowly than potential at abrupt doping.

For fitting, write the implicit diode equation with its series voltage drop, then rearrange it as V(I). State the current-controlled measurement assumption before discussing least squares. Explain logarithmic saturation current, fixed temperature, absolute-noise covariance and why active bounds/rank deficiency prevent an ordinary Gaussian covariance report.

No transport parameters are derived from the equilibrium profile. This separation is a scientific limitation, not a software bug.

## Questions to prepare

1. Why is the equilibrium Fermi level flat although bands bend?
2. How do you derive charge-neutral contact values?
3. Why can depletion theory disagree with an accurate numerical solution?
4. How did you distinguish solver, discretization and material-model errors?
5. Why average ionized doping over the interface control volume?
6. How does independent collocation handle the doping discontinuity?
7. What does the full-Boltzmann first integral add to verification?
8. Why fit V(I), and when would that be inappropriate?
9. Why can low-current observations not establish resistance reliably?
10. What would be required to predict biased current self-consistently?

## Career signal and accurate descriptions

This demonstrates boundary-value modelling, semiconductor electrostatics, parameter extraction, uncertainty interpretation, scientific testing and Python packaging. These competencies are relevant to device-characterization, scientific-software and simulation research roles. It does not establish commercial TCAD proficiency, fabrication experience or measured-device validation.

**CV bullet:** Developed a Python package for equilibrium silicon PN-junction electrostatics and diode parameter extraction, verified with independent numerical and analytical solutions, mesh-convergence studies and automated scientific tests.

**Project description:** A reproducible Python study of silicon junction electrostatics and compact diode I–V diagnostics, combining conservative nonlinear solvers, uncertainty-aware parameter fitting and documented model limitations.

Compared with Project 1, this adds spatial boundary conditions, conservative discretization, nonlinear matrix solves, independent boundary-value verification, inverse modelling and parameter identifiability. Before using it in applications, reproduce an example and explain the assumptions and major design decisions in your own words.
