"""Separate compact forward diode model and current-controlled voltage fitting."""

from dataclasses import dataclass

import numpy as np
from numpy.typing import ArrayLike, NDArray
from scipy.optimize import brentq, least_squares
from scipy.special import expit

from .electrostatics import ConvergenceError
from .material import silicon

# Engineering search limits, not universal physical limits; see docs/MODEL.md.
_LOWER = np.array([np.log(1e-18), 0.5, 0.0])
_UPPER = np.array([np.log(1e-3), 4.0, 1e5])


@dataclass(frozen=True)
class DiodeParameters:
    """Effective Is (A), ideality (dimensionless), Rs (ohm) and known T (K)."""

    saturation_current_A: float = 1e-11
    ideality_factor: float = 1.6
    series_resistance_ohm: float = 5.0
    temperature_K: float = 300.0

    def __post_init__(self) -> None:
        silicon(self.temperature_K)
        for name, lower, upper in (
            ("saturation_current_A", 1e-18, 1e-3),
            ("ideality_factor", 0.5, 4),
            ("series_resistance_ohm", 0, 1e5),
        ):
            value = getattr(self, name)
            if not np.isfinite(value) or not lower <= value <= upper:
                raise ValueError(f"{name} must be finite and in [{lower}, {upper}]")


def voltage_at_current(current_A: ArrayLike, parameters: DiodeParameters) -> NDArray:
    """Forward terminal voltage (V) for nonnegative imposed current (A).

    V = eta*V_T*log(1 + I/Is) + I*Rs. This is a compact model;
    it excludes breakdown, high injection and self-heating.
    """
    current = np.asarray(current_A, dtype=float)
    if not np.all(np.isfinite(current)) or np.any(current < 0):
        raise ValueError("current_A must be finite and nonnegative")
    with np.errstate(divide="ignore", over="ignore", invalid="ignore"):
        logarithm = np.logaddexp(0, np.log(current) - np.log(parameters.saturation_current_A))
        voltage = (
            parameters.ideality_factor
            * silicon(parameters.temperature_K).thermal_voltage_V
            * logarithm
            + current * parameters.series_resistance_ohm
        )
    if not np.all(np.isfinite(voltage)):
        raise ValueError("current_A produces voltage outside floating-point range")
    return voltage


def current_at_voltage(voltage_V: ArrayLike, parameters: DiodeParameters) -> NDArray:
    """Solve the implicit forward-current equation for 0 <= voltage_V <= 5 V.

    Bracket in y=log(1+I/Is), where the scalar equation is monotonic.
    The 5 V cap bounds exponential evaluation; it does not certify model validity.
    """
    voltage = np.asarray(voltage_V, dtype=float)
    if not np.all(np.isfinite(voltage)) or np.any(voltage < 0) or np.any(voltage > 5):
        raise ValueError("voltage_V must be finite and between 0 and 5 V")
    thermal_factor = (
        parameters.ideality_factor * silicon(parameters.temperature_K).thermal_voltage_V
    )
    saturation = parameters.saturation_current_A
    resistance = parameters.series_resistance_ohm

    def solve_one(bias_V: float) -> float:
        if bias_V == 0:
            return 0.0
        if resistance == 0:
            return saturation * np.expm1(bias_V / thermal_factor)
        reduced = brentq(
            lambda value: (
                thermal_factor * value + resistance * saturation * np.expm1(value) - bias_V
            ),
            0,
            bias_V / thermal_factor,
            xtol=1e-13,
            rtol=1e-13,
        )
        return saturation * np.expm1(reduced)

    return np.array([solve_one(float(bias)) for bias in voltage.flat]).reshape(voltage.shape)


@dataclass(frozen=True)
class DiodeFit:
    """Fit and local uncertainty for known independent voltage standard deviations.

    Covariance order is Is (A), eta, Rs (ohm). None means uncertainty was
    not identifiable in the interior of the search bounds. Residuals use
    (observed - predicted)/sigma. Model discrepancy is not in the covariance.
    """

    parameters: DiodeParameters
    predicted_voltage_V: NDArray
    standardized_residuals: NDArray
    covariance: NDArray | None
    correlation: NDArray | None
    reduced_chi_square: float
    scaled_jacobian_condition: float
    warnings: tuple[str, ...]

    @property
    def standard_errors(self) -> NDArray | None:
        return None if self.covariance is None else np.sqrt(np.diag(self.covariance))


def fit_diode(
    current_A: ArrayLike,
    voltage_V: ArrayLike,
    sigma_voltage_V: ArrayLike,
    *,
    temperature_K: float = 300.0,
) -> DiodeFit:
    """Fit Is, eta and Rs to a current-controlled sweep with known voltage noise.

    Provide at least five positive-current observations and positive finite
    voltage standard deviations (one scalar or one per observation). Current
    errors must be negligible. Temperature is known, not simultaneously fitted.
    """
    thermal_voltage = silicon(temperature_K).thermal_voltage_V
    current = np.asarray(current_A, dtype=float)
    voltage = np.asarray(voltage_V, dtype=float)
    if current.ndim != 1 or current.size < 5 or voltage.shape != current.shape:
        raise ValueError("current_A and voltage_V must be 1D arrays of equal length >= 5")
    if not np.all(np.isfinite(current)) or np.any(current <= 0):
        raise ValueError("fit current_A must be finite and strictly positive")
    if not np.all(np.isfinite(voltage)):
        raise ValueError("voltage_V must be finite")
    sigma = np.asarray(sigma_voltage_V, dtype=float)
    if sigma.ndim > 1 or (sigma.ndim == 1 and sigma.shape != current.shape):
        raise ValueError("sigma_voltage_V must be scalar or match the observation shape")
    sigma = np.broadcast_to(sigma, current.shape)
    if not np.all(np.isfinite(sigma)) or np.any(sigma <= 0):
        raise ValueError("sigma_voltage_V must be finite and positive")
    log_current = np.log(current)

    def prediction(variables: NDArray) -> NDArray:
        log_saturation, ideality, resistance = variables
        return (
            ideality * thermal_voltage * np.logaddexp(0, log_current - log_saturation)
            + current * resistance
        )

    def jacobian(variables: NDArray) -> NDArray:
        log_saturation, ideality, _ = variables
        return (
            np.column_stack(
                [
                    -ideality * thermal_voltage * expit(log_current - log_saturation),
                    thermal_voltage * np.logaddexp(0, log_current - log_saturation),
                    current,
                ]
            )
            / sigma[:, None]
        )

    # High-forward-bias linearization supplies a data-based starting estimate.
    design = np.column_stack([np.ones_like(current), log_current, current]) / sigma[:, None]
    intercept, slope, resistance = np.linalg.lstsq(design, voltage / sigma, rcond=None)[0]
    ideality = np.clip(slope / thermal_voltage, 0.6, 3.8)
    start = np.array([-intercept / (ideality * thermal_voltage), ideality, resistance])
    start = np.clip(start, _LOWER + 1e-6, _UPPER - 1e-6)
    optimized = least_squares(
        lambda variables: (prediction(variables) - voltage) / sigma,
        start,
        jac=jacobian,
        bounds=(_LOWER, _UPPER),
        x_scale="jac",
        ftol=1e-12,
        xtol=1e-12,
        gtol=1e-10,
        max_nfev=1000,
    )
    if not optimized.success:
        raise ConvergenceError(f"Diode parameter fit failed: {optimized.message}")
    parameters = DiodeParameters(
        float(np.exp(optimized.x[0])),
        float(optimized.x[1]),
        float(optimized.x[2]),
        temperature_K,
    )
    weighted_jacobian = jacobian(optimized.x)
    column_norms = np.linalg.norm(weighted_jacobian, axis=0)
    _, singular_values, right_vectors = np.linalg.svd(
        weighted_jacobian / column_norms, full_matrices=False
    )
    condition = float(singular_values[0] / max(singular_values[-1], np.finfo(float).tiny))
    warnings = []
    covariance = correlation = None
    if singular_values[-1] < singular_values[0] * 1e-10:
        warnings.append("Rank-deficient fit: parameter covariance is unavailable.")
    elif np.any(optimized.active_mask) or np.any(
        np.isclose(optimized.x, _LOWER, rtol=0, atol=1e-7)
    ):
        warnings.append(
            "Fit reaches a parameter bound: interior Gaussian covariance is unavailable."
        )
    else:
        scaled_inverse = right_vectors.T / singular_values
        covariance_variables = (scaled_inverse @ scaled_inverse.T) / np.outer(
            column_norms, column_norms
        )
        transform = np.array([parameters.saturation_current_A, 1.0, 1.0])
        covariance = covariance_variables * np.outer(transform, transform)
        standard_errors = np.sqrt(np.diag(covariance))
        correlation = covariance / np.outer(standard_errors, standard_errors)
        if np.max(np.abs(correlation - np.eye(3))) > 0.98:
            warnings.append(
                "Strong parameter correlation: interpret individual parameters cautiously."
            )
        if standard_errors[2] >= parameters.series_resistance_ohm / 2:
            warnings.append("Series resistance is weakly constrained by this current range.")
    if condition > 1e4:
        warnings.append(
            "Ill-conditioned sensitivity matrix: expand the measured current range."
        )
    residuals = (voltage - prediction(optimized.x)) / sigma
    return DiodeFit(
        parameters,
        prediction(optimized.x),
        residuals,
        covariance,
        correlation,
        float(np.dot(residuals, residuals) / (current.size - 3)),
        condition,
        tuple(warnings),
    )
