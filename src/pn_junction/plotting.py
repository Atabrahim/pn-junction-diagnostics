"""Scientific figures; Matplotlib is needed only for the optional plots extra."""

import matplotlib.pyplot as plt
import numpy as np

from .diode import DiodeFit
from .electrostatics import EquilibriumResult, depletion_profile

_STYLE = {
    "font.size": 10,
    "axes.titlesize": 11,
    "axes.labelsize": 10,
    "legend.fontsize": 8.5,
    "axes.spines.top": False,
    "axes.spines.right": False,
    "axes.grid": True,
    "grid.alpha": 0.2,
    "figure.facecolor": "white",
    "svg.fonttype": "none",
    "svg.hashsalt": "pn-junction-diagnostics",
}
_BLUE, _ORANGE, _TEAL = "#2166ac", "#d95f02", "#16817a"


def plot_equilibrium(result: EquilibriumResult):
    """Potential, field, carrier densities and bands; return the Matplotlib figure."""
    with plt.rc_context(_STYLE):
        figure, axes = plt.subplots(2, 2, figsize=(10.5, 7.2), layout="constrained")
        position_um = result.position_m * 1e6
        analytical_potential, analytical_field = depletion_profile(
            result.junction, result.position_m
        )
        axes[0, 0].plot(
            position_um, result.potential_V, color=_BLUE, label="Numerical Boltzmann"
        )
        axes[0, 0].plot(
            position_um, analytical_potential, "--", color=_ORANGE, label="Analytical depletion"
        )
        axes[0, 0].set(
            ylabel="Potential relative to p contact (V)",
            title="(a) Internal built-in potential",
        )
        face_position_um = (position_um[1:] + position_um[:-1]) / 2
        axes[0, 1].plot(
            face_position_um,
            result.face_field_V_m / 1e5,
            color=_BLUE,
            label="Numerical, cell faces",
        )
        axes[0, 1].plot(
            position_um,
            analytical_field / 1e5,
            "--",
            color=_ORANGE,
            label="Analytical depletion",
        )
        axes[0, 1].set(ylabel="Electric field (kV/cm)", title="(b) Field points from n to p")
        axes[1, 0].semilogy(position_um, result.electron_cm3, color=_BLUE, label="Electrons, n")
        axes[1, 0].semilogy(position_um, result.hole_cm3, color=_ORANGE, label="Holes, p")
        axes[1, 0].axhline(
            result.junction.material.intrinsic_cm3,
            color=_TEAL,
            linestyle=":",
            label="Model intrinsic density",
        )
        axes[1, 0].set(
            ylabel=r"Carrier density (cm$^{-3}$)", title="(c) Equilibrium mass action: np = ni²"
        )
        axes[1, 1].plot(position_um, result.conduction_band_eV, color=_BLUE, label=r"$E_c$")
        axes[1, 1].plot(position_um, result.valence_band_eV, color=_ORANGE, label=r"$E_v$")
        axes[1, 1].axhline(0, color=_TEAL, linestyle="--", label=r"$E_F = 0$")
        axes[1, 1].set(
            ylabel="Energy relative to Fermi level (eV)",
            title="(d) Flat Fermi level at equilibrium",
        )
        for axis in axes.flat:
            axis.axvline(0, color="0.55", linewidth=0.7, linestyle=":")
            axis.set_xlabel("Position from junction (µm); p ← 0 → n")
            axis.legend(loc="best")
        junction = result.junction
        figure.suptitle(
            f"Silicon PN junction at equilibrium · {junction.temperature_K:g} K\n"
            f"Na = {junction.acceptor_cm3:.0e} cm⁻³, Nd = {junction.donor_cm3:.0e} cm⁻³ · "
            f"{len(position_um)} nodes · fully ionized dopants",
            fontsize=13,
        )
    return figure


def plot_diode_fit(
    current_A, voltage_V, sigma_voltage_V, result: DiodeFit, *, data_label="INPUT DATA"
):
    """Curve, residuals and local correlation; caller supplies the data provenance label."""
    with plt.rc_context(_STYLE):
        figure = plt.figure(figsize=(10.5, 7.2), layout="constrained")
        grid = figure.add_gridspec(2, 2, height_ratios=[1.2, 1])
        curve = figure.add_subplot(grid[0, :])
        residual = figure.add_subplot(grid[1, 0])
        correlation = figure.add_subplot(grid[1, 1])
        current_mA = np.asarray(current_A) * 1e3
        curve.set_xscale("log")
        curve.errorbar(
            current_mA,
            voltage_V,
            yerr=sigma_voltage_V,
            fmt=".",
            ms=4,
            color=_ORANGE,
            alpha=0.8,
            label="Input observations ± 1σ voltage uncertainty",
        )
        curve.plot(
            current_mA,
            result.predicted_voltage_V,
            color=_BLUE,
            label="Numerical compact-model fit",
        )
        curve.set(
            xlabel="Controlled forward current (mA)",
            ylabel="Terminal voltage (V)",
            title="(a) Forward diode model with series resistance",
        )
        curve.legend(loc="upper left")
        residual.semilogx(current_mA, result.standardized_residuals, ".", color=_BLUE)
        residual.axhline(0, color="0.3", linewidth=0.8)
        residual.axhspan(-2, 2, color=_TEAL, alpha=0.08)
        residual.set(
            xlabel="Controlled forward current (mA)",
            ylabel="(Observed − fitted) / σV",
            title=f"(b) Residuals · reduced χ² = {result.reduced_chi_square:.3f}",
        )
        if result.correlation is not None:
            raster = correlation.imshow(result.correlation, vmin=-1, vmax=1, cmap="RdBu_r")
            for row in range(3):
                for column in range(3):
                    value = result.correlation[row, column]
                    correlation.text(
                        column,
                        row,
                        f"{value:.2f}",
                        ha="center",
                        va="center",
                        color="white" if abs(value) > 0.65 else "black",
                    )
            figure.colorbar(raster, ax=correlation, label="Correlation coefficient", shrink=0.8)
        else:
            correlation.text(
                0.5, 0.5, "Covariance unavailable", ha="center", transform=correlation.transAxes
            )
        correlation.grid(False)
        correlation.set(
            xticks=[0, 1, 2],
            yticks=[0, 1, 2],
            xticklabels=["Is", "η", "Rs"],
            yticklabels=["Is", "η", "Rs"],
            title="(c) Local parameter correlation",
        )
        figure.suptitle(
            f"{data_label} · current-controlled diode diagnostics\n"
            f"{result.parameters.temperature_K:g} K · known independent voltage uncertainties",
            fontsize=13,
        )
    return figure


def plot_verification(mesh_studies: list[dict], asymmetry: list[dict]):
    """Separate discretization convergence from depletion-model discrepancy."""
    with plt.rc_context(_STYLE):
        figure, axes = plt.subplots(1, 2, figsize=(10.5, 4.5), layout="constrained")
        for study in mesh_studies:
            axes[0].loglog(
                study["cells_per_side"],
                np.array(study["error_V"]) * 1e3,
                "o-",
                label=study["label"],
            )
        cells = np.asarray(mesh_studies[0]["cells_per_side"])
        guide = mesh_studies[0]["error_V"][0] * 1e3 * (cells[0] / cells) ** 2
        axes[0].loglog(cells, guide, "--", color="0.4", label="Second-order guide")
        axes[0].set(
            xlabel="Mesh intervals per side",
            ylabel="Maximum potential error (mV)",
            title="(a) Error against independent collocation",
        )
        axes[0].legend()
        ratios = [entry["donor_acceptor_ratio"] for entry in asymmetry]
        axes[1].semilogx(
            ratios,
            [entry["numerical_field_ratio"] for entry in asymmetry],
            "o",
            color=_BLUE,
            label="Numerical interface field / depletion peak",
        )
        axes[1].semilogx(
            ratios,
            [entry["first_integral_field_ratio"] for entry in asymmetry],
            "-",
            color=_ORANGE,
            label="Full-Boltzmann first integral / depletion peak",
        )
        axes[1].axhline(1, color="0.5", linestyle="--", label="Depletion approximation")
        axes[1].set(
            xlabel="Doping ratio Nd / Na (Na = 10¹⁴ cm⁻³)",
            ylabel="Field magnitude ratio",
            title="(b) Model discrepancy persists on a fine mesh",
        )
        axes[1].legend(loc="upper left", fontsize=7.5)
        figure.suptitle(
            "Numerical verification and depletion-approximation limits · 300 K", fontsize=13
        )
    return figure
