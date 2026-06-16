"""
transformer.protection
----------------------
Protection relay setting calculations for power transformers.

References
~~~~~~~~~~
- IEEE C57.13-2016   – Instrument transformers for protection
- IEC 60255-151:2009 – Overcurrent protection
- IEC 60255-87:2017  – Differential protection
- Buchholz relay threshold: IEC 60076-1 / manufacturer data
"""

from __future__ import annotations

import math
from typing import Tuple


class TransformerProtection:
    """
    Relay setting utilities for a two-winding power transformer.

    All currents are in amperes unless otherwise noted.
    """

    # ------------------------------------------------------------------
    # 87T – Percentage differential protection
    # ------------------------------------------------------------------

    @staticmethod
    def differential_current(
        i_primary: float,
        i_secondary: float,
        ctr_primary: float,
        ctr_secondary: float,
    ) -> Tuple[float, float, float]:
        """
        Calculate the operating (differential) and restraint currents
        for a percentage-differential relay (87T).

        The relay compares currents referred to a common base using the
        CT ratios.  Compensation for transformer vector-group phase shift
        (e.g. 30° for Dyn11) must be applied externally via CT winding
        connection or numerical relay software.

        .. math::
            I_{op}  = |I_{r1} - I_{r2}|
            I_{res} = \\tfrac{1}{2}(I_{r1} + I_{r2})
            slope   = I_{op} / I_{res} \\times 100\\%

        Parameters
        ----------
        i_primary : float
            Measured primary-side line current [A].
        i_secondary : float
            Measured secondary-side line current [A].
        ctr_primary : float
            Primary-side CT ratio (e.g. 200 for a 200/1 CT).
        ctr_secondary : float
            Secondary-side CT ratio.

        Returns
        -------
        (i_op, i_res, slope_pct) : tuple[float, float, float]
            Operating current [A secondary], restraint current
            [A secondary], and the operate/restrain slope [%].
        """
        i_r1 = i_primary / ctr_primary
        i_r2 = i_secondary / ctr_secondary
        i_op = abs(i_r1 - i_r2)
        i_res = 0.5 * (abs(i_r1) + abs(i_r2))
        slope_pct = (i_op / i_res * 100.0) if i_res > 0 else 0.0
        return i_op, i_res, slope_pct

    # ------------------------------------------------------------------
    # 51 – Overcurrent protection (pickup setting)
    # ------------------------------------------------------------------

    @staticmethod
    def overcurrent_pickup(
        load_kva: float,
        voltage_kv: float,
        multiplier: float = 1.25,
    ) -> float:
        """
        Recommended overcurrent relay pickup current [A].

        The pickup is set at *multiplier* × full-load current so that
        the relay does not operate under maximum continuous load while
        still providing back-up protection.

        .. math::
            I_{FL} = \\frac{S}{\\sqrt{3}\\,V}
            I_{pickup} = multiplier \\times I_{FL}

        Parameters
        ----------
        load_kva : float
            Maximum continuous load apparent power [kVA].
        voltage_kv : float
            Nominal voltage at the relay location [kV].
        multiplier : float
            Safety margin factor (default 1.25, i.e. 125% of FLC).

        Returns
        -------
        float
            Overcurrent relay pickup setting [A primary].
        """
        i_fl = (load_kva * 1_000) / (math.sqrt(3) * voltage_kv * 1_000)
        return multiplier * i_fl

    # ------------------------------------------------------------------
    # 64REF – Restricted earth-fault protection
    # ------------------------------------------------------------------

    @staticmethod
    def restricted_earth_fault(
        i_neutral: float,
        i_phases: Tuple[float, float, float],
    ) -> Tuple[float, bool]:
        """
        Restricted earth-fault (REF) relay operating quantity.

        A high-impedance REF relay (64REF) operates when the spill
        current between the neutral CT and the sum of the three-phase
        CTs exceeds a threshold.

        .. math::
            I_{spill} = I_N - (I_A + I_B + I_C)

        An internal earth fault causes :math:`I_{spill} \\neq 0`.
        The relay operates when |I_spill| > 0.2 A (typical setting,
        ~5% of rated secondary current on a 1 A relay).

        Parameters
        ----------
        i_neutral : float
            Current measured by neutral CT [A secondary].
        i_phases : tuple[float, float, float]
            Phase A, B, C currents measured by phase CTs [A secondary].

        Returns
        -------
        (i_spill, operate) : tuple[float, bool]
            Spill current magnitude and relay operate flag.
        """
        i_spill = i_neutral - sum(i_phases)
        operate = abs(i_spill) > 0.2  # typical 5% pickup
        return abs(i_spill), operate

    # ------------------------------------------------------------------
    # Buchholz relay
    # ------------------------------------------------------------------

    @staticmethod
    def buchholz_gas_volume_threshold_ml() -> dict:
        """
        Buchholz relay alarm and trip gas-accumulation thresholds [mL].

        Thresholds are indicative values per IEC 60076-1 Annex A and
        typical utility practice.  Actual settings depend on the relay
        model and transformer rating.

        Returns
        -------
        dict
            Keys ``"alarm_ml"`` and ``"trip_ml"`` with threshold values.
        """
        return {
            "alarm_ml": 100,   # slow gas accumulation → alarm
            "trip_ml": 250,    # rapid gas surge → instantaneous trip
            "surge_velocity_cm_s": 100,  # trip on oil surge velocity
            "notes": (
                "Alarm at ~100 mL accumulated gas (slow fault); "
                "Trip on Buchholz float or surge-velocity element. "
                "Verify with relay manufacturer datasheet."
            ),
        }
