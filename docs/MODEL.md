# Scientific model and numerical design

## Scope and provenance

This release treats an abrupt, planar, one-dimensional silicon homojunction at thermal equilibrium. Temperature is uniform (250–400 K), each side has uniform dopant density (10¹⁴–10¹⁷ cm⁻³), and all dopants are assumed ionized. These bounds restrict the numerical API; they do not certify negligible material-model error. Incomplete ionization, especially near the cold/high-doping corner, and bandgap narrowing can matter. Project 1 explores carrier-statistics approximations in more depth.

There is no applied terminal bias, interface sheet charge, dielectric discontinuity, generation, recombination or self-heating. Boltzmann statistics and constant effective masses are deliberate approximations. The compact I–V model below is a separate model, not a current calculated from equilibrium electrostatics.

## Silicon parameters

All densities in the public API are in cm⁻³. Poisson's equation uses SI lengths (m), permittivity (F/m) and charge (C); density is multiplied by 10⁶ on conversion to m⁻³. SciPy supplies the elementary positive charge `e`, Boltzmann constant `k`, Planck constant `h`, electron mass `m_e` and vacuum permittivity `epsilon_0`.

The thermal voltage is $V_T=k_BT/q$ in V. Numerically, $k_BT$ in eV equals $V_T$ in V.

$$E_g(T)=1.1695-\frac{4.73\times10^{-4}T^2}{T+636}\quad\text{eV}.$$

Here $T$ is temperature in K; the coefficient is in eV/K and the denominator constant in K. This is the Varshni parameter set in [Palankovski, §3.3.1, Table 3.8](https://www.iue.tuwien.ac.at/phd/palankovski/node37.html).

$$N_c=2g_v\left(\frac{2\pi m_{e,\mathrm{DOS}}k_BT}{h^2}\right)^{3/2},\qquad
N_v=2\left(\frac{2\pi m_0k_BT}{h^2}\right)^{3/2}\left(0.49^{3/2}+0.16^{3/2}\right).$$

These expressions produce m⁻³ before conversion. The conduction valley degeneracy $g_v=6$, spin degeneracy is 2, $m_{e,\mathrm{DOS}}=m_0(0.19^2\times0.98)^{1/3}$, and $m_0$ is the free-electron mass in kg. Electron transverse/longitudinal masses and heavy/light-hole masses come from [§3.3.4, Table 3.16](https://www.iue.tuwien.ac.at/phd/palankovski/node40.html); see also [the DOS equations](https://www.iue.tuwien.ac.at/phd/palankovski/node41.html). We hold masses fixed, unlike the fuller temperature-dependent model in that reference.

$$n_i=\sqrt{N_cN_v}\exp\left(-\frac{E_g}{2V_T}\right).$$

Here $n_i,N_c,N_v$ are in cm⁻³ and $E_g$ is numerically in eV. This is a **model-derived** intrinsic density, not a measured/calibrated silicon dataset. Its 300 K value is about $6.156\times10^9$ cm⁻³, consistent with the parameter model used in Project 1, not a universal experimental value.

We use $\varepsilon=11.7\varepsilon_0$ independent of temperature. The value is the lower end of the reported 11.7–11.9 range in [Palankovski, §3.2.1, Table 3.2](https://www.iue.tuwien.ac.at/phd/palankovski/node32.html), not that table's default of 11.9. No numerical accuracy claim includes uncertainty in these parameters.

## Equilibrium electrostatics

The coordinate $x$ increases from the p side to the n side, with the metallurgical interface at $x=0$. Acceptors $N_A$ occupy $x<0$, donors $N_D$ occupy $x>0$. Define signed ionized doping $C=-N_A$ on the p side and $C=N_D$ on the n side.

Let $u=(E_F-E_i)/(k_BT)$ be dimensionless. $E_F$ is the constant equilibrium Fermi energy; $E_i$ is the intrinsic energy. Then

$$n=n_i e^u,\qquad p=n_i e^{-u},\qquad \rho=q(p-n+C)10^6,$$
$$\frac{d^2u}{dx^2}=-\frac{\rho}{\varepsilon V_T},\qquad E=-V_T\frac{du}{dx}.$$

Electron/hole densities $n,p$ are in cm⁻³, charge density $\rho$ in C/m³ and electric field $E$ in V/m. The potential reported to the user is $\psi(x)=V_T[u(x)-u_L]$ in V, so the left contact is the voltage reference. The equations follow equilibrium drift–diffusion cancellation and Poisson's equation; see [MIT 6.012, Lecture 4](https://ocw.mit.edu/courses/6-012-microelectronic-devices-and-circuits-spring-2009/2a02d79958a93f067bd1ae334492fb6a75_MIT6_012S09_lec04.pdf).

**Boundary conditions:** contacts are placed well into the neutral bulk. Exact Boltzmann charge neutrality gives

$$u_L=\operatorname{asinh}\left(-\frac{N_A}{2n_i}\right),\qquad
u_R=\operatorname{asinh}\left(\frac{N_D}{2n_i}\right).$$

Dirichlet values are fixed at both contacts. The internal built-in potential is $V_{bi}=V_T(u_R-u_L)$. In the extrinsic limit this becomes $V_T\ln(N_AN_D/n_i^2)$. It is not an externally measurable open-circuit voltage: contact potentials must also be considered.

**Band diagram:** with $E_F=0$ eV, $E_i=-V_Tu$, $E_c=E_i+V_T\ln(N_c/n_i)$ and $E_v=E_c-E_g$, all numerically in eV. This energy reference differs from the left-referenced potential; only differences have physical meaning. The equilibrium Fermi level must be flat.

## Analytical depletion approximation

Neglect mobile charge in the depletion region and use neutral bulk outside it:

$$W=\sqrt{\frac{2\varepsilon V_{bi}}{q10^6}\left(\frac1{N_A}+\frac1{N_D}\right)},\quad
x_p=W\frac{N_D}{N_A+N_D},\quad x_n=W\frac{N_A}{N_A+N_D}.$$

Widths $W,x_p,x_n$ are in m; charge balance requires $N_Ax_p=N_Dx_n$. The peak field magnitude is $q10^6N_Ax_p/\varepsilon$. Field is negative because potential rises from p to n. Potential is quadratic within each depleted side, continuous with continuous field at the junction, and constant outside. See [MIT 6.012, Lecture 5](https://ocw.mit.edu/courses/6-012-microelectronic-devices-and-circuits-spring-2009/ac6a8e55da0ad6e1f7dedc37d86b6a75_MIT6_012S09_lec05.pdf).

For a like-for-like boundary comparison, the analytical profile uses the exact bulk $V_{bi}$ above. Numerical mobile-charge tails smooth the sharp depletion edges. A small persistent difference from the depletion approximation is physical model difference, not necessarily discretization error. No threshold-defined numerical depletion width is presented as exact.

## Discretization and nonlinear solve

Each side has a uniform mesh, with a shared node at zero. Left and right lengths are $x_p+bL_{D,p}$ and $x_n+bL_{D,n}$, where $L_D=\sqrt{\varepsilon V_T/(qN10^6)}$ is the majority-density Debye length and $b=12$ by default. Users can vary $b$ to check contact placement.

Lengths are scaled by $L_0=\sqrt{\varepsilon V_T/(qN_\mathrm{ref}10^6)}$, where $N_\mathrm{ref}=\max(N_A,N_D)$. Integrate Poisson's equation over each interior node's control volume. With dimensionless neighboring spacings $h_-,h_+$ and volume $v=(h_-+h_+)/2$, the residual is

$$R_i=\frac{(u_{i+1}-u_i)/h_+-(u_i-u_{i-1})/h_-}{v}
+\frac{p_i-n_i+C_i}{N_\mathrm{ref}}.$$

In this equation only, the subscript on $n_i$ denotes the electron density at node $i$, not intrinsic density. The code uses distinct names to avoid that ambiguity. At the interface, signed doping is averaged over the portions of the control volume on each side. This preserves ionized dopant charge on an unequal mesh.

An analytic tridiagonal Jacobian, SciPy's banded linear solve and damped Newton steps solve the nonlinear system. Residuals are divided by volume before convergence testing; otherwise refining the mesh could make a poorly solved equation appear converged. Failures raise a convergence error. Electric field at cell faces is calculated from potential differences, allowing a discrete Gauss-law conservation check. Node fields are centered derivatives for visualization.

An independent validation uses SciPy `solve_bvp`: each side is mapped to a unit interval and the four-state system enforces both contact values plus continuity of potential and field at the interface. This handles the doping discontinuity explicitly instead of smoothing it. It shares the physical model but not the finite-volume/Newton implementation.

### A second independent check: the full-Boltzmann first integral

For semi-infinite neutral contacts, multiply the differential equation by $du/dx$ and integrate once on each side. Set $S_L=2n_i\cosh u_L$ and $S_R=2n_i\cosh u_R$, both in cm⁻³. Matching field at the interface gives

$$u_0=\frac{S_L-S_R+N_Au_L+N_Du_R}{N_A+N_D},$$
$$E_0=-\sqrt{\frac{2q10^6V_T}{\varepsilon}
\left[2n_i\cosh u_0-S_L+N_A(u_0-u_L)\right]}.$$

Here $u_0$ is the dimensionless interface potential and $E_0$ is the signed field in V/m. The bracket is a density in cm⁻³. The left-referenced interface potential is $V_T(u_0-u_L)$ V. These analytical relations retain mobile charge; they are **not** the depletion approximation. Small numerical differences arise from mesh spacing and finite contact placement.

On the lightly doped side close to a strongly asymmetric interface, mobile charge can compete with or exceed fixed dopant charge. An accurately solved Poisson–Boltzmann model can therefore differ substantially from the depletion approximation, especially in interface field. Mesh refinement removes discretization error; it cannot remove different physical assumptions. The second-order convergence claim concerns potential. Differentiation at the abrupt interface gives slower field convergence, which is checked separately.

## Separate compact diode model

For forward bias, assume a single ideality factor $\eta$, saturation current $I_s$ (A), series resistance $R_s$ (Ω) and known uniform $T$:

$$I=I_s\left[\exp\left(\frac{V-IR_s}{\eta V_T}\right)-1\right],\qquad
V(I)=\eta V_T\ln(1+I/I_s)+IR_s.$$

$I$ is current in A and $V$ terminal voltage in V. The first expression combines the ideal diode relation with Kirchhoff's voltage law for the series resistor. No junction area, diffusion lengths, mobility or recombination model is inferred from the equilibrium calculation. The fit parameters are effective descriptions; $\eta$ alone does not establish a microscopic transport mechanism.

The fitting measurement convention is **controlled current with negligible current error and independent Gaussian voltage errors of known standard deviation** $\sigma_V$ (V). Weighted least squares minimizes $\sum[(V_\mathrm{model}-V_\mathrm{data})/\sigma_V]^2$. This is not an error model for a voltage-controlled experiment with noisy current. Such data require a different likelihood.

Fit variables are $(\ln I_s,\eta,R_s)$, with bounded trust-region least squares and an analytic Jacobian. Logarithmic $I_s$ preserves positivity. Local covariance is obtained from the weighted Jacobian via singular-value decomposition, with **absolute supplied voltage uncertainties**, not residual rescaling. Covariance is unavailable at active bounds or numerical rank deficiency. Correlations and a column-normalized condition number flag weak identifiability; local errors exclude temperature uncertainty and model discrepancy and are not guaranteed global confidence intervals. See [SciPy least_squares](https://docs.scipy.org/doc/scipy/reference/generated/scipy.optimize.least_squares.html) for the numerical algorithm.

The inverse current calculation brackets a scalar root in $y=\ln(1+I/I_s)$ to avoid uncontrolled exponential iteration. It accepts terminal voltages 0–5 V, which bounds exponential evaluation but does not certify physical accuracy at high bias. Search bounds are $10^{-18}\le I_s\le10^{-3}$ A, $0.5\le\eta\le4$ and $0\le R_s\le10^5$ Ω. These are explicit engineering search limits, not universal physical limits. Temperature is restricted to 250–400 K. The fitted current observations must be strictly positive; the model evaluation also accepts zero current.

Reverse breakdown, shunt leakage, high injection and self-heating are outside the compact model. The included case study is explicitly **SYNTHETIC DATA**; no experimental validation is claimed. A noisy current-controlled dataset is generated with known current and independent 1.5 mV Gaussian voltage noise. Its truth parameters and random seed are disclosed, allowing parameter recovery to be assessed rather than just judging the visual quality of a fitted curve.
