"""Thin command-line interface; CSV headers and JSON fields carry explicit units."""

import argparse
import csv
import json
from dataclasses import asdict
from pathlib import Path

import numpy as np

from . import __version__
from .diode import DiodeFit, fit_diode
from .electrostatics import (
    ConvergenceError,
    Junction,
    depletion_approximation,
    solve_equilibrium,
)


def fit_summary(result: DiodeFit) -> dict:
    """JSON-compatible fit diagnostics; covariance order is documented explicitly."""
    return {
        "result_type": "NUMERICAL FIT; input provenance is supplied by the user",
        "measurement_model": "controlled current; known independent Gaussian voltage errors",
        "parameters": asdict(result.parameters),
        "parameter_order": ["saturation_current_A", "ideality_factor", "series_resistance_ohm"],
        "standard_errors": None
        if result.standard_errors is None
        else result.standard_errors.tolist(),
        "covariance": None if result.covariance is None else result.covariance.tolist(),
        "correlation": None if result.correlation is None else result.correlation.tolist(),
        "reduced_chi_square": result.reduced_chi_square,
        "scaled_jacobian_condition": result.scaled_jacobian_condition,
        "warnings": list(result.warnings),
    }


def read_diode_csv(path: Path) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    """Read required current_A, voltage_V, sigma_voltage_V columns without guessing units."""
    columns = ("current_A", "voltage_V", "sigma_voltage_V")
    with path.open(newline="", encoding="utf-8") as handle:
        reader = csv.DictReader(handle)
        if reader.fieldnames is None or any(name not in reader.fieldnames for name in columns):
            raise ValueError("CSV requires current_A, voltage_V and sigma_voltage_V headers")
        rows = []
        for line, row in enumerate(reader, start=2):
            try:
                rows.append([float(row[name]) for name in columns])
            except (ValueError, TypeError) as error:
                raise ValueError(f"Invalid numeric CSV value on line {line}") from error
    if not rows:
        raise ValueError("CSV contains no observations")
    return tuple(np.asarray(rows).T)


def main(argv: list[str] | None = None) -> int:
    """Execute a simulation or fit; exit 2 on invalid input or failed convergence."""
    parser = argparse.ArgumentParser(
        description="Equilibrium PN junctions and separate diode diagnostics"
    )
    parser.add_argument("--version", action="version", version=__version__)
    commands = parser.add_subparsers(dest="command", required=True)
    simulate = commands.add_parser(
        "simulate", help="write numerical equilibrium profiles to CSV"
    )
    simulate.add_argument("--acceptor-cm3", type=float, default=1e16)
    simulate.add_argument("--donor-cm3", type=float, default=1e16)
    simulate.add_argument("--temperature-k", type=float, default=300)
    simulate.add_argument("--cells", type=int, default=400, help="mesh intervals on each side")
    simulate.add_argument("--padding-debye", type=float, default=12)
    simulate.add_argument("--output", type=Path, required=True)
    fit = commands.add_parser(
        "fit", help="fit a current-controlled I-V CSV with known voltage noise"
    )
    fit.add_argument("csv", type=Path)
    fit.add_argument("--temperature-k", type=float, default=300)
    fit.add_argument("--output", type=Path, required=True)
    args = parser.parse_args(argv)
    try:
        if args.command == "simulate":
            junction = Junction(args.acceptor_cm3, args.donor_cm3, args.temperature_k)
            result = solve_equilibrium(
                junction, cells_per_side=args.cells, padding_debye=args.padding_debye
            )
            profiles = np.column_stack(
                [
                    result.position_m,
                    result.potential_V,
                    result.field_V_m,
                    result.electron_cm3,
                    result.hole_cm3,
                    result.charge_C_m3,
                    result.conduction_band_eV,
                    result.valence_band_eV,
                ]
            )
            args.output.parent.mkdir(parents=True, exist_ok=True)
            np.savetxt(
                args.output,
                profiles,
                delimiter=",",
                comments="",
                header=(
                    "position_m,potential_V,field_V_m,electron_cm3,hole_cm3,charge_C_m3,"
                    "conduction_band_eV,valence_band_eV"
                ),
            )
            summary = {
                "result_type": "NUMERICAL EQUILIBRIUM SIMULATION",
                "junction": asdict(junction),
                "nodes": len(result.position_m),
                "built_in_voltage_V": junction.built_in_voltage_V,
                "analytical_depletion_width_m": depletion_approximation(junction).width_m,
                "scaled_residual": result.scaled_residual,
                "gauss_error_C_m2": result.gauss_error_C_m2,
                "output": str(args.output),
            }
        else:
            observations = read_diode_csv(args.csv)
            result = fit_diode(*observations, temperature_K=args.temperature_k)
            summary = fit_summary(result)
            summary["input_file"] = str(args.csv)
            serialized = json.dumps(summary, indent=2, allow_nan=False)
            args.output.parent.mkdir(parents=True, exist_ok=True)
            args.output.write_text(serialized + "\n", encoding="utf-8")
        print(json.dumps(summary, indent=2, allow_nan=False))
    except (OSError, ValueError, ConvergenceError) as error:
        parser.exit(2, f"error: {error}\n")
    return 0
