"""Compact-model inversion, parameter recovery and uncertainty diagnostics."""

import numpy as np
import pytest

from pn_junction import (
    DiodeParameters,
    current_at_voltage,
    fit_diode,
    silicon,
    voltage_at_current,
)


@pytest.mark.parametrize("resistance", [0, 5, 1000])
def test_implicit_current_matches_voltage_model(resistance):
    parameters = DiodeParameters(series_resistance_ohm=resistance)
    current = np.r_[0.0, np.geomspace(1e-13, 1e-3, 60)]
    voltage = voltage_at_current(current, parameters)
    np.testing.assert_allclose(
        current_at_voltage(voltage, parameters), current, rtol=1e-10, atol=1e-24
    )
    assert np.all(np.diff(voltage) > 0)
    assert float(current_at_voltage(0, parameters)) == 0


def test_zero_resistance_shockley_limit():
    parameters = DiodeParameters(series_resistance_ohm=0)
    voltage = np.linspace(0, 0.9, 40)
    expected = parameters.saturation_current_A * np.expm1(
        voltage / (parameters.ideality_factor * silicon().thermal_voltage_V)
    )
    np.testing.assert_allclose(current_at_voltage(voltage, parameters), expected, rtol=1e-13)


@pytest.mark.parametrize("temperature_K", [250, 300, 400])
def test_noiseless_parameter_recovery(temperature_K):
    parameters = DiodeParameters(3e-10, 1.35, 12, temperature_K)
    current = np.geomspace(1e-11, 0.03, 100)
    result = fit_diode(
        current, voltage_at_current(current, parameters), 0.001, temperature_K=temperature_K
    )
    assert result.parameters.saturation_current_A == pytest.approx(3e-10, rel=1e-7)
    assert result.parameters.ideality_factor == pytest.approx(1.35, rel=1e-7)
    assert result.parameters.series_resistance_ohm == pytest.approx(12, rel=1e-7)
    assert result.reduced_chi_square < 1e-15
    # Supplied absolute measurement uncertainty is not erased by a perfect fit.
    assert np.all(result.standard_errors > 0)


def test_synthetic_noise_recovery_and_covariance_scaling():
    parameters = DiodeParameters()
    current = np.geomspace(1e-9, 0.02, 100)
    sigma = 0.0015
    voltage = voltage_at_current(current, parameters) + np.random.default_rng(2026).normal(
        0, sigma, 100
    )
    result = fit_diode(current, voltage, sigma)
    true_values = np.array([1e-11, 1.6, 5])
    fitted_values = np.array(
        [
            result.parameters.saturation_current_A,
            result.parameters.ideality_factor,
            result.parameters.series_resistance_ohm,
        ]
    )
    assert np.all(np.abs(fitted_values - true_values) < 3 * result.standard_errors)
    assert 0.5 < result.reduced_chi_square < 1.5
    np.testing.assert_allclose(result.correlation.diagonal(), 1)
    assert np.linalg.eigvalsh(result.covariance).min() > 0
    doubled = fit_diode(current, voltage, 2 * sigma)
    np.testing.assert_allclose(doubled.standard_errors, 2 * result.standard_errors, rtol=1e-5)
    assert doubled.reduced_chi_square == pytest.approx(result.reduced_chi_square / 4, rel=1e-10)


def test_limited_current_range_does_not_claim_precise_resistance():
    current = np.geomspace(1e-9, 1e-6, 50)
    result = fit_diode(current, voltage_at_current(current, DiodeParameters()), 0.0015)
    assert result.standard_errors[2] > 5
    assert any("weakly constrained" in message for message in result.warnings)


def test_rank_deficiency_has_no_covariance():
    current = np.full(20, 1e-5)
    result = fit_diode(current, voltage_at_current(current, DiodeParameters()), 0.001)
    assert result.covariance is None and result.standard_errors is None
    assert any("Rank-deficient" in message for message in result.warnings)


def test_bound_limited_fit_has_no_gaussian_covariance():
    current = np.geomspace(1e-9, 0.02, 80)
    # A deliberately unphysical negative-resistance trend forces the allowed Rs=0 bound.
    voltage = (
        voltage_at_current(current, DiodeParameters(series_resistance_ohm=0)) - current * 5
    )
    result = fit_diode(current, voltage, 0.001)
    assert result.covariance is None
    assert any("bound" in message for message in result.warnings)


@pytest.mark.parametrize(
    "arguments",
    [
        {"saturation_current_A": 0},
        {"ideality_factor": np.nan},
        {"series_resistance_ohm": -1},
        {"temperature_K": 500},
    ],
)
def test_invalid_parameters(arguments):
    with pytest.raises(ValueError):
        DiodeParameters(**arguments)


@pytest.mark.parametrize("voltage", [-0.1, np.nan, 6])
def test_invalid_inverse_voltage(voltage):
    with pytest.raises(ValueError):
        current_at_voltage(voltage, DiodeParameters())


@pytest.mark.parametrize(
    "current, voltage, sigma",
    [
        ([1, 2], [1, 2], 0.1),
        ([0, 1, 2, 3, 4], [1] * 5, 0.1),
        ([1] * 5, [1] * 5, 0),
        ([1] * 5, [1] * 5, [0.1, 0.1]),
        ([1] * 5, [np.nan] * 5, 0.1),
        ([np.inf] * 5, [1] * 5, 0.1),
    ],
)
def test_invalid_fit_data(current, voltage, sigma):
    with pytest.raises(ValueError):
        fit_diode(current, voltage, sigma)
