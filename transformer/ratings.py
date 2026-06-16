"""
transformer.ratings
-------------------
Nameplate ratings and basic calculations for a two-winding power transformer.

Formulae follow IEC 60076-1:2011.
"""

from __future__ import annotations

import math


class TransformerRatings:
    """
    Encapsulates the nameplate data of a two-winding oil-immersed power
    transformer and provides derived electrical quantities.

    Parameters
    ----------
    kva : float
        Rated apparent power [kVA].
    primary_kv : float
        Rated primary (HV) line voltage [kV].
    secondary_kv : float
        Rated secondary (LV) line voltage [kV].
    impedance_pct : float
        Short-circuit impedance as a percentage of rated voltage [%].
    no_load_loss_kw : float
        No-load (core/iron) losses at rated voltage and frequency [kW].
    load_loss_kw : float
        Load (copper/winding) losses at rated current and 75 °C [kW].
    vector_group : str
        IEC vector-group designation, e.g. ``"Dyn11"``, ``"YNyn0"``.
    """

    def __init__(
        self,
        kva: float,
        primary_kv: float,
        secondary_kv: float,
        impedance_pct: float,
        no_load_loss_kw: float,
        load_loss_kw: float,
        vector_group: str = "Dyn11",
    ) -> None:
        if kva <= 0:
            raise ValueError("kva must be positive")
        if primary_kv <= 0 or secondary_kv <= 0:
            raise ValueError("voltage ratings must be positive")
        if not (0 < impedance_pct < 100):
            raise ValueError("impedance_pct must be between 0 and 100")

        self.kva = kva
        self.primary_kv = primary_kv
        self.secondary_kv = secondary_kv
        self.impedance_pct = impedance_pct
        self.no_load_loss_kw = no_load_loss_kw
        self.load_loss_kw = load_loss_kw
        self.vector_group = vector_group

    # ------------------------------------------------------------------
    # Basic electrical quantities
    # ------------------------------------------------------------------

    def turns_ratio(self) -> float:
        """
        Voltage turns ratio  a = V1 / V2.

        For a three-phase transformer the ratio is defined on a
        phase-to-phase (line) basis per IEC 60076-1 §5.2.
        """
        return self.primary_kv / self.secondary_kv

    def primary_current_A(self) -> float:
        """
        Rated primary (HV) line current [A].

        .. math::
            I_1 = \\frac{S}{\\sqrt{3}\\,V_1}

        where *S* is in VA and *V₁* in V.
        """
        return (self.kva * 1_000) / (math.sqrt(3) * self.primary_kv * 1_000)

    def secondary_current_A(self) -> float:
        """
        Rated secondary (LV) line current [A].

        .. math::
            I_2 = \\frac{S}{\\sqrt{3}\\,V_2}
        """
        return (self.kva * 1_000) / (math.sqrt(3) * self.secondary_kv * 1_000)

    # ------------------------------------------------------------------
    # Losses and efficiency
    # ------------------------------------------------------------------

    def full_load_efficiency_pct(self, pf: float = 0.9) -> float:
        """
        Full-load efficiency at the specified power factor [%].

        .. math::
            \\eta = \\frac{P_{out}}{P_{out} + P_{NL} + P_{LL}} \\times 100

        where:
        - :math:`P_{out} = S \\cdot pf` [kW]
        - :math:`P_{NL}` = no-load losses [kW]
        - :math:`P_{LL}` = full-load load losses [kW]

        Parameters
        ----------
        pf : float
            Load power factor (0 < pf ≤ 1). Default 0.9.
        """
        if not (0 < pf <= 1):
            raise ValueError("Power factor must be in range (0, 1]")
        p_out_kw = self.kva * pf
        total_losses_kw = self.no_load_loss_kw + self.load_loss_kw
        return (p_out_kw / (p_out_kw + total_losses_kw)) * 100.0

    def short_circuit_impedance_ohm_primary(self) -> float:
        """
        Short-circuit impedance referred to the primary side [Ω].

        .. math::
            Z_{sc} = \\frac{z_{\\%}}{100} \\cdot \\frac{V_1^2}{S}
        """
        return (self.impedance_pct / 100.0) * (
            (self.primary_kv * 1_000) ** 2 / (self.kva * 1_000)
        )

    def __repr__(self) -> str:
        return (
            f"TransformerRatings({self.kva} kVA, "
            f"{self.primary_kv}/{self.secondary_kv} kV, "
            f"{self.vector_group}, "
            f"Z={self.impedance_pct}%)"
        )
