"""
transformer.tap_changer
-----------------------
On-load tap-changer (OLTC) analysis utilities.

The optimal tap position is determined by finding the tap that brings
the secondary voltage closest to the target voltage.  Tap positions are
numbered from the centre tap (0 = nominal ratio); positive taps raise
the secondary voltage, negative taps lower it.
"""

from __future__ import annotations

import math
from typing import Tuple


class OLTCAnalyzer:
    """
    Utilities for on-load tap-changer selection and voltage regulation.

    Tap positions are centred about 0 (nominal).  A positive tap
    position *increases* the secondary voltage (by reducing the
    effective turns ratio), which is the convention for most IEC OLTC
    designs.
    """

    # ------------------------------------------------------------------
    # Optimal tap selection
    # ------------------------------------------------------------------

    @staticmethod
    def optimal_tap(
        measured_voltage_kv: float,
        target_voltage_kv: float,
        tap_step_pct: float,
        n_taps: int,
    ) -> Tuple[int, float, float]:
        """
        Find the OLTC tap position that brings secondary voltage closest
        to *target_voltage_kv*.

        Each tap step changes the secondary voltage by *tap_step_pct* %
        relative to the nominal voltage.  The total regulation range is
        ±(n_taps × tap_step_pct) %.

        Algorithm
        ~~~~~~~~~
        Required fractional voltage change:

        .. math::
            \\delta = \\frac{V_{target} - V_{measured}}{V_{target}}

        Tap position (rounded to nearest integer, clamped to ±n_taps):

        .. math::
            n = \\text{round}\\!\\left(\\frac{\\delta}{tap\\_step\\_pct/100}\\right)

        Parameters
        ----------
        measured_voltage_kv : float
            Current measured secondary voltage [kV].
        target_voltage_kv : float
            Desired secondary voltage [kV].
        tap_step_pct : float
            Voltage change per tap step [%] (e.g. 1.25).
        n_taps : int
            Maximum number of tap steps in either direction from nominal.

        Returns
        -------
        (tap_position, achieved_voltage_kv, residual_error_pct) : tuple
            - ``tap_position``: integer tap position (negative = lower,
              positive = raise).
            - ``achieved_voltage_kv``: secondary voltage at the chosen tap.
            - ``residual_error_pct``: remaining voltage deviation from
              target [%].
        """
        if tap_step_pct <= 0:
            raise ValueError("tap_step_pct must be positive")
        if n_taps < 1:
            raise ValueError("n_taps must be at least 1")

        delta = (target_voltage_kv - measured_voltage_kv) / target_voltage_kv
        tap_float = delta / (tap_step_pct / 100.0)
        tap_pos = int(round(tap_float))
        tap_pos = max(-n_taps, min(n_taps, tap_pos))

        achieved_kv = measured_voltage_kv * (1 + tap_pos * tap_step_pct / 100.0)
        residual_pct = (achieved_kv - target_voltage_kv) / target_voltage_kv * 100.0
        return tap_pos, achieved_kv, residual_pct

    # ------------------------------------------------------------------
    # Voltage regulation
    # ------------------------------------------------------------------

    @staticmethod
    def voltage_regulation_pct(
        no_load_v: float,
        full_load_v: float,
    ) -> float:
        """
        Percentage voltage regulation of the transformer.

        .. math::
            VR = \\frac{V_{NL} - V_{FL}}{V_{FL}} \\times 100\\%

        where both voltages are at the secondary terminals with the same
        primary voltage applied.

        Parameters
        ----------
        no_load_v : float
            Secondary terminal voltage at no load [V or kV – units
            must be consistent].
        full_load_v : float
            Secondary terminal voltage at full rated load [same units].

        Returns
        -------
        float
            Voltage regulation [%].
        """
        if full_load_v <= 0:
            raise ValueError("full_load_v must be positive")
        return (no_load_v - full_load_v) / full_load_v * 100.0

    @staticmethod
    def approximate_regulation_pct(
        impedance_pct: float,
        resistance_pct: float,
        power_factor: float = 0.9,
    ) -> float:
        """
        Approximate voltage regulation using the Kapp regulation formula.

        .. math::
            VR \\approx \\varepsilon_R \\cos\\phi
                       + \\varepsilon_X \\sin\\phi
                       + \\frac{(\\varepsilon_X \\cos\\phi
                               - \\varepsilon_R \\sin\\phi)^2}{200}

        where :math:`\\varepsilon_R` = resistance percentage,
        :math:`\\varepsilon_X` = reactance percentage.

        Parameters
        ----------
        impedance_pct : float
            Short-circuit impedance [%].
        resistance_pct : float
            Short-circuit resistance (= load-loss %) [%].
        power_factor : float
            Load power factor (lagging). Default 0.9.
        """
        eps_r = resistance_pct
        eps_x = math.sqrt(impedance_pct**2 - eps_r**2)
        cos_phi = power_factor
        sin_phi = math.sqrt(1 - cos_phi**2)
        vr = (
            eps_r * cos_phi
            + eps_x * sin_phi
            + (eps_x * cos_phi - eps_r * sin_phi) ** 2 / 200.0
        )
        return vr
