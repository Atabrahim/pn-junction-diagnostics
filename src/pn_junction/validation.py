"""Independent numerical reference for the equilibrium boundary-value problem."""

import numpy as np
from numpy.typing import NDArray
from scipy.constants import e
from scipy.integrate import solve_bvp

from .electrostatics import ConvergenceError, EquilibriumResult, Junction, depletion_profile


def interface_first_integral(junction: Junction) -> tuple[float, float]:
    """Analytical Boltzmann interface potential (V) and signed field (V/m).

    Integrating u'' once on each side and matching field yields the result
    for semi-infinite neutral bulks. Unlike the depletion approximation,
    this includes mobile charge. It is independent of both numerical solvers.
    """
    material = junction.material
    left, right = junction.bulk_reduced_potentials
    acceptors, donors = junction.acceptor_cm3, junction.donor_cm3
    left_mobile = np.hypot(acceptors, 2 * material.intrinsic_cm3)
    right_mobile = np.hypot(donors, 2 * material.intrinsic_cm3)
    interface = (left_mobile - right_mobile + acceptors * left + donors * right) / (
        acceptors + donors
    )
    integrated_density = (
        2 * material.intrinsic_cm3 * np.cosh(interface)
        - left_mobile
        + acceptors * (interface - left)
    )
    field = -np.sqrt(
        2
        * e
        * 1e6
        * material.thermal_voltage_V
        * integrated_density
        / material.permittivity_F_m
    )
    return material.thermal_voltage_V * (interface - left), float(field)


def collocation_potential(result: EquilibriumResult, tolerance: float = 1e-7) -> NDArray:
    """Independent collocation potential (V) on a finite-volume solution's mesh.

    Two subdomains avoid placing a discontinuous source inside a smooth
    collocation interval. Only geometry and material parameters are reused;
    the initial guess is analytical, not the finite-volume solution.
    """
    if not np.isfinite(tolerance) or not 1e-10 <= tolerance <= 1e-3:
        raise ValueError("tolerance must be between 1e-10 and 1e-3")
    junction = result.junction
    material = junction.material
    left_m, right_m = -result.position_m[0], result.position_m[-1]
    left_bulk, right_bulk = junction.bulk_reduced_potentials
    density_scale = max(junction.acceptor_cm3, junction.donor_cm3)
    length_scale_squared = (
        material.permittivity_F_m * material.thermal_voltage_V / (e * 1e6 * density_scale)
    )
    left_factor, right_factor = (
        left_m**2 / length_scale_squared,
        right_m**2 / length_scale_squared,
    )

    def equations(coordinate: NDArray, state: NDArray) -> NDArray:
        del coordinate
        left_mobile = -2 * material.intrinsic_cm3 * np.sinh(state[0])
        right_mobile = -2 * material.intrinsic_cm3 * np.sinh(state[2])
        return np.vstack(
            [
                state[1],
                -left_factor * (left_mobile - junction.acceptor_cm3) / density_scale,
                state[3],
                -right_factor * (right_mobile + junction.donor_cm3) / density_scale,
            ]
        )

    def boundary(left: NDArray, right: NDArray) -> NDArray:
        return np.array(
            [
                left[0] - left_bulk,
                right[2] - right_bulk,
                right[0] - left[2],
                right[1] - left[3] * left_m / right_m,
            ]
        )

    coordinate = np.linspace(0, 1, 151)
    left_potential, left_field = depletion_profile(junction, left_m * (coordinate - 1))
    right_potential, right_field = depletion_profile(junction, right_m * coordinate)
    initial = np.vstack(
        [
            left_potential / material.thermal_voltage_V + left_bulk,
            -left_field * left_m / material.thermal_voltage_V,
            right_potential / material.thermal_voltage_V + left_bulk,
            -right_field * right_m / material.thermal_voltage_V,
        ]
    )
    solution = solve_bvp(
        equations, boundary, coordinate, initial, tol=tolerance, max_nodes=12000
    )
    if not solution.success:
        raise ConvergenceError(f"Independent collocation failed: {solution.message}")
    positions = result.position_m
    reduced = np.empty_like(positions)
    is_left = positions <= 0
    reduced[is_left] = solution.sol(1 + positions[is_left] / left_m)[0]
    reduced[~is_left] = solution.sol(positions[~is_left] / right_m)[2]
    return material.thermal_voltage_V * (reduced - left_bulk)
