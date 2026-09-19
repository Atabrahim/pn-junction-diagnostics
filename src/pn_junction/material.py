"""Restricted, traceable silicon Boltzmann parameter model; see docs/MODEL.md."""

from dataclasses import dataclass

import numpy as np
from scipy.constants import e, epsilon_0, h, k, m_e


@dataclass(frozen=True)
class Silicon:
    """Derived parameters at one temperature, with units in field names."""

    temperature_K: float
    thermal_voltage_V: float
    bandgap_eV: float
    conduction_dos_cm3: float
    valence_dos_cm3: float
    intrinsic_cm3: float
    permittivity_F_m: float


def silicon(temperature_K: float = 300.0) -> Silicon:
    """Return fixed-mass silicon parameters for 250 <= T <= 400 K.

    Palankovski Tables 3.8, 3.16 and 3.2 supply the gap, masses and
    permittivity range. Intrinsic density is model-derived, not measured.
    """
    if not np.isfinite(temperature_K) or not 250 <= temperature_K <= 400:
        raise ValueError("temperature_K must be finite and between 250 and 400 K")
    thermal_voltage_V = k * temperature_K / e
    bandgap_eV = 1.1695 - 4.73e-4 * temperature_K**2 / (temperature_K + 636.0)
    dos_prefactor_cm3 = 2 * (2 * np.pi * m_e * k * temperature_K / h**2) ** 1.5 / 1e6
    conduction_dos_cm3 = dos_prefactor_cm3 * 6 * np.sqrt(0.19**2 * 0.98)
    valence_dos_cm3 = dos_prefactor_cm3 * (0.49**1.5 + 0.16**1.5)
    intrinsic_cm3 = np.sqrt(conduction_dos_cm3 * valence_dos_cm3) * np.exp(
        -bandgap_eV / (2 * thermal_voltage_V)
    )
    return Silicon(
        temperature_K,
        thermal_voltage_V,
        bandgap_eV,
        conduction_dos_cm3,
        valence_dos_cm3,
        intrinsic_cm3,
        11.7 * epsilon_0,
    )
