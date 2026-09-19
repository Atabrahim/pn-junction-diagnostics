"""Silicon equilibrium electrostatics and separate compact diode diagnostics."""

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
    "EquilibriumResult",
    "Junction",
    "Silicon",
    "depletion_approximation",
    "depletion_profile",
    "silicon",
    "solve_equilibrium",
]
