"""Reproduce all published figures, synthetic observations and validation metrics.

Run from a checkout with: python examples/reproduce.py --output outputs/reproduced
Scientific logic lives in the installed pn_junction package, not in this script.
"""

import argparse
import json
import platform
from dataclasses import asdict
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import scipy

from pn_junction import (
    DiodeParameters,
    Junction,
    depletion_approximation,
    fit_diode,
    solve_equilibrium,
    voltage_at_current,
)
from pn_junction.cli import fit_summary
from pn_junction.plotting import plot_diode_fit, plot_equilibrium, plot_verification
from pn_junction.validation import collocation_potential, interface_first_integral


def reproduce(output: Path) -> dict:
    """Write deterministic synthetic data and figures; enforce numerical acceptance gates."""
    figures, data = output / "figures", output / "data"
    figures.mkdir(parents=True, exist_ok=True)
    data.mkdir(parents=True, exist_ok=True)
    truth = DiodeParameters()
    current_A = np.geomspace(1e-9, 0.02, 100)
    sigma_V = 0.0015
    voltage_V = voltage_at_current(current_A, truth) + np.random.default_rng(2026).normal(
        0, sigma_V, 100
    )
    np.savetxt(
        data / "synthetic_diode.csv",
        np.column_stack([current_A, voltage_V, np.full_like(current_A, sigma_V)]),
        delimiter=",",
        header="current_A,voltage_V,sigma_voltage_V",
        comments="",
    )
    metadata = {
        "data_type": "SYNTHETIC DATA, not experimental measurements",
        "generator": "examples/reproduce.py; NumPy default_rng, seed 2026",
        "truth_parameters": asdict(truth),
        "observation_model": "exact current; additive independent Gaussian voltage noise",
        "sigma_voltage_V": sigma_V,
        "sample_count": len(current_A),
        "license": "MIT; generated within this repository; no external raw data",
        "preprocessing": "none",
    }
    (data / "synthetic_diode_metadata.json").write_text(
        json.dumps(metadata, indent=2) + "\n", encoding="utf-8"
    )
    diode = fit_diode(current_A, voltage_V, sigma_V)
    fitted = np.array(
        [
            diode.parameters.saturation_current_A,
            diode.parameters.ideality_factor,
            diode.parameters.series_resistance_ohm,
        ]
    )
    truth_values = np.array(
        [truth.saturation_current_A, truth.ideality_factor, truth.series_resistance_ohm]
    )
    recovery_z = np.abs(fitted - truth_values) / diode.standard_errors
    restricted = current_A <= 1e-6
    low_current_fit = fit_diode(current_A[restricted], voltage_V[restricted], sigma_V)

    cases = []
    for temperature_K in (250, 300, 400):
        for acceptor, donor in ((1e16, 1e16), (1e14, 1e17), (1e17, 1e14)):
            junction = Junction(acceptor, donor, temperature_K)
            result = solve_equilibrium(junction, cells_per_side=1600)
            reference = collocation_potential(result)
            analytical_potential, analytical_field = interface_first_integral(junction)
            error_V = float(np.max(np.abs(result.potential_V - reference)))
            interface_error_V = abs(float(result.potential_V[1600]) - analytical_potential)
            field_relative_error = abs(float(result.field_V_m[1600]) / analytical_field - 1)
            cases.append(
                {
                    **asdict(junction),
                    "nodes": len(result.position_m),
                    "collocation_max_error_V": error_V,
                    "first_integral_interface_error_V": interface_error_V,
                    "first_integral_field_relative_error": field_relative_error,
                    "scaled_residual": result.scaled_residual,
                    "gauss_error_C_m2": result.gauss_error_C_m2,
                    "passed": bool(
                        error_V < 2.5e-4
                        and interface_error_V < 2.5e-4
                        and field_relative_error < 0.005
                        and result.scaled_residual <= 1e-9
                    ),
                }
            )
    meshes = []
    for junction, label in (
        (Junction(), "Na = Nd = 10¹⁶ cm⁻³"),
        (Junction(1e15, 1e17), "Na = 10¹⁵, Nd = 10¹⁷ cm⁻³"),
    ):
        errors = []
        for cells in (100, 200, 400, 800):
            result = solve_equilibrium(junction, cells_per_side=cells)
            errors.append(
                float(np.max(np.abs(result.potential_V - collocation_potential(result))))
            )
        meshes.append(
            {
                "label": label,
                "cells_per_side": [100, 200, 400, 800],
                "error_V": errors,
                "last_refinement_ratio": errors[-2] / errors[-1],
            }
        )
    asymmetry = []
    for ratio in np.geomspace(1, 1000, 10):
        junction = Junction(1e14, min(1e17, 1e14 * ratio))
        result = solve_equilibrium(junction, cells_per_side=1600)
        peak = depletion_approximation(junction).peak_field_V_m
        asymmetry.append(
            {
                "donor_acceptor_ratio": float(ratio),
                "numerical_field_ratio": -float(result.field_V_m[1600]) / peak,
                "first_integral_field_ratio": -interface_first_integral(junction)[1] / peak,
            }
        )

    default_result = solve_equilibrium()
    default_depletion = depletion_approximation(default_result.junction)
    report = {
        "classification": "MODEL VERIFICATION; SYNTHETIC RECOVERY; no experimental validation",
        "versions": {
            "python": platform.python_version(),
            "numpy": np.__version__,
            "scipy": scipy.__version__,
            "matplotlib": matplotlib.__version__,
        },
        "default_junction": {
            "built_in_voltage_V": default_result.junction.built_in_voltage_V,
            "analytical_depletion_width_m": default_depletion.width_m,
            "numerical_peak_field_V_m": float(-default_result.field_V_m.min()),
            "analytical_depletion_peak_field_V_m": default_depletion.peak_field_V_m,
        },
        "electrostatic_cases": cases,
        "mesh_studies": meshes,
        "asymmetry_study": asymmetry,
        "diode_fit": fit_summary(diode),
        "parameter_recovery_standard_errors": recovery_z.tolist(),
        "limited_current_fit": fit_summary(low_current_fit),
        "acceptance": {
            "max_potential_error_V": 2.5e-4,
            "max_interface_field_relative_error": 0.005,
            "parameter_recovery_max_standard_errors": 3.0,
            "minimum_last_mesh_refinement_ratio": 3.5,
        },
        "passed": bool(
            all(case["passed"] for case in cases)
            and np.all(recovery_z < 3)
            and all(study["last_refinement_ratio"] > 3.5 for study in meshes)
        ),
    }
    (output / "validation_report.json").write_text(
        json.dumps(report, indent=2, allow_nan=False) + "\n", encoding="utf-8"
    )
    if not report["passed"]:
        raise RuntimeError("Reproducibility checks failed; inspect validation_report.json")
    generated = {
        "junction_equilibrium": plot_equilibrium(default_result),
        "numerical_verification": plot_verification(meshes, asymmetry),
        "diode_diagnostics": plot_diode_fit(
            current_A,
            voltage_V,
            sigma_V,
            diode,
            data_label="SYNTHETIC DATA · σV = 1.5 mV · seed 2026",
        ),
    }
    for name, figure in generated.items():
        figure.savefig(figures / f"{name}.png", dpi=180)
        figure.savefig(figures / f"{name}.svg", metadata={"Date": None})
        plt.close(figure)
    return report


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, default=Path("outputs/reproduced"))
    arguments = parser.parse_args()
    result = reproduce(arguments.output)
    print(
        json.dumps(
            {
                "passed": result["passed"],
                "electrostatic_cases": len(result["electrostatic_cases"]),
                "output": str(arguments.output),
            },
            indent=2,
        )
    )
