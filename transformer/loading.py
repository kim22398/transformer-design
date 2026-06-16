"""
transformer.loading
-------------------
Permissible overload calculations per IEC 60076-7:2018 §7.3.

The loading guide defines limits based on:
- Maximum hot-spot temperature (98 °C for normal ageing; 140 °C absolute max)
- Maximum top-oil temperature (105 °C)
- Maximum load factor for short-time emergency loading (1.5 pu typical)

This module implements the iterative search method to find the maximum
continuous overload factor *K₂* such that the hot-spot temperature does
not exceed the specified limit, given a prior load *K₁* and ambient.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from transformer.thermal import ThermalModel


class LoadingCalculator:
    """
    Permissible loading and overload factor calculations.

    Parameters
    ----------
    thermal_model : ThermalModel
        A configured :class:`~transformer.thermal.ThermalModel` instance
        whose parameters match the transformer under study.
    max_hot_spot_C : float
        Maximum permissible hot-spot temperature [°C].
        IEC 60076-7 Table 1:
        - Normal continuous: 98 °C
        - Long-time emergency: 120 °C
        - Short-time emergency: 140 °C
    max_top_oil_C : float
        Maximum permissible top-oil temperature [°C].  Default 105 °C
        (IEC 60076-7 Table 1, ONAN short-time emergency).
    """

    def __init__(
        self,
        thermal_model: "ThermalModel",
        max_hot_spot_C: float = 98.0,
        max_top_oil_C: float = 105.0,
    ) -> None:
        self.tm = thermal_model
        self.max_hot_spot_C = max_hot_spot_C
        self.max_top_oil_C = max_top_oil_C

    def permissible_overload(
        self,
        ambient_C: float,
        pre_load_factor: float,
        duration_h: float,
        search_resolution: float = 0.001,
    ) -> dict:
        """
        Maximum permissible overload factor for a given scenario.

        Uses a binary-search over the load factor *K₂* to find the
        highest value that keeps both the steady-state hot-spot
        temperature and top-oil temperature within their permitted limits.

        The pre-load factor *K₁* is used to determine the thermal
        pre-condition: the transformer is assumed to be in steady state
        at *K₁* before the overload *K₂* is applied.  For simplicity
        this implementation returns the *steady-state* limit (i.e. it
        does not model the thermal time constant transient); this is
        conservative for short-duration overloads.

        For transient overload studies use the full differential equation
        approach per IEC 60076-7 Annex A with numerical integration.

        Parameters
        ----------
        ambient_C : float
            Ambient temperature [°C].
        pre_load_factor : float
            Load factor immediately prior to the overload event (K₁).
        duration_h : float
            Duration of the overload [hours].  Currently used to
            annotate the result; transient thermal modelling is noted
            as a future enhancement.
        search_resolution : float
            Binary-search convergence tolerance on load factor.

        Returns
        -------
        dict with keys:
            - ``max_load_factor``: maximum permissible *K₂*
            - ``hot_spot_C``: hot-spot temperature at *K₂*
            - ``top_oil_C``: top-oil temperature at *K₂*
            - ``limiting_constraint``: which limit is active
            - ``ambient_C``, ``pre_load_factor``, ``duration_h``
        """
        lo, hi = 0.0, 3.0  # search range for K₂

        def _feasible(k2: float) -> bool:
            hs = self.tm.hot_spot_temp(k2, ambient_C)
            to = ambient_C + self.tm.top_oil_rise(k2, ambient_C)
            return hs <= self.max_hot_spot_C and to <= self.max_top_oil_C

        if not _feasible(lo):
            return {
                "max_load_factor": 0.0,
                "hot_spot_C": self.tm.hot_spot_temp(0.0, ambient_C),
                "top_oil_C": ambient_C + self.tm.top_oil_rise(0.0, ambient_C),
                "limiting_constraint": "ambient too high",
                "ambient_C": ambient_C,
                "pre_load_factor": pre_load_factor,
                "duration_h": duration_h,
            }

        while hi - lo > search_resolution:
            mid = (lo + hi) / 2
            if _feasible(mid):
                lo = mid
            else:
                hi = mid

        k_max = lo
        hs_at_kmax = self.tm.hot_spot_temp(k_max, ambient_C)
        to_at_kmax = ambient_C + self.tm.top_oil_rise(k_max, ambient_C)

        if hs_at_kmax >= self.max_hot_spot_C - 0.5:
            constraint = f"hot-spot limit ({self.max_hot_spot_C} °C)"
        else:
            constraint = f"top-oil limit ({self.max_top_oil_C} °C)"

        return {
            "max_load_factor": round(k_max, 3),
            "hot_spot_C": round(hs_at_kmax, 2),
            "top_oil_C": round(to_at_kmax, 2),
            "limiting_constraint": constraint,
            "ambient_C": ambient_C,
            "pre_load_factor": pre_load_factor,
            "duration_h": duration_h,
        }

    def cumulative_loss_of_life(
        self,
        load_profile: list[tuple[float, float]],
        ambient_C: float,
    ) -> float:
        """
        Cumulative percentage loss of insulation life for a load cycle.

        Parameters
        ----------
        load_profile : list[tuple[float, float]]
            List of (load_factor, duration_h) pairs representing the
            load cycle.
        ambient_C : float
            Constant ambient temperature [°C].

        Returns
        -------
        float
            Total insulation life consumed [%].
        """
        total_lol = 0.0
        for k, hours in load_profile:
            hs = self.tm.hot_spot_temp(k, ambient_C)
            lol_per_h = self.tm.loss_of_life_pct_per_hour(hs)
            total_lol += lol_per_h * hours
        return total_lol
