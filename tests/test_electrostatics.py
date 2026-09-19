"""Physical invariants, independent reference and convergence of the junction solver."""

import numpy as np
import pytest
from scipy.constants import e, epsilon_0, k

from pn_junction import (
    ConvergenceError,
    Junction,
    depletion_approximation,
    depletion_profile,
    silicon,
    solve_equilibrium,
)
from pn_junction.validation import collocation_potential


def test_silicon_matches_project_one_parameter_reference():
    material = silicon()
    assert material.bandgap_eV == pytest.approx(1.1240192307692307)
    assert material.conduction_dos_cm3 == pytest.approx(2.8319781581794095e19, rel=1e-8)
    assert material.valence_dos_cm3 == pytest.approx(1.02133077775324e19, rel=1e-8)
    assert material.intrinsic_cm3 == pytest.approx(6.155766827822502e9, rel=1e-8)
    assert material.permittivity_F_m == 11.7 * epsilon_0
    assert material.thermal_voltage_V == pytest.approx(k * 300 / e)


@pytest.mark.parametrize("temperature_K", [250, 300, 400])
def test_material_trends_and_density_units(temperature_K):
    material = silicon(temperature_K)
    assert material.conduction_dos_cm3 / silicon().conduction_dos_cm3 == pytest.approx(
        (temperature_K / 300) ** 1.5
    )
    assert 1e19 < material.conduction_dos_cm3 < 1e20
    assert silicon(250).intrinsic_cm3 < material.intrinsic_cm3 * (1 + 1e-12)
    assert material.bandgap_eV >= silicon(400).bandgap_eV


@pytest.mark.parametrize(
    "junction", [Junction(), Junction(1e15, 1e17), Junction(1e17, 1e14, 250)]
)
def test_depletion_charge_balance_boundary_and_integrated_field(junction):
    depletion = depletion_approximation(junction)
    assert junction.acceptor_cm3 * depletion.p_width_m == pytest.approx(
        junction.donor_cm3 * depletion.n_width_m, rel=1e-12
    )
    points = np.array(
        [
            -2 * depletion.p_width_m,
            -depletion.p_width_m,
            0,
            depletion.n_width_m,
            2 * depletion.n_width_m,
        ]
    )
    potential, field = depletion_profile(junction, points)
    assert potential[0] == potential[1] == 0
    assert potential[-1] == potential[-2] == junction.built_in_voltage_V
    assert field[0] == field[-1] == 0
    assert field[2] == pytest.approx(-depletion.peak_field_V_m)
    # Area under the piecewise-linear signed field gives the total potential drop.
    assert -np.sum((field[1:] + field[:-1]) * np.diff(points) / 2) == pytest.approx(
        junction.built_in_voltage_V
    )
    textbook_voltage = junction.material.thermal_voltage_V * np.log(
        junction.acceptor_cm3 * junction.donor_cm3 / junction.material.intrinsic_cm3**2
    )
    assert junction.built_in_voltage_V == pytest.approx(textbook_voltage, rel=1e-8)


@pytest.mark.parametrize(
    "junction", [Junction(), Junction(1e15, 1e17), Junction(1e14, 1e14, 400)]
)
def test_equilibrium_physical_invariants(junction):
    result = solve_equilibrium(junction)
    assert result.scaled_residual < 1e-9
    assert result.potential_V[0] == 0
    assert result.potential_V[-1] == pytest.approx(junction.built_in_voltage_V)
    assert np.all(np.diff(result.potential_V) > 0)
    assert np.all(result.face_field_V_m < 0)
    assert np.all(result.electron_cm3 > 0) and np.all(result.hole_cm3 > 0)
    np.testing.assert_allclose(
        result.electron_cm3 * result.hole_cm3, junction.material.intrinsic_cm3**2, rtol=1e-14
    )
    np.testing.assert_allclose(
        result.conduction_band_eV - result.valence_band_eV,
        junction.material.bandgap_eV,
        rtol=1e-14,
    )
    contact_charge_fraction = np.array([result.charge_C_m3[0], result.charge_C_m3[-1]]) / (
        e * 1e6 * np.array([junction.acceptor_cm3, junction.donor_cm3])
    )
    assert np.max(np.abs(contact_charge_fraction)) < 1e-13
    sheet_charge_scale = (
        e * 1e6 * junction.acceptor_cm3 * depletion_approximation(junction).p_width_m
    )
    assert abs(result.gauss_error_C_m2) / sheet_charge_scale < 1e-8
    assert result.conduction_band_eV[0] > result.conduction_band_eV[-1]


def test_symmetric_junction_reflection():
    result = solve_equilibrium()
    np.testing.assert_allclose(result.electron_cm3, result.hole_cm3[::-1], rtol=1e-11)
    np.testing.assert_allclose(
        result.reduced_potential, -result.reduced_potential[::-1], atol=1e-11
    )


@pytest.mark.parametrize(
    "junction", [Junction(), Junction(1e15, 1e17), Junction(1e14, 1e14, 400)]
)
def test_independent_collocation_and_grid_convergence(junction):
    errors = []
    for cells in (100, 200, 400):
        result = solve_equilibrium(junction, cells_per_side=cells)
        reference = collocation_potential(result)
        errors.append(np.max(np.abs(result.potential_V - reference)))
    assert errors[-1] < 2e-4
    assert 3.2 < errors[0] / errors[1] < 4.8
    assert 3.2 < errors[1] / errors[2] < 4.8


def test_contact_padding_and_depletion_limit():
    first = solve_equilibrium(cells_per_side=800, padding_debye=12)
    farther = solve_equilibrium(cells_per_side=1000, padding_debye=18)
    interpolated = np.interp(first.position_m, farther.position_m, farther.potential_V)
    assert np.max(np.abs(first.potential_V - interpolated)) < 2e-5
    analytical = depletion_approximation(first.junction)
    assert abs(first.field_V_m.min()) / analytical.peak_field_V_m == pytest.approx(1, rel=0.05)
    assert abs(first.face_field_V_m[0]) / analytical.peak_field_V_m < 1e-5


@pytest.mark.parametrize(
    "arguments",
    [
        {"acceptor_cm3": -1},
        {"donor_cm3": 1e20},
        {"donor_cm3": np.nan},
        {"temperature_K": 100},
        {"temperature_K": np.inf},
    ],
)
def test_invalid_physical_inputs(arguments):
    with pytest.raises(ValueError):
        Junction(**arguments)


@pytest.mark.parametrize(
    "arguments",
    [
        {"cells_per_side": 19},
        {"cells_per_side": 20.5},
        {"cells_per_side": True},
        {"padding_debye": np.nan},
        {"padding_debye": 1},
        {"max_iterations": 0},
        {"residual_tolerance": -1},
    ],
)
def test_invalid_numerical_inputs(arguments):
    with pytest.raises(ValueError):
        solve_equilibrium(**arguments)


def test_nonconvergence_is_not_silently_accepted():
    with pytest.raises(ConvergenceError):
        solve_equilibrium(max_iterations=1)
