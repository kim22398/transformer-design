"""
transformer.oil_analysis
------------------------
Dissolved-gas analysis (DGA), dielectric breakdown voltage, and
moisture-in-oil calculations.

DGA methods implemented
~~~~~~~~~~~~~~~~~~~~~~~
1. **Duval Triangle** (IEC 60599:2022, method T1)
   Uses the relative percentages of CH₄, C₂H₄, C₂H₂ to classify fault
   type into six zones.

2. **Rogers Ratios** (IEEE C57.104-2019 / IEC 60599 Annex A)
   Uses three gas ratios (C₂H₂/C₂H₄, CH₄/H₂, C₂H₄/C₂H₆) to classify
   faults into four fault codes.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Optional


# ---------------------------------------------------------------------------
# Duval Triangle fault zones (IEC 60599:2022 Table 1)
# ---------------------------------------------------------------------------
# Zone boundaries defined as minimum C₂H₂ percentage thresholds.
# Full implementation uses the triangular coordinate system; this version
# uses the simplified rectangular decision rules published in the standard.

_DUVAL_ZONES = {
    "PD":  "Partial discharge",
    "T1":  "Thermal fault < 300 °C",
    "T2":  "Thermal fault 300–700 °C",
    "T3":  "Thermal fault > 700 °C",
    "D1":  "Low-energy electrical discharge (corona / sparking)",
    "D2":  "High-energy electrical discharge (arcing)",
    "DT":  "Thermal + electrical fault mixture",
}


@dataclass
class DGAResult:
    """Container for DGA diagnosis results."""
    method: str
    fault_code: str
    fault_description: str
    recommendation: str
    gases_ppm: dict


class OilAnalysis:
    """
    Dissolved-gas analysis and oil quality assessment utilities.

    All gas concentrations are in parts per million by volume (ppm v/v)
    as extracted from oil per IEC 60567.
    """

    # ------------------------------------------------------------------
    # Dissolved-gas analysis
    # ------------------------------------------------------------------

    def parse_dissolved_gas(
        self,
        h2: float,
        ch4: float,
        c2h2: float,
        c2h4: float,
        c2h6: float,
        co: float,
        co2: float,
    ) -> dict:
        """
        Diagnose transformer condition using Duval Triangle and Rogers
        Ratio methods.

        Parameters
        ----------
        h2   : float  Hydrogen [ppm]
        ch4  : float  Methane [ppm]
        c2h2 : float  Acetylene [ppm]
        c2h4 : float  Ethylene [ppm]
        c2h6 : float  Ethane [ppm]
        co   : float  Carbon monoxide [ppm]
        co2  : float  Carbon dioxide [ppm]

        Returns
        -------
        dict with keys ``"duval"``, ``"rogers"``, ``"gases_ppm"``,
        ``"cellulose_involved"``, ``"tdcg_ppm"``.
        """
        gases = {
            "H2": h2, "CH4": ch4, "C2H2": c2h2,
            "C2H4": c2h4, "C2H6": c2h6, "CO": co, "CO2": co2,
        }
        tdcg = h2 + ch4 + c2h2 + c2h4 + c2h6 + co  # Total Dissolved Combustible Gas
        cellulose = (co / co2 > 0.1) if co2 > 0 else False  # CO/CO₂ > 0.1 → paper involved

        duval = self._duval_triangle(ch4, c2h2, c2h4)
        rogers = self._rogers_ratios(h2, ch4, c2h2, c2h4, c2h6)

        return {
            "duval": duval,
            "rogers": rogers,
            "gases_ppm": gases,
            "tdcg_ppm": tdcg,
            "cellulose_involved": cellulose,
            "tdcg_condition": self._tdcg_condition(tdcg),
        }

    # ------------------------------------------------------------------
    # Duval Triangle (IEC 60599:2022)
    # ------------------------------------------------------------------

    @staticmethod
    def _duval_triangle(ch4: float, c2h2: float, c2h4: float) -> DGAResult:
        """
        Classify fault using the Duval Triangle method.

        The triangle coordinates (%CH₄, %C₂H₂, %C₂H₄) are normalised
        so that %CH₄ + %C₂H₂ + %C₂H₄ = 100.  Zone boundaries per
        IEC 60599:2022 Figure 1.
        """
        total = ch4 + c2h2 + c2h4
        if total == 0:
            return DGAResult(
                method="Duval Triangle",
                fault_code="ND",
                fault_description="No fault gases detectable",
                recommendation="No action required.",
                gases_ppm={"CH4": ch4, "C2H2": c2h2, "C2H4": c2h4},
            )

        pct_ch4  = ch4  / total * 100
        pct_c2h2 = c2h2 / total * 100
        pct_c2h4 = c2h4 / total * 100

        # Decision rules (simplified rectangular boundaries from IEC 60599 Fig.1)
        if pct_c2h2 > 29:
            code = "D2"
        elif pct_c2h2 > 4 and pct_c2h4 > 20:
            code = "DT"
        elif pct_c2h2 > 4:
            code = "D1"
        elif pct_c2h4 > 50:
            code = "T3"
        elif pct_c2h4 > 20:
            code = "T2"
        elif pct_ch4 > 98:
            code = "PD"
        else:
            code = "T1"

        recommendations = {
            "PD":  "Investigate partial discharge; check grounding and insulation.",
            "T1":  "Low-temperature thermal fault; inspect cooling system.",
            "T2":  "Moderate thermal fault; investigate hot-spots, check connections.",
            "T3":  "Severe thermal fault; de-energise and inspect immediately.",
            "D1":  "Low-energy discharge; check insulation integrity, reduce stress.",
            "D2":  "High-energy arcing detected; de-energise immediately.",
            "DT":  "Combined thermal-electrical fault; plan outage for inspection.",
            "ND":  "Normal.",
        }

        return DGAResult(
            method="Duval Triangle",
            fault_code=code,
            fault_description=_DUVAL_ZONES.get(code, "Unknown"),
            recommendation=recommendations.get(code, "Consult specialist."),
            gases_ppm={"CH4": ch4, "C2H2": c2h2, "C2H4": c2h4},
        )

    # ------------------------------------------------------------------
    # Rogers Ratios (IEEE C57.104-2019 / IEC 60599 Annex A)
    # ------------------------------------------------------------------

    @staticmethod
    def _rogers_ratios(
        h2: float,
        ch4: float,
        c2h2: float,
        c2h4: float,
        c2h6: float,
    ) -> DGAResult:
        """
        Classify fault using the three-ratio Rogers method.

        Ratios:
        - R1 = C₂H₂ / C₂H₄
        - R2 = CH₄  / H₂
        - R3 = C₂H₄ / C₂H₆

        Fault codes (IEEE C57.104-2019 Table 4):

        ======  ====  ====  ====  ==========================
        Code    R1    R2    R3    Fault type
        ======  ====  ====  ====  ==========================
        0       <0.1  0.1–1 <1    Normal ageing
        1       <0.1  <0.1  <1    Partial discharge
        2        <1   0.1–1 >3    High-temperature thermal
        3       0.1–3 0.1–1 1–3   Low-energy discharge
        4       >0.3  0.1–1 >3    High-energy discharge/arcing
        ======  ====  ====  ====  ==========================
        """
        r1 = c2h2 / c2h4 if c2h4 > 0 else 0.0
        r2 = ch4  / h2   if h2   > 0 else 0.0
        r3 = c2h4 / c2h6 if c2h6 > 0 else 0.0

        # Simplified Rogers decision table
        if r1 < 0.1 and 0.1 <= r2 < 1.0 and r3 < 1.0:
            code, desc = "0", "Normal ageing / no fault"
        elif r1 < 0.1 and r2 < 0.1 and r3 < 1.0:
            code, desc = "1", "Partial discharge (corona)"
        elif r1 < 1.0 and 0.1 <= r2 < 1.0 and r3 > 3.0:
            code, desc = "2", "High-temperature thermal fault (> 700 °C)"
        elif 0.1 <= r1 < 3.0 and 0.1 <= r2 < 1.0 and 1.0 <= r3 <= 3.0:
            code, desc = "3", "Low-energy electrical discharge"
        elif r1 >= 0.3 and r3 > 1.0:
            code, desc = "4", "High-energy electrical discharge (arcing)"
        else:
            code, desc = "U", "Undetermined – multiple ratio combinations"

        recommendations = {
            "0": "Normal. Continue routine monitoring.",
            "1": "Partial discharge. Check for voids, moisture, sharp edges.",
            "2": "Severe thermal fault. Inspect core, clamps, and connections.",
            "3": "Discharge. Investigate insulation integrity.",
            "4": "Arcing. De-energise; inspect windings and tap changer.",
            "U": "Inconclusive. Combine with Duval Triangle result and trend analysis.",
        }

        return DGAResult(
            method="Rogers Ratios",
            fault_code=code,
            fault_description=desc,
            recommendation=recommendations.get(code, "Consult specialist."),
            gases_ppm={"H2": h2, "CH4": ch4, "C2H2": c2h2, "C2H4": c2h4, "C2H6": c2h6},
        )

    # ------------------------------------------------------------------
    # TDCG condition (IEEE C57.104-2019 Table 2)
    # ------------------------------------------------------------------

    @staticmethod
    def _tdcg_condition(tdcg_ppm: float) -> str:
        """Return TDCG condition per IEEE C57.104-2019 Table 2."""
        if tdcg_ppm < 720:
            return "Condition 1 – Normal (continue routine sampling)"
        elif tdcg_ppm < 1920:
            return "Condition 2 – Investigate; increase sampling frequency"
        elif tdcg_ppm < 4630:
            return "Condition 3 – High concern; plan outage"
        else:
            return "Condition 4 – Critical; consider immediate de-energisation"

    # ------------------------------------------------------------------
    # Dielectric breakdown voltage
    # ------------------------------------------------------------------

    @staticmethod
    def dielectric_breakdown_kv_rating(measured_kv: float) -> dict:
        """
        Classify measured dielectric breakdown voltage (BDV) against
        IEC 60156:2018 acceptance criteria.

        Parameters
        ----------
        measured_kv : float
            BDV test result [kV] (mean of 6 punctures per IEC 60156).

        Returns
        -------
        dict with ``"status"``, ``"limit_kv"``, ``"margin_kv"``.
        """
        # IEC 60156 minimum BDV for new oil in service (> 72.5 kV systems)
        limit_kv = 60.0
        status = "PASS" if measured_kv >= limit_kv else "FAIL"
        return {
            "measured_kv": measured_kv,
            "limit_kv": limit_kv,
            "margin_kv": measured_kv - limit_kv,
            "status": status,
            "standard": "IEC 60156:2018",
        }

    # ------------------------------------------------------------------
    # Moisture content
    # ------------------------------------------------------------------

    @staticmethod
    def moisture_ppm_to_saturation_pct(ppm: float, temp_C: float) -> float:
        """
        Convert absolute moisture content [ppm] to relative saturation
        percentage at the given oil temperature.

        The saturation concentration of water in mineral transformer oil
        follows an Arrhenius-type relationship (IEC 60422:2013):

        .. math::
            W_s(T) = A \\cdot e^{B T}

        Using empirical constants A = 2.173, B = 0.0411 (Oommen 1984)
        which give Wₛ in ppm at temperature T in °C.

        Parameters
        ----------
        ppm : float
            Measured water content [ppm by weight].
        temp_C : float
            Oil temperature [°C].

        Returns
        -------
        float
            Relative water saturation [%].  Values > 100 % indicate
            free water is present.
        """
        import math
        A = 2.173
        B = 0.0411
        w_sat = A * math.exp(B * temp_C)
        return (ppm / w_sat) * 100.0
