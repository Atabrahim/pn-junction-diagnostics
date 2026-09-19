"""Silicon equilibrium electrostatics and separate compact diode diagnostics."""

from .diode import DiodeFit, DiodeParameters, current_at_voltage, fit_diode, voltage_at_current
from .electrostatics import (
    ConvergenceError,
    Depletion,
    EquilibriumResult,
    Junction,
    depletion_approximation,
    depletion_profile,
    solve_equilibrium,
)
from .material import Silicon, silicon

__version__ = "0.1.0"
__all__ = [
    "ConvergenceError",
    "Depletion",
    "DiodeFit",
    "DiodeParameters",
    "EquilibriumResult",
    "Junction",
    "Silicon",
    "depletion_approximation",
    "depletion_profile",
    "current_at_voltage",
    "fit_diode",
    "silicon",
    "solve_equilibrium",
    "voltage_at_current",
]
