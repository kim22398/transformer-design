# Dissolved Gas Analysis (DGA) Interpretation Guide

## Overview

Dissolved Gas Analysis is the single most powerful predictive maintenance tool available for oil-immersed power transformers. Incipient faults within the transformer — whether electrical or thermal — decompose the insulating oil (and sometimes the cellulose paper) into characteristic combustible gases that dissolve in the oil. By extracting and quantifying these gases from a periodic oil sample, engineers can detect developing faults months or years before they cause a failure.

This guide explains the diagnostic methods implemented in `transformer/oil_analysis.py`, covering the key gases and their significance, the Duval Triangle method (IEC 60599:2022), the Rogers Ratios method (IEEE C57.104-2019), TDCG alarm levels, a sample interpretation walkthrough, and recommended action levels.

---

## 1. Key Gases and What They Indicate

The following combustible gases are monitored in a standard DGA:

| Gas | Formula | Primary source | Fault indication |
|---|---|---|---|
| Hydrogen | H₂ | Oil and paper decomposition | Partial discharge, corona; any overheating |
| Methane | CH₄ | Oil thermal decomposition | Low-to-moderate thermal fault (< 300 °C) |
| Ethane | C₂H₆ | Oil thermal decomposition | Thermal fault (< 300 °C, mild) |
| Ethylene | C₂H₄ | Oil thermal decomposition | Thermal fault (> 300 °C, significant) |
| Acetylene | C₂H₂ | High-energy arc or very hot spot | Electrical discharge; arc; very high temperature (> 700 °C) |
| Carbon monoxide | CO | Cellulose (paper) decomposition | Cellulose involved in thermal fault |
| Carbon dioxide | CO₂ | Cellulose oxidation or normal ageing | Elevated CO₂/CO ratio is often benign; very high absolute levels suggest paper degradation |

**The three hydrocarbon gases** — methane (CH₄), ethylene (C₂H₄), and acetylene (C₂H₂) — form the basis of the Duval Triangle.

**Acetylene is a critical marker.** Its carbon–carbon triple bond is highly stable and requires very high temperatures (or an electrical arc) to form. Even a small concentration (> 5 ppm) warrants investigation; concentrations above 10–15 ppm with a rising trend are a serious alarm signal.

**CO and CO₂** together indicate whether solid insulation (paper, pressboard) is involved. The CO/CO₂ ratio is significant: a ratio greater than 0.1 suggests active cellulose decomposition, which is of greater concern than oil decomposition alone because the paper cannot be replaced without a full rewind.

**Non-combustible gases** (nitrogen, oxygen) are not used for fault diagnosis but indicate the condition of the gas-blanketing or breathing system.

---

## 2. Total Dissolved Combustible Gas (TDCG)

TDCG is the sum of the concentrations of all combustible gases:

```
TDCG = H₂ + CH₄ + C₂H₂ + C₂H₄ + C₂H₆ + CO    [ppm]
```

Note: CO₂ is excluded because it can be present in significant quantities from normal paper ageing without indicating an active fault.

### IEEE C57.104-2019 TDCG Condition Levels

| Condition | TDCG range | Action required |
|---|---|---|
| **1 — Normal** | < 720 ppm | Continue routine annual sampling |
| **2 — Increased concern** | 720 – 1 919 ppm | Increase sampling to quarterly; investigate individual gas levels |
| **3 — High concern** | 1 920 – 4 629 ppm | Sample monthly; plan outage for internal inspection when possible |
| **4 — Critical** | ≥ 4 630 ppm | Consider immediate de-energisation; consult specialist |

These limits apply to **total TDCG**. Individual gas levels (especially for acetylene and hydrogen) may trigger action at lower TDCG values — always assess individual gases alongside the total.

**Rate of change** is often more important than the absolute level. A TDCG of 600 ppm that doubled in three months is more alarming than a stable 900 ppm level that has not changed in two years.

---

## 3. Duval Triangle Method (IEC 60599:2022)

### Principle

The Duval Triangle plots the **relative percentages** of methane (CH₄), ethylene (C₂H₄), and acetylene (C₂H₂) on a triangular coordinate system. The triangle is divided into zones, each corresponding to a distinct fault type. The advantage of a relative-percentage approach is that it is insensitive to the oil volume and gas extraction method.

The three coordinates are calculated as:

```
%CH₄  = CH₄  / (CH₄ + C₂H₄ + C₂H₂) × 100
%C₂H₄ = C₂H₄ / (CH₄ + C₂H₄ + C₂H₂) × 100
%C₂H₂ = C₂H₂ / (CH₄ + C₂H₄ + C₂H₂) × 100
```

Each point plots uniquely within the triangle, and the zone it falls into gives the fault classification.

### Triangle Zone Diagram

```
        C₂H₂
         100%
          /\
         /  \
        / D2 \
       /______\
      / D1  DT \
     /____  ____\
    / PD  \/  T3 \
   /      /\      \
  /  T1  /  \  T2  \
 /______/    \______\
CH₄  100%            C₂H₄  100%
```

### Zone Definitions (IEC 60599:2022 Figure 1)

| Zone | Fault type | Description |
|---|---|---|
| **PD** | Partial discharge | Very high %CH₄ (> 98%), very low C₂H₂ and C₂H₄; corona in gas cavities or voids |
| **T1** | Thermal fault < 300 °C | Dominant CH₄; low acetylene; overheated oil at low temperature |
| **T2** | Thermal fault 300–700 °C | Significant C₂H₄ (20–50%); moderate CH₄; hot connections or core |
| **T3** | Thermal fault > 700 °C | Very high C₂H₄ (> 50%); severe overheating; carbonised conductor insulation possible |
| **D1** | Low-energy discharge | Moderate C₂H₂ (4–29%); low C₂H₄; corona, sparking, floating potential |
| **D2** | High-energy discharge | C₂H₂ > 29%; arcing; immediate risk of failure if trend is rising |
| **DT** | Thermal + electrical mixture | C₂H₂ 4–29% and C₂H₄ > 20%; combined fault; common in OLTC-related contamination |

### Simplified Decision Rules (implemented in `_duval_triangle()`)

The production implementation uses rectangular boundary approximations from IEC 60599 Figure 1:

```
If %C₂H₂ > 29%                         → D2  (high-energy arcing)
Else if %C₂H₂ > 4% AND %C₂H₄ > 20%    → DT  (thermal + discharge)
Else if %C₂H₂ > 4%                     → D1  (low-energy discharge)
Else if %C₂H₄ > 50%                    → T3  (thermal > 700 °C)
Else if %C₂H₄ > 20%                    → T2  (thermal 300–700 °C)
Else if %CH₄  > 98%                    → PD  (partial discharge)
Else                                    → T1  (thermal < 300 °C)
```

For borderline points near zone boundaries, the full triangular coordinate implementation (or a graphical tool) should be used to confirm the classification.

---

## 4. Rogers Ratios Method (IEEE C57.104-2019)

### Principle

The Rogers Ratios method uses three ratios of gas concentrations to classify faults. Each ratio reflects a different aspect of the decomposition chemistry:

| Ratio | Formula | Physical significance |
|---|---|---|
| R₁ | C₂H₂ / C₂H₄ | Arc energy level; high R₁ means high-temperature discharge |
| R₂ | CH₄ / H₂ | Thermal vs. discharge origin; low R₂ means discharge dominant |
| R₃ | C₂H₄ / C₂H₆ | Thermal fault temperature; high R₃ means high-temperature thermal |

### Fault Codes (IEEE C57.104-2019 Table 4)

| Code | R₁ (C₂H₂/C₂H₄) | R₂ (CH₄/H₂) | R₃ (C₂H₄/C₂H₆) | Fault type |
|---|---|---|---|---|
| **0** | < 0.1 | 0.1–1.0 | < 1.0 | Normal ageing; no fault |
| **1** | < 0.1 | < 0.1 | < 1.0 | Partial discharge (corona in gas space) |
| **2** | < 1.0 | 0.1–1.0 | > 3.0 | High-temperature thermal fault (> 700 °C) |
| **3** | 0.1–3.0 | 0.1–1.0 | 1.0–3.0 | Low-energy electrical discharge |
| **4** | ≥ 0.3 | 0.1–1.0 | > 1.0 | High-energy electrical discharge (arcing) |
| **U** | — | — | — | Undetermined; use Duval Triangle as primary |

**Limitation:** If any denominator gas is zero or below the detection limit, the ratio cannot be calculated and the Rogers method is unreliable. In such cases, rely solely on the Duval Triangle. The `_rogers_ratios()` implementation returns code "U" for undetermined combinations not matching any of the above patterns.

---

## 5. Using Both Methods Together

The Duval Triangle and Rogers Ratios methods are complementary rather than redundant:

- **Both agree:** High confidence in the diagnosis. Proceed with the recommended action.
- **Duval gives DT, Rogers gives 3 or 4:** Consistent with a mixed fault involving both thermal and electrical discharge components (e.g., arcing at a resistive joint, or OLTC contamination).
- **Rogers returns "U":** Fall back to Duval Triangle as the primary diagnosis.
- **Both disagree significantly:** The sample may have been contaminated, or multiple simultaneous fault types are present. Retest with a fresh sample and engage a specialist.

In general, **Duval Triangle is more reliable** for mixed fault zones and for cases where individual gas concentrations are low. Rogers Ratios can be more sensitive for distinguishing high-temperature thermal from high-energy discharge.

---

## 6. Worked Interpretation Example

The following gas concentrations are taken from the 10 MVA unit in `transformer_audit.py`:

| Gas | Concentration |
|---|---|
| H₂ | 180 ppm |
| CH₄ | 290 ppm |
| C₂H₂ | 4 ppm |
| C₂H₄ | 310 ppm |
| C₂H₆ | 75 ppm |
| CO | 620 ppm |
| CO₂ | 4 100 ppm |
| **TDCG** | **1 479 ppm** |

**Step 1 — TDCG Assessment:**

TDCG = 180 + 290 + 4 + 310 + 75 + 620 = 1 479 ppm → **Condition 2** (Increased concern). Increase sampling frequency to quarterly.

**Step 2 — Cellulose involvement:**

CO/CO₂ = 620/4 100 = 0.151 > 0.1 → **Cellulose degradation indicated.** The paper insulation is participating in the thermal process. This elevates the severity of the diagnosis.

**Step 3 — Duval Triangle:**

```
Total (for Duval) = CH₄ + C₂H₄ + C₂H₂ = 290 + 310 + 4 = 604 ppm
%CH₄  = 290/604 × 100 = 48.0%
%C₂H₄ = 310/604 × 100 = 51.3%
%C₂H₂ =   4/604 × 100 =  0.7%
```

%C₂H₂ = 0.7% (not > 4%), %C₂H₄ = 51.3% (> 50%) → **Zone T3: Thermal fault > 700 °C.**

**Step 4 — Rogers Ratios:**

```
R₁ = C₂H₂ / C₂H₄ =   4 / 310 = 0.013  (< 0.1)
R₂ = CH₄  / H₂   = 290 / 180 = 1.611  (> 1.0)
R₃ = C₂H₄ / C₂H₆ = 310 /  75 = 4.133  (> 3.0)
```

R₁ < 0.1, R₂ > 1.0, R₃ > 3.0 → Pattern matches code **2: High-temperature thermal fault (> 700 °C).** (R₂ slightly outside the 0.1–1.0 band; Duval T3 takes precedence.)

**Step 5 — Conclusion and Actions:**

Both methods consistently indicate a **severe thermal fault at a temperature exceeding 700 °C** with cellulose insulation involved. Recommended actions:

1. **Increase oil sampling to monthly** and track the rate of rise in C₂H₄ and total hydrocarbons.
2. **Review recent operating history:** Has the transformer been overloaded? Are oil temperature gauges reading correctly?
3. **Investigate cooling system:** Check fan operation, oil circulation, radiator condition, and oil level.
4. **Plan an internal inspection** at the next available outage. Examine the core clamps, bus-bar joints, and the top of the windings for discolouration, carbon deposits, or distorted conductor insulation.
5. **De-energise immediately** if the TDCG rate of rise exceeds 30 ppm/day or acetylene appears or increases.

---

## 7. Action Level Summary

| Finding | Immediate action | Monitoring |
|---|---|---|
| Duval T1 or Rogers Code 0 | None | Annual sampling |
| TDCG Condition 2, T1 or T2 | Review load history | Quarterly sampling |
| TDCG Condition 2, T3 or D1 | Inspect cooling; review overloads | Monthly sampling |
| Any acetylene detected (first occurrence) | Confirm with retest; check OLTC | Monthly or weekly |
| C₂H₂ > 10 ppm or rising trend | Plan outage for inspection | Weekly until stable |
| Duval D2 or TDCG Condition 3 | Prepare for outage | Weekly until outage |
| TDCG Condition 4 or D2 with rising gas | Consider de-energisation | Continuous monitoring |

---

## References

- IEC 60599:2022, *Mineral oil-filled electrical equipment in service — Guidance on the interpretation of dissolved and free gases analysis*
- IEEE C57.104-2019, *IEEE Guide for the Interpretation of Gases Generated in Mineral Oil-Immersed Transformers*
- Duval, M. (1989). "Dissolved gas analysis: It can save your transformer." *IEEE Electrical Insulation Magazine* 5(6): 22–27.
- Rogers, R.R. (1978). "IEEE and IEC codes to interpret incipient faults in transformers, using gas in oil analysis." *IEEE Trans. Electrical Insulation* EI-13(5): 349–354.
