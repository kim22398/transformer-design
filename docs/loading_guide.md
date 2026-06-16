# Permissible Loading Guide — IEC 60076-7

## Overview

IEC 60076-7:2018 defines the framework for determining how much load a transformer can carry without unacceptable loss of insulation life. Unlike simple nameplate ratings that define a single continuous rating, the loading guide recognises that transformers can tolerate short-duration overloads provided the hot-spot temperature and top-oil temperature remain within defined limits and the cumulative loss of insulation life is acceptable.

This guide explains the three loading categories, the temperature limits governing each, the ageing rate during overload, and provides a worked example of overload assessment using the `LoadingCalculator` class.

---

## 1. Loading Categories

IEC 60076-7 §7.3 defines three categories of permissible loading:

### 1.1 Normal Cyclic Loading

Normal cyclic loading refers to the **routine daily load cycle** experienced by a transformer in normal network operation. The transformer may exceed rated current during peak demand periods provided:

- The daily load cycle does not produce a **long-term average hot-spot** significantly above 98 °C (which is the reference temperature for normal ageing).
- The **peak hot-spot temperature** during the cycle does not exceed 98 °C under the 20 °C ambient assumed for the nameplate rating.

In practice, many utilities permit a peak load factor of 1.0–1.1 pu for short daily periods (2–4 hours) as part of normal operation, accepting a modest acceleration of ageing during those hours in exchange for lower hot-spot temperatures during off-peak hours. The annual loss-of-life budget approach compares the total loss of life from the actual annual load curve against a reference value (typically 1 normal life year = 100% of `200 000/8 760 × 100%` per hour = 0.000 5%/h).

### 1.2 Long-Time Emergency Loading

Long-time emergency loading applies when a transformer must carry **above-nameplate current for an extended period** (hours to days) due to a network contingency such as a parallel transformer outage. The limits are:

| Parameter | Limit |
|---|---|
| Hot-spot temperature | **120 °C maximum** |
| Top-oil temperature | **105 °C maximum** |
| Load factor K | Determined by thermal calculation; typically 1.1–1.3 pu |

At 120 °C the ageing acceleration factor *V* ≈ 8.1 (IEC 60076-7 Annex B), meaning insulation ages approximately 8× faster than normal. This is acceptable for limited periods but must be tracked and reported.

The permissible duration of long-time emergency loading depends on:
- The accumulated loss of life at the overload rate.
- The probability of restoring normal network topology (how quickly can the outage be repaired?).
- The asset's remaining insulation life and its strategic importance.

### 1.3 Short-Time Emergency Loading

Short-time emergency loading allows a very high peak load for a brief period (typically 0.5–1 hour) to ride through a severe contingency or to enable emergency load transfer. The limits are:

| Parameter | Limit |
|---|---|
| Hot-spot temperature | **140 °C maximum** |
| Top-oil temperature | **115 °C maximum** |
| Load factor K | Typically up to 1.5 pu (depends on transformer parameters) |

At 140 °C the ageing acceleration factor *V* ≈ 52, meaning insulation ages 52× faster than normal. A 30-minute event at 140 °C consumes the equivalent of approximately 26 hours of normal life — a significant but usually acceptable cost to preserve network integrity during a major contingency.

---

## 2. Temperature Limits Summary

| Loading category | Hot-spot limit [°C] | Top-oil limit [°C] | Typical duration |
|---|---|---|---|
| Normal cyclic | 98 (long-term reference) | 95 (IEC design limit) | Continuous |
| Long-time emergency | 120 | 105 | Hours to days |
| Short-time emergency | 140 | 115 | 0.5–1 hour |

These limits apply to **mineral oil with standard Kraft paper insulation**. For thermally upgraded paper (TUP), some utilities apply slightly elevated temperature limits under an agreed loading specification — consult the transformer manufacturer and applicable utility standard.

---

## 3. Hot-Spot Temperature and Ageing Rate

The relationship between hot-spot temperature and insulation ageing rate is governed by the Arrhenius equation (IEC 60076-7 Annex B, Eq. B.1):

```
V = exp[B / (98 + 273) − B / (θ_h + 273)]
```

with B = 15 000 K. Key values for engineering planning:

| Hot-spot θ_h [°C] | Ageing factor V | Equivalent normal-life hours per actual hour |
|---|---|---|
| 80 | 0.21 | 1 hour of operation = 0.21 h equivalent |
| 90 | 0.53 | 1 hour of operation = 0.53 h equivalent |
| 98 (reference) | 1.00 | 1 hour = 1 hour normal ageing |
| 105 | 2.01 | 1 hour = 2.0 h equivalent |
| 110 | 3.15 | 1 hour = 3.2 h equivalent |
| 120 | 8.11 | 1 hour = 8.1 h equivalent |
| 130 | 20.4 | 1 hour = 20.4 h equivalent |
| 140 | 52.3 | 1 hour = 52.3 h equivalent |

Night-time and weekend off-peak operation (hot-spot < 98 °C) partially offsets ageing consumed during peak overloads. An annual loss-of-life budget can be established by integrating *V* over the full annual load curve.

---

## 4. Pre-Load State and Thermal History

The transformer's thermal state before an overload event significantly affects how quickly the hot-spot temperature rises during the overload:

- A unit at **K = 0.5** (light load, cool oil) before the overload has substantial thermal inertia — the oil time constant (typically 1.5–3 hours for ONAN) means the hot-spot temperature will not reach its new steady-state value during a 30-minute overload.
- A unit at **K = 0.9** (near-rated, hot oil) has little thermal headroom and will reach near-steady-state temperature much sooner.

The `permissible_overload()` method takes a `pre_load_factor` parameter for documentation and context. The current implementation returns steady-state temperatures, which is **conservative** (safe-side) because it ignores the thermal lag that keeps actual temperatures below steady-state during short overloads. For precise short-duration (< 1 hour) analysis, the full transient approach per IEC 60076-7 Annex A should be used.

---

## 5. Worked Example — Overload Assessment

**Scenario:** A 10 MVA, 33/11 kV ONAN transformer must carry 115% load for 4 hours during the loss of a parallel unit on a hot summer afternoon. The ambient temperature is 40 °C and the pre-event load was 80% (K₁ = 0.8).

**Step 1 — Identify the loading category:**

Duration = 4 hours → **Long-time emergency loading.**  
Limits: hot-spot ≤ 120 °C, top-oil ≤ 105 °C.

**Step 2 — Set up the thermal model:**

```python
from transformer.thermal import ThermalModel
from transformer.loading import LoadingCalculator

thermal = ThermalModel(
    rated_top_oil_rise_K=55.0,
    rated_winding_gradient_K=23.0,
    ratio_load_to_no_load_loss=6.07,   # 85/14 kW
    cooling_mode="ONAN",
    hot_spot_factor=1.3,
)

calc = LoadingCalculator(
    thermal_model=thermal,
    max_hot_spot_C=120.0,   # long-time emergency limit
    max_top_oil_C=105.0,
)
```

**Step 3 — Determine maximum permissible overload:**

```python
result = calc.permissible_overload(
    ambient_C=40.0,
    pre_load_factor=0.8,
    duration_h=4.0,
)
# Result: max_load_factor ≈ 1.105 pu
# hot_spot_C ≈ 120.0 °C  (at the limit)
# top_oil_C  ≈  99.3 °C
# limiting_constraint: "hot-spot limit (120 °C)"
```

The maximum permissible steady-state load under these conditions is approximately **1.105 pu** (110.5% of rated). If the required load is only 1.15 pu (115%), this exceeds the long-time emergency limit. Two options:

1. **Reduce duration:** 115% may be acceptable for a shorter period (e.g., 1 hour short-time emergency, limit 140 °C), or  
2. **Activate forced cooling** if the unit has ONAF or OFAF cooling stages — switching to OFAF (x=1.0, lower Δθ_or) may raise the permissible K₂ to 1.2 or above.

**Step 4 — Calculate the loss of insulation life:**

```python
# Assess the full overload event as a 4-hour period at the maximum permitted K
lol = calc.cumulative_loss_of_life(
    load_profile=[(1.105, 4.0)],
    ambient_C=40.0,
)
# lol ≈ 0.000162% per hour × 4 h = 0.000648%
# Equivalent normal life consumed: 0.000648/0.0005 ≈ 1.3× normal rate for 4 hours
```

**Step 5 — Decision:**

The 4-hour overload at K = 1.105 consumes approximately 1.3× the normal 4-hour ageing allowance. For a transformer with remaining life measured in decades, this is acceptable — document the event, schedule the next DGA sample 3 months earlier than planned, and initiate the parallel unit repair.

---

## 6. Cyclic Loading and Annual Life Budget

For a transformer operating on a known daily load cycle, `cumulative_loss_of_life()` can integrate the full 24-hour (or annual) ageing:

```python
# Daily load profile (K, hours)
profile = [
    (0.45, 6.0),   # Night
    (0.80, 4.0),   # Morning
    (1.00, 6.0),   # Peak
    (0.95, 4.0),   # Afternoon
    (0.70, 4.0),   # Evening
]
daily_lol = calc.cumulative_loss_of_life(profile, ambient_C=35.0)
annual_lol = daily_lol * 365
# Compare annual_lol against 0.0438% (= 1/200000 × 8760h × 100%)
# If annual_lol < 0.0438%, the transformer ages at less than normal rate
```

This approach allows asset managers to trade peak overloads (higher ageing rate) against overnight periods at light load (lower ageing rate) to achieve an acceptable annual total.

---

## 7. Cooling Mode Comparison

Switching a transformer from ONAN to a higher cooling mode (if cooling fans or pumps are fitted) substantially increases permissible loading:

```python
for mode, delta_or, delta_hr in [
    ("ONAN", 55.0, 23.0),
    ("ONAF", 55.0, 20.0),
    ("OFAF", 45.0, 17.0),
]:
    tm = ThermalModel(delta_or, delta_hr, 6.07, mode, 1.3)
    lc = LoadingCalculator(tm, max_hot_spot_C=120.0, max_top_oil_C=105.0)
    r = lc.permissible_overload(40.0, 0.8, 4.0)
    print(f"{mode}: max K₂ = {r['max_load_factor']:.3f}")
```

For a unit with both ONAN and ONAF capability, switching fans on during a contingency event can be the difference between managing the overload safely and exceeding the thermal limit.

---

## References

- IEC 60076-7:2018, §7.3 — *Permissible loading*
- IEC 60076-7:2018, Annex A — *Numerical calculation of transient top-oil and hot-spot temperatures*
- IEC 60076-7:2018, Annex B — *Ageing rate of insulation and loss-of-life calculation*
- IEEE C57.91-2011, *IEEE Guide for Loading Mineral-Oil-Immersed Transformers*
- CIGRE TB 659 (2016), *Transformer Thermal Modelling*
