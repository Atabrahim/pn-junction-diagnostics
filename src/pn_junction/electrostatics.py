"""Equilibrium abrupt-junction Poisson–Boltzmann solver and analytical comparison."""

from dataclasses import dataclass

import numpy as np
from numpy.typing import ArrayLike, NDArray
from scipy.constants import e
from scipy.linalg import solve_banded

from .material import Silicon, silicon


class ConvergenceError(RuntimeError):
    """A numerical solution did not meet the requested convergence criterion."""


@dataclass(frozen=True)
class Junction:
    """Uniform p/n doping, fully ionized, in the restricted silicon model."""

    acceptor_cm3: float = 1e16
    donor_cm3: float = 1e16
    temperature_K: float = 300.0

    def __post_init__(self) -> None:
        silicon(self.temperature_K)
        for name in ("acceptor_cm3", "donor_cm3"):
            density = getattr(self, name)
            if not np.isfinite(density) or not 1e14 <= density <= 1e17:
                raise ValueError(f"{name} must be finite and in [1e14, 1e17] cm^-3")

    @property
    def material(self) -> Silicon:
        return silicon(self.temperature_K)

    @property
    def bulk_reduced_potentials(self) -> tuple[float, float]:
        """Dimensionless u=(E_F-E_i)/(kT) at neutral left/right contacts."""
        intrinsic_cm3 = self.material.intrinsic_cm3
        return (
            float(np.arcsinh(-self.acceptor_cm3 / (2 * intrinsic_cm3))),
            float(np.arcsinh(self.donor_cm3 / (2 * intrinsic_cm3))),
        )

    @property
    def built_in_voltage_V(self) -> float:
        left, right = self.bulk_reduced_potentials
        return self.material.thermal_voltage_V * (right - left)


@dataclass(frozen=True)
class Depletion:
    """Analytical depletion widths and peak field magnitude (SI units)."""

    p_width_m: float
    n_width_m: float
    peak_field_V_m: float

    @property
    def width_m(self) -> float:
        return self.p_width_m + self.n_width_m


def depletion_approximation(junction: Junction) -> Depletion:
    """Compute charge-balanced widths using exact bulk built-in potential."""
    permittivity = junction.material.permittivity_F_m
    width_m = np.sqrt(
        2
        * permittivity
        * junction.built_in_voltage_V
        / (e * 1e6)
        * (1 / junction.acceptor_cm3 + 1 / junction.donor_cm3)
    )
    p_width_m = width_m * junction.donor_cm3 / (junction.acceptor_cm3 + junction.donor_cm3)
    n_width_m = width_m - p_width_m
    return Depletion(
        p_width_m, n_width_m, e * 1e6 * junction.acceptor_cm3 * p_width_m / permittivity
    )


def depletion_profile(junction: Junction, position_m: ArrayLike) -> tuple[NDArray, NDArray]:
    """Return analytical left-referenced potential (V) and signed field (V/m)."""
    position_m = np.asarray(position_m, dtype=float)
    if not np.all(np.isfinite(position_m)):
        raise ValueError("position_m must be finite")
    depletion = depletion_approximation(junction)
    factor = e * 1e6 / junction.material.permittivity_F_m
    left_distance_m = np.clip(position_m + depletion.p_width_m, 0, depletion.p_width_m)
    right_distance_m = np.clip(depletion.n_width_m - position_m, 0, depletion.n_width_m)
    potential_V = np.where(
        position_m <= 0,
        factor * junction.acceptor_cm3 * left_distance_m**2 / 2,
        junction.built_in_voltage_V - factor * junction.donor_cm3 * right_distance_m**2 / 2,
    )
    field_V_m = np.where(
        position_m <= 0,
        -factor * junction.acceptor_cm3 * left_distance_m,
        -factor * junction.donor_cm3 * right_distance_m,
    )
    return potential_V, field_V_m


@dataclass(frozen=True)
class EquilibriumResult:
    """Node profiles and face fields; energy zero is the equilibrium Fermi level."""

    junction: Junction
    position_m: NDArray
    potential_V: NDArray
    field_V_m: NDArray
    face_field_V_m: NDArray
    electron_cm3: NDArray
    hole_cm3: NDArray
    charge_C_m3: NDArray
    conduction_band_eV: NDArray
    valence_band_eV: NDArray
    reduced_potential: NDArray
    iterations: int
    scaled_residual: float

    @property
    def gauss_error_C_m2(self) -> float:
        """Integrated interior charge minus net face flux; discrete Gauss law."""
        volumes_m = (self.position_m[2:] - self.position_m[:-2]) / 2
        integrated_charge = np.dot(self.charge_C_m3[1:-1], volumes_m)
        flux = self.junction.material.permittivity_F_m * (
            self.face_field_V_m[-1] - self.face_field_V_m[0]
        )
        return float(integrated_charge - flux)


def _mesh(junction: Junction, cells_per_side: int, padding_debye: float) -> NDArray:
    depletion = depletion_approximation(junction)
    material = junction.material
    debye_m = np.sqrt(
        material.permittivity_F_m
        * material.thermal_voltage_V
        / (e * 1e6 * np.array([junction.acceptor_cm3, junction.donor_cm3]))
    )
    left_m = depletion.p_width_m + padding_debye * debye_m[0]
    right_m = depletion.n_width_m + padding_debye * debye_m[1]
    return np.concatenate(
        [
            np.linspace(-left_m, 0, cells_per_side + 1),
            np.linspace(0, right_m, cells_per_side + 1)[1:],
        ]
    )


def solve_equilibrium(
    junction: Junction | None = None,
    *,
    cells_per_side: int = 400,
    padding_debye: float = 12.0,
    residual_tolerance: float = 1e-9,
    max_iterations: int = 80,
) -> EquilibriumResult:
    """Solve zero-bias Poisson–Boltzmann with conservative finite volumes.

    The mesh has 2*cells_per_side+1 nodes. Contact padding is measured in
    majority-density Debye lengths beyond analytical depletion edges.
    Residual tolerance is dimensionless; it is not an experimental error.
    Raises ConvergenceError rather than returning an unconverged profile.
    """
    if junction is None:
        junction = Junction()
    if isinstance(cells_per_side, bool) or not isinstance(cells_per_side, (int, np.integer)):
        raise ValueError("cells_per_side must be an integer")
    if not 20 <= cells_per_side <= 5000:
        raise ValueError("cells_per_side must be between 20 and 5000")
    if not np.isfinite(padding_debye) or not 4 <= padding_debye <= 40:
        raise ValueError("padding_debye must be finite and between 4 and 40")
    if not np.isfinite(residual_tolerance) or not 1e-12 <= residual_tolerance <= 1e-5:
        raise ValueError("residual_tolerance must be in [1e-12, 1e-5]")
    if isinstance(max_iterations, bool) or not isinstance(max_iterations, (int, np.integer)):
        raise ValueError("max_iterations must be an integer")
    if not 1 <= max_iterations <= 200:
        raise ValueError("max_iterations must be between 1 and 200")
    material = junction.material
    density_scale = max(junction.acceptor_cm3, junction.donor_cm3)
    length_scale_m = np.sqrt(
        material.permittivity_F_m * material.thermal_voltage_V / (e * 1e6 * density_scale)
    )
    position_m = _mesh(junction, cells_per_side, padding_debye)
    spacing = np.diff(position_m) / length_scale_m
    left_h, right_h = spacing[:-1], spacing[1:]
    volume = (left_h + right_h) / 2
    doping_cm3 = np.where(position_m < 0, -junction.acceptor_cm3, junction.donor_cm3)
    interface = cells_per_side
    doping_cm3[interface] = (
        -junction.acceptor_cm3 * spacing[interface - 1]
        + junction.donor_cm3 * spacing[interface]
    ) / (spacing[interface - 1] + spacing[interface])
    left_bulk, right_bulk = junction.bulk_reduced_potentials
    reduced = (
        depletion_profile(junction, position_m)[0] / material.thermal_voltage_V + left_bulk
    )
    reduced[0], reduced[-1] = left_bulk, right_bulk

    def residual(candidate: NDArray) -> tuple[NDArray, NDArray]:
        electrons = material.intrinsic_cm3 * np.exp(candidate[1:-1])
        holes = material.intrinsic_cm3 * np.exp(-candidate[1:-1])
        charge_scaled = (holes - electrons + doping_cm3[1:-1]) / density_scale
        flux_difference = (
            np.diff(candidate)[1:] / right_h - np.diff(candidate)[:-1] / left_h
        ) / volume
        return flux_difference + charge_scaled, (electrons + holes) / density_scale

    for iteration in range(max_iterations + 1):
        residual_vector, mobile_scaled = residual(reduced)
        residual_norm = float(np.max(np.abs(residual_vector)))
        if residual_norm <= residual_tolerance:
            break
        if iteration == max_iterations:
            raise ConvergenceError(
                f"Newton failed after {iteration} steps: residual {residual_norm:.3e}"
            )
        banded = np.zeros((3, len(reduced) - 2))
        banded[1] = -(1 / left_h + 1 / right_h) / volume - mobile_scaled
        banded[0, 1:] = 1 / (right_h[:-1] * volume[:-1])
        banded[2, :-1] = 1 / (left_h[1:] * volume[1:])
        step = solve_banded((1, 1), banded, -residual_vector)
        damping = min(1.0, 3.0 / max(float(np.max(np.abs(step))), 3.0))
        for _ in range(30):
            trial = reduced.copy()
            trial[1:-1] += damping * step
            if np.min(trial) >= left_bulk - 1 and np.max(trial) <= right_bulk + 1:
                trial_norm = np.max(np.abs(residual(trial)[0]))
                if trial_norm < residual_norm:
                    reduced = trial
                    break
            damping /= 2
        else:
            raise ConvergenceError(
                f"Newton line search stalled at residual {residual_norm:.3e}"
            )

    electron_cm3 = material.intrinsic_cm3 * np.exp(reduced)
    hole_cm3 = material.intrinsic_cm3 * np.exp(-reduced)
    potential_V = material.thermal_voltage_V * (reduced - left_bulk)
    face_field_V_m = -np.diff(potential_V) / np.diff(position_m)
    conduction_band_eV = material.thermal_voltage_V * (
        np.log(material.conduction_dos_cm3 / material.intrinsic_cm3) - reduced
    )
    return EquilibriumResult(
        junction,
        position_m,
        potential_V,
        -np.gradient(potential_V, position_m, edge_order=2),
        face_field_V_m,
        electron_cm3,
        hole_cm3,
        e * 1e6 * (hole_cm3 - electron_cm3 + doping_cm3),
        conduction_band_eV,
        conduction_band_eV - material.bandgap_eV,
        reduced,
        iteration,
        residual_norm,
    )
