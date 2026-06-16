"""
transformer.thermal
-------------------
IEC 60076-7:2018 thermal model for oil-immersed power transformers.

Implements the *exponential* (non-linear) thermal model described in
Annex A of IEC 60076-7:2018, which is the standard approach for ONAN/
ONAF/OFAF-cooled units.

Key symbols
~~~~~~~~~~~
- Δθ_or  : Rated top-oil temperature rise above ambient [K]
- Δθ_hr  : Rated hot-spot-to-top-oil temperature gradient [K]
- x      : Oil thermal exponent (typically 0.8 for ONAN)
- y      : Winding thermal exponent (typically 1.6 for ONAN)
- R      : Ratio of load losses to no-load losses at rated load
- K      : Load factor (per-unit load, 1.0 = rated)
"""

from __future__ import annotations

import math


# ---------------------------------------------------------------------------
# IEC 60076-7 default thermal exponents (Table 2 / Clause 7.2)
# ---------------------------------------------------------------------------
_EXPONENTS = {
    "ONAN": {"x": 0.8, "y": 1.6},
    "ONAF": {"x": 0.9, "y": 1.6},
    "OFAF": {"x": 1.0, "y": 1.6},
    "ODAF": {"x": 1.0, "y": 2.0},
}

# IEC 60076-7:2018 Eq. (1): reference hot-spot temperature for normal
# ageing of oil-impregnated paper insulation [°C].
_THETA_HR_REF = 98.0  # °C  (hot-spot reference for normal ageing)

# Activation energy / Boltzmann constant ratio used in Arrhenius model
# for transformer-grade Kraft paper (IEC 60076-7 Annex B, Eq. B.1).
_B = 15_000.0  # K


class ThermalModel:
    """
    IEC 60076-7:2018 exponential thermal model.

    Parameters
    ----------
    rated_top_oil_rise_K : float
        Rated top-oil temperature rise above ambient at full load [K].
        Typical value: 55 K (ONAN, ONAF) or 45 K (OFAF).
    rated_winding_gradient_K : float
        Rated hot-spot-to-top-oil temperature gradient at full load [K].
        Typical value: 23 K (ONAN) per IEC 60076-7 Table 2.
    ratio_load_to_no_load_loss : float
        *R* = load losses / no-load losses at rated load.
        Default 6.0 (typical for 10–63 MVA ONAN transformers).
    cooling_mode : str
        One of ``"ONAN"``, ``"ONAF"``, ``"OFAF"``, ``"ODAF"``.
    hot_spot_factor : float
        Hot-spot factor *H* (IEC 60076-7 §7.2).  Default 1.3.
    """

    def __init__(
        self,
        rated_top_oil_rise_K: float = 55.0,
        rated_winding_gradient_K: float = 23.0,
        ratio_load_to_no_load_loss: float = 6.0,
        cooling_mode: str = "ONAN",
        hot_spot_factor: float = 1.3,
    ) -> None:
        if cooling_mode not in _EXPONENTS:
            raise ValueError(
                f"cooling_mode must be one of {list(_EXPONENTS.keys())}"
            )
        self.delta_theta_or = rated_top_oil_rise_K
        self.delta_theta_hr = rated_winding_gradient_K
        self.R = ratio_load_to_no_load_loss
        self.cooling_mode = cooling_mode
        self.x = _EXPONENTS[cooling_mode]["x"]
        self.y = _EXPONENTS[cooling_mode]["y"]
        self.H = hot_spot_factor

    # ------------------------------------------------------------------
    # IEC 60076-7 §7.2 – steady-state temperatures
    # ------------------------------------------------------------------

    def top_oil_rise(self, load_factor: float, ambient_C: float = 20.0) -> float:
        """
        Steady-state top-oil temperature rise above ambient [K].

        IEC 60076-7:2018 Eq. (2):

        .. math::
            \\Delta\\theta_o = \\Delta\\theta_{or}
            \\left(\\frac{1 + R K^2}{1 + R}\\right)^x

        Parameters
        ----------
        load_factor : float
            Per-unit load (*K*).  1.0 = rated load.
        ambient_C : float
            Ambient temperature [°C].  Included here for API symmetry;
            the rise itself is independent of ambient.
        """
        K = load_factor
        rise = self.delta_theta_or * ((1 + self.R * K**2) / (1 + self.R)) ** self.x
        return rise

    def hot_spot_temp(self, load_factor: float, ambient_C: float = 20.0) -> float:
        """
        Steady-state hot-spot temperature [°C].

        IEC 60076-7:2018 Eq. (3):

        .. math::
            \\theta_h = \\theta_a + \\Delta\\theta_o
                       + H \\cdot \\Delta\\theta_{hr} \\cdot K^y

        Parameters
        ----------
        load_factor : float
            Per-unit load (*K*).
        ambient_C : float
            Ambient temperature [°C].
        """
        K = load_factor
        delta_theta_o = self.top_oil_rise(K, ambient_C)
        winding_gradient = self.H * self.delta_theta_hr * (K**self.y)
        return ambient_C + delta_theta_o + winding_gradient

    # ------------------------------------------------------------------
    # IEC 60076-7 Annex B – insulation ageing
    # ------------------------------------------------------------------

    def aging_acceleration_factor(self, hot_spot_C: float) -> float:
        """
        Ageing acceleration factor *V* relative to reference hot-spot
        98 °C (IEC 60076-7 Annex B, Eq. B.1).

        .. math::
            V = \\exp\\!\\left[
                \\frac{B}{\\theta_{hr,ref}+273}
                - \\frac{B}{\\theta_h+273}
            \\right]

        A value of 1.0 means normal ageing; >1 means accelerated ageing.
        """
        theta_h_K = hot_spot_C + 273.15
        theta_ref_K = _THETA_HR_REF + 273.15
        return math.exp(_B / theta_ref_K - _B / theta_h_K)

    def loss_of_life_pct_per_hour(self, hot_spot_C: float) -> float:
        """
        Percentage of normal insulation life consumed per hour of
        operation at *hot_spot_C*.

        Normal insulation life for well-dried, oxygen-free Kraft paper
        is 200 000 hours (IEC 60076-7 Table B.1, thermally upgraded
        paper: 300 000 h). This implementation uses the standard
        200 000 h base.

        .. math::
            L = \\frac{V}{L_{normal}} \\times 100\\%

        where :math:`L_{normal} = 200\\,000` h.
        """
        normal_life_h = 200_000.0
        V = self.aging_acceleration_factor(hot_spot_C)
        return (V / normal_life_h) * 100.0

    def __repr__(self) -> str:
        return (
            f"ThermalModel(mode={self.cooling_mode}, "
            f"Δθ_or={self.delta_theta_or} K, "
            f"Δθ_hr={self.delta_theta_hr} K, R={self.R})"
        )
