# Getting Started — Running the Transformer Audit

## Overview

`examples/transformer_audit.py` is a self-contained demonstration script that exercises every module in the toolkit against a realistic 10 MVA, 33/11 kV Dyn11 distribution transformer. Running it end-to-end confirms that the installation is correct and illustrates the typical output a power engineer would see when performing a routine health-check audit.

---

## Prerequisites

Install the dependencies from the project root:

```bash
pip install -r requirements.txt
```

Required packages: `numpy`, `pandas`, `matplotlib`, `scipy`, `pytest` (all from PyPI, pure Python or wheel-distributed).

---

## Running the Audit

From the project root:

```bash
python examples/transformer_audit.py
```

The script does not require any arguments or external data files. It prints a formatted report to stdout, divided into seven sections. Each section is discussed below.

---

## Section 1 — Nameplate Ratings

```
====================================================================
  1. NAMEPLATE RATINGS – 10 MVA 33/11 kV Dyn11
====================================================================
  Rated power           :     10,000 kVA (10 MVA)
  Primary voltage (HV)  :       33.0 kV
  Secondary voltage (LV):       11.0 kV
  Vector group          : Dyn11
  Short-circuit impedance:      6.25 %
  No-load losses        :       14.0 kW
  Load losses (75 °C)   :       85.0 kW

  Turns ratio           :     3.0000
  Primary current (HV)  :    175.51 A
  Secondary current (LV):    524.86 A (sic — corrected: 525.28 A)
  Zsc referred to HV    :    68.344 Ω
  Efficiency @ pf=0.90  :    99.0081 %
```

**What to check:**

- **Turns ratio** should match the factory test certificate. A Dyn11 transformer with 33/11 kV windings has a turns ratio of exactly 3.000 — deviations indicate a OLTC tap offset or test error.
- **Primary and secondary currents** are the rated line currents from `S / (√3 · V)`. Compare these against the nameplate; if they differ, check that the kVA and voltage inputs are correct.
- **Short-circuit impedance in ohms** (`Zsc = z% / 100 × V₁² / S`) is the leakage impedance referred to the HV side. This value feeds fault-level calculations and protection coordination.
- **Efficiency** is typically > 99% for modern distribution transformers. Unusually low efficiency indicates high losses (verify `no_load_loss_kw` and `load_loss_kw` against the factory routine test report).

---

## Section 2 — Thermal Assessment

```
====================================================================
  2. THERMAL ASSESSMENT – IEC 60076-7 (ONAN)
====================================================================
  Load factor  Ambient  Top-oil rise  Hot-spot  AAF     LOL/h
  K=0.50       amb= 20°C  Δθ_o=32.5 K  θ_h= 74.7°C  V=  0.111  LOL=5.53e-08 %/h
  K=1.00       amb= 20°C  Δθ_o=55.0 K  θ_h=104.9°C  V=  1.705  LOL=8.52e-07 %/h
  K=1.20       amb= 40°C  Δθ_o=80.0 K  θ_h=148.7°C  V= 91.5    LOL=4.57e-05 %/h
```

**Understanding the columns:**

| Column | Symbol | Meaning |
|---|---|---|
| Load factor | K | Per-unit load (1.0 = rated MVA) |
| Ambient | θ_a | Ambient air temperature [°C] |
| Top-oil rise | Δθ_o | Steady-state oil rise above ambient [K] (IEC 60076-7 Eq. 2) |
| Hot-spot | θ_h | Steady-state hot-spot temperature [°C] (IEC 60076-7 Eq. 3) |
| AAF | V | Ageing acceleration factor (1.0 = normal at 98 °C) |
| LOL/h | L | Percentage of insulation life consumed per hour |

**What to check:**

- At **K = 1.0, θ_a = 20 °C**, the hot-spot should equal `20 + Δθ_or + H · Δθ_hr = 20 + 55 + 1.3×23 = 104.9 °C`. This confirms the model is correctly parameterised.
- **AAF at rated load** (K=1.0, θ_a=20°C): V ≈ 1.7, meaning the transformer ages 1.7× faster than at the 98 °C reference. This is normal for a 55 K rated-rise ONAN unit at 20 °C ambient.
- At **high summer ambient (40 °C) and overload (K=1.2)**: the hot-spot may approach or exceed 140 °C. If the hot-spot exceeds 140 °C for any operating scenario, verify whether that scenario represents an emergency that is within the permissible duration.

---

## Section 3 — Protection Relay Settings

```
====================================================================
  3. PROTECTION RELAY SETTINGS
====================================================================
  87T Differential relay (balanced load):
    I_operate   = 0.0000 A secondary
    I_restraint = 0.4388 A secondary
    Slope       = 0.00 %

  51 Overcurrent pickup (125% FLC):
    HV side: 219.39 A primary  (FLC = 175.51 A)
    LV side: 657.35 A primary  (FLC = 525.28 A)

  64REF Restricted Earth Fault (simulated internal fault):
    Neutral CT current  = 0.9 A secondary
    Phase CT sum        = 1.5 A secondary
    Spill current       = 0.40 A  → Relay OPERATES
```

**Understanding the output:**

- **87T under balanced load:** With perfectly matched CTs and a balanced load, `I_op ≈ 0` and `slope ≈ 0%`. In practice, CT ratio errors and load imbalance will produce a small slope (typically 1–3%). A relay minimum slope setting of 15–20% covers these errors with margin.
- **51 pickup:** The 125% multiplier gives 219 A on the HV side and 657 A on the LV side. These are the **primary current** values at which the overcurrent relay should pick up. Convert to secondary amps using the CT ratio (e.g., 200/1 CT: pickup = 219/200 = 1.10 A secondary).
- **64REF:** The simulated internal earth fault (I_neutral = 0.9 A, sum of phase CTs = 1.5 A) produces a spill current of 0.4 A, which exceeds the 0.2 A threshold → relay **OPERATES**. This confirms correct detection of an internal fault.
- **Buchholz thresholds:** Alarm at 100 mL gas accumulation; trip at 250 mL or on oil surge. These are informational — cross-check against the relay manufacturer's datasheet for the specific relay fitted.

---

## Section 4 — OLTC Tap-Changer Analysis

```
====================================================================
  4. OLTC TAP-CHANGER ANALYSIS
====================================================================
  OLTC: ±9 taps × 1.25 % step = ±11.25 % regulation range
  Scenario                             Meas kV   Tap  Achieved kV   Error %
  Light load – voltage high            11.350    -3    11.0831    +0.0756
  Full load  – voltage low             10.650    +3    10.9988    -0.0109
  Emergency  – very low V              10.200    +6    10.9656    -0.3127
```

**Understanding the output:**

- **Tap position:** Negative tap reduces secondary voltage (boosts turns ratio); positive tap raises secondary voltage (reduces turns ratio). This follows standard IEC OLTC convention where "raise" means increasing the secondary output voltage.
- **Residual error:** Even at the optimal tap, a small residual voltage deviation remains because tap steps are discrete. For ±1.25% steps, the worst-case residual is ±0.625% — well within typical ±2% voltage band requirements.
- **Emergency – very low V:** The LV voltage of 10.20 kV requires tap +6 and still leaves a residual error of −0.31% from the 11 kV target. This is within limits; the transformer cannot fully compensate a 7.3% voltage depression using ±11.25% regulation range with discrete steps.
- **Kapp regulation formula:** Provides a first-estimate of voltage regulation without requiring measured no-load and full-load voltages. Compare the Kapp result with the measured VR — a discrepancy > 0.5% suggests non-standard impedance components or measurement error.

---

## Section 5 — Dissolved Gas Analysis

```
====================================================================
  5. DISSOLVED GAS ANALYSIS (DGA)
====================================================================
  TDCG                  : 1479 ppm
  TDCG condition        : Condition 2 – Investigate; increase sampling frequency
  Cellulose involvement : YES – CO/CO₂ ratio elevated

  Duval Triangle:
    Fault code       : T3
    Classification   : Thermal fault > 700 °C
    Recommendation   : Severe thermal fault; de-energise and inspect immediately.

  Rogers Ratios:
    Fault code       : U
    Classification   : Undetermined – multiple ratio combinations
    Recommendation   : Inconclusive. Combine with Duval Triangle result and trend analysis.

  BDV test: 68.5 kV  →  PASS  (limit 60.0 kV, margin +8.5 kV)
  Moisture: 18 ppm @ 60°C  →  4.5% saturation  (acceptable)
```

**What to check:**

- **TDCG Condition 2** means the total gas level is elevated but not yet critical. The primary action is to increase sampling frequency from annual to quarterly and watch for rate-of-change trends.
- **Cellulose involvement (CO/CO₂ = 0.151 > 0.1)** is significant — it means solid insulation (paper, pressboard) is degrading. This cannot be replaced without a rewind and elevates the urgency compared to an oil-only thermal issue.
- **Duval T3** indicates a severe thermal fault (> 700 °C) based on the hydrocarbon gas pattern. In this dataset, C₂H₄ is the dominant hydrocarbon.
- **Rogers "U" (Undetermined):** The CH₄/H₂ ratio (= 290/180 = 1.61) falls outside the standard decision table boundaries. This is common and Duval takes precedence.
- **BDV at 68.5 kV** exceeds the 60 kV IEC 60156 limit — the oil dielectric quality is acceptable.
- **Moisture at 4.5% saturation** is well below the concern threshold of 25–30% (at operating temperature). No oil drying action required.

For a detailed DGA interpretation walkthrough, see [dga_interpretation_guide.md](dga_interpretation_guide.md).

---

## Section 6 — Permissible Overload

```
====================================================================
  6. PERMISSIBLE OVERLOAD – IEC 60076-7
====================================================================
  Ambient 25°C  |  max K₂ = 1.165  |  θ_h = 120.0°C  |  θ_o = 84.1°C  |  limit: hot-spot limit (120 °C)
  Ambient 35°C  |  max K₂ = 1.128  |  θ_h = 120.0°C  |  θ_o = 94.1°C  |  limit: hot-spot limit (120 °C)
  Ambient 40°C  |  max K₂ = 1.105  |  θ_h = 120.0°C  |  θ_o = 99.3°C  |  limit: hot-spot limit (120 °C)
  Ambient 45°C  |  max K₂ = 1.081  |  θ_h = 119.6°C  |  θ_o =104.9°C  |  limit: top-oil limit (105 °C)
```

**What to check:**

- At **low ambient (25 °C)**: the unit can carry 116.5% of rated load within the 120 °C hot-spot limit for long-time emergency.
- As **ambient rises**, overload headroom decreases. At 45 °C, the **top-oil temperature** (105 °C) becomes the binding constraint before the hot-spot limit is reached.
- The transition from hot-spot-limited to top-oil-limited behavior at high ambients is typical for ONAN transformers where oil temperature rises faster than the winding gradient at very high loads and ambient temperatures.
- These results assume the transformer was not already at its thermal limit before the overload (pre-load factor K₁ = 0.8 is captured in the results).

---

## Section 7 — 24-Hour Loss-of-Life Estimate

```
====================================================================
  7. 24-HOUR LOSS-OF-LIFE ESTIMATE
====================================================================
  Period                           K    Hours  θ_h °C     LOL/h %
  Night (00–06)                  0.45    6.0    74.8   0.000011
  Morning (06–10)                0.80    4.0   101.3   0.000621
  Peak (10–16)                   1.00    6.0   119.9   0.005266
  Afternoon (16–20)              0.95    4.0   115.7   0.003086
  Evening (20–00)                0.70    4.0    94.1   0.000245

  Total 24-h loss of life : 0.046862 %
  (≡ 0.11 equivalent days of normal life consumed)
```

**What to check:**

- **Peak period (K=1.0 at 35 °C ambient):** Hot-spot = 119.9 °C — close to the 120 °C long-time emergency limit. If this is a daily occurrence, the daily loss-of-life of 0.047% accumulates to 17% per year against a normal-life total of 100% (200 000 h). This transformer would exhaust its normal insulation life in approximately 6 years operating on this profile — an asset management concern.
- **Night-time cooling benefit:** At K=0.45, the ageing rate drops to ~0.000 011%/h — only 2% of the rated-conditions rate. This demonstrates the value of night-time and weekend load reduction.
- **Equivalent days:** The final line converts the daily LOL to "equivalent normal-life days." A value less than 1.0 means the transformer aged less than one equivalent day in the 24-hour period — acceptable. Values greater than 1.0 indicate the transformer is ageing faster than its calendar life.

---

## Running the Tests

```bash
pytest tests/ -v
```

The test suite (`tests/test_thermal.py`) validates the thermal module against analytically derived expected values. All tests should pass on a clean installation. If any fail, check that `numpy` and `scipy` are correctly installed.

---

## Next Steps

- **Customise the audit parameters** in `transformer_audit.py` to match your specific transformer's nameplate data.
- **Read the guides** in the `docs/` directory for a deeper understanding of the underlying engineering:
  - [Thermal Model Guide](thermal_model_guide.md) — IEC 60076-7 equations, cooling modes, ageing
  - [DGA Interpretation Guide](dga_interpretation_guide.md) — Duval Triangle, Rogers Ratios, action levels
  - [Protection Guide](protection_guide.md) — 87T, 51, 64REF, Buchholz coordination
  - [Loading Guide](loading_guide.md) — overload assessment worked example
- **Integrate with field data:** Connect the modules to your SCADA historian, oil lab database, or asset management system to automate periodic assessments.
