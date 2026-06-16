# IEC 60076-7 Thermal Model — Engineer's Guide

## Overview

The thermal behaviour of an oil-immersed power transformer determines both its permissible loading and its insulation ageing rate. IEC 60076-7:2018, "Loading guide for oil-immersed power transformers," provides the industry-standard framework for calculating top-oil temperature, hot-spot temperature, and insulation loss-of-life under any combination of load and ambient temperature.

This guide explains the model implemented in `transformer/thermal.py`, covering the underlying equations, the physical significance of each parameter, and practical engineering application for overload assessment.

---

## 1. Temperature Hierarchy

A transformer's thermal state is described by a three-layer temperature hierarchy:

```
Ambient temperature         θ_a          [°C]
      +
Top-oil temperature rise    Δθ_o         [K]
      =
Top-oil temperature         θ_o          [°C]
      +
Hot-spot-to-top-oil rise    H · Δθ_hr · K^y  [K]
      =
Hot-spot temperature        θ_h          [°C]
```

The **hot-spot** is the point of maximum temperature in the winding, occurring typically near the top of the high-voltage winding due to the combined effects of I²R heating and the upward circulation of heated oil. It is the hot-spot — not the average winding temperature — that governs insulation ageing.

---

## 2. Top-Oil Temperature Rise

The steady-state top-oil temperature rise above ambient follows a non-linear (exponential) relationship with load factor *K*:

```
Δθ_o = Δθ_or · [(1 + R · K²) / (1 + R)]^x        (IEC 60076-7 Eq. 2)
```

Where:

| Symbol | Meaning | Typical value |
|---|---|---|
| Δθ_or | Rated top-oil rise at full load *K* = 1 | 55 K (ONAN) |
| R | Ratio of load losses to no-load losses at rated load | 6.0 (10–63 MVA ONAN) |
| K | Load factor (per-unit load; 1.0 = rated) | 0 to ~1.5 |
| x | Oil thermal exponent (cooling-mode dependent) | 0.8 (ONAN) |

At *K* = 1 the formula reduces identically to Δθ_or, confirming correct normalisation. At *K* = 0 (energised but unloaded) the residual rise is due solely to no-load losses:

```
Δθ_o(K=0) = Δθ_or · [1/(1+R)]^x
```

The top-oil temperature itself is:

```
θ_o = θ_a + Δθ_o
```

The IEC 60076-7 Table 1 maximum permissible top-oil temperature is **105 °C** for short-time emergency loading; for normal continuous operation the limit is effectively governed by the hot-spot limit described below.

---

## 3. Hot-Spot Temperature Rise

The hot-spot temperature combines the top-oil temperature with the winding-to-top-oil gradient:

```
θ_h = θ_a + Δθ_o + H · Δθ_hr · K^y               (IEC 60076-7 Eq. 3)
```

Where:

| Symbol | Meaning | Typical value |
|---|---|---|
| H | Hot-spot factor (ratio of hot-spot gradient to average gradient) | 1.3 (ONAN/ONAF) |
| Δθ_hr | Rated hot-spot-to-top-oil gradient at *K* = 1 | 23 K (ONAN) |
| y | Winding thermal exponent (cooling-mode dependent) | 1.6 (ONAN/ONAF/OFAF) |

The hot-spot factor *H* accounts for the non-uniform distribution of leakage flux in the winding — the top turns experience higher eddy-current losses and therefore a steeper gradient. IEC 60076-7 recommends *H* = 1.3 as a default; more accurate values are obtained from heat-run test measurements or FEM analysis.

---

## 4. Thermal Time Constants

The equations above describe **steady-state** temperatures. In practice, thermal time constants determine how quickly the transformer responds to load changes:

- **Oil thermal time constant** τ_o: the time for the top-oil rise to reach 63% of its new steady-state value after a step change in load. Typical values are 1.5–3.0 hours for ONAN transformers, shorter for forced-cooling modes.
- **Winding thermal time constant** τ_w: the time for the hot-spot gradient to respond to a load change. Typically 5–10 minutes — much shorter than the oil time constant.

For **short-duration overloads** (less than τ_o), the oil does not fully heat up and the transient hot-spot temperature is lower than the steady-state value predicted by the equations above. This toolkit uses the steady-state equations, which are conservative (safe-side) for overload assessment. The full differential equation approach from IEC 60076-7 Annex A can be implemented via numerical integration for more precise short-duration analysis.

---

## 5. Thermal Exponents by Cooling Mode

IEC 60076-7 Table 2 specifies the thermal exponents for each standard cooling mode:

| Cooling mode | x (oil exponent) | y (winding exponent) | Typical Δθ_or |
|---|---|---|---|
| ONAN — Oil Natural, Air Natural | 0.8 | 1.6 | 55 K |
| ONAF — Oil Natural, Air Forced | 0.9 | 1.6 | 55 K |
| OFAF — Oil Forced, Air Forced | 1.0 | 1.6 | 45 K |
| ODAF — Oil Directed, Air Forced | 1.0 | 2.0 | 40–45 K |

**Physical interpretation:**

- The oil exponent `x` governs how strongly the oil temperature rise responds to load. ONAN has the weakest response (x = 0.8) because natural convection creates a self-reinforcing buoyancy effect that improves heat transfer at higher temperatures. Forced-oil cooling (OFAF/ODAF, x = 1.0) approaches a linear relationship.
- The winding exponent `y` reflects the relative contribution of eddy-current losses. ODAF (y = 2.0) has higher eddy losses in the directed-flow winding design; the other modes share y = 1.6.

A transformer with multiple cooling stages (e.g., ONAN/ONAF) should use the exponents corresponding to the active cooling stage at the time of assessment.

---

## 6. Arrhenius Ageing Acceleration Factor

Oil-impregnated cellulose (Kraft paper) insulation degrades primarily through thermal hydrolysis. The rate of degradation follows an Arrhenius relationship with absolute temperature, giving an **ageing acceleration factor** *V* that quantifies how much faster (or slower) ageing proceeds compared to operation at the reference hot-spot temperature of 98 °C:

```
V = exp[B / (θ_hr,ref + 273) − B / (θ_h + 273)]    (IEC 60076-7 Annex B, Eq. B.1)
```

Where:

| Symbol | Meaning | Value |
|---|---|---|
| B | Activation energy / Boltzmann constant for Kraft paper | 15 000 K |
| θ_hr,ref | Reference hot-spot temperature for normal ageing | 98 °C |
| θ_h | Actual hot-spot temperature | variable |

Key values:

| Hot-spot [°C] | V (AAF) | Meaning |
|---|---|---|
| 80 | 0.21 | Ageing is 5× slower than normal |
| 98 | 1.00 | Normal ageing rate |
| 110 | 3.15 | Ageing 3× faster than normal |
| 120 | 8.11 | Ageing 8× faster than normal |
| 140 | 52.3 | Ageing 52× faster than normal |

The "rule of thumb" that ageing roughly doubles for each 6 K temperature rise near 98 °C (Montsinger's rule) is consistent with the Arrhenius model for the B = 15 000 K constant.

**Thermally upgraded paper** (with additives that stabilise against oxidation) has a longer normal insulation life — IEC 60076-7 Table B.1 cites 300 000 hours — but uses the same Arrhenius exponent. This toolkit uses the standard 200 000 h base; modify `loss_of_life_pct_per_hour()` to use 300 000 h for thermally upgraded units.

---

## 7. Loss-of-Life Calculation

The percentage of insulation life consumed per hour is:

```
L [%/h] = (V / L_normal) × 100
```

where `L_normal = 200 000` hours for standard Kraft paper.

For a load cycle consisting of *n* steps, each at load factor *K_i* for *h_i* hours, the total percentage loss of insulation life is:

```
LOL [%] = Σ_i [ L(θ_h(K_i)) × h_i ]
```

This is implemented in `LoadingCalculator.cumulative_loss_of_life()`. An annual LOL of 0.0438% (corresponding to 24 h/day × 365 days = 8 760 h at the reference hot-spot) constitutes normal life expenditure.

**Worked example:**

A transformer operates for 4 hours at K = 1.2 during a summer peak, with θ_a = 40 °C:

```python
thermal = ThermalModel(55, 23, 6.07, "ONAN", 1.3)
hs = thermal.hot_spot_temp(1.2, 40.0)    # → 128.3 °C
V  = thermal.aging_acceleration_factor(hs) # → 18.4
lol_4h = thermal.loss_of_life_pct_per_hour(hs) * 4  # → 0.000368%
```

This 4-hour overload period consumes roughly 18× the normal rate — equivalent to approximately 73 hours of normal operation.

---

## 8. Cooling Mode Impact on Overload Capability

Forced cooling significantly improves overload capacity by reducing both the rated top-oil rise and the sensitivity of the oil temperature to load:

| Cooling mode | Max K (θ_a=40°C, θ_h,max=120°C) | Notes |
|---|---|---|
| ONAN (Δθ_or=55 K) | ≈ 1.11 pu | Limited by natural convection |
| ONAF (Δθ_or=55 K) | ≈ 1.13 pu | Fan cooling reduces oil gradient sensitivity |
| OFAF (Δθ_or=45 K) | ≈ 1.25 pu | Forced oil significantly improves heat transfer |
| ODAF (Δθ_or=40 K) | ≈ 1.28 pu | Directed flow maximises winding cooling |

These figures are approximate and depend on the specific *R*, *H*, and Δθ_hr values for a given unit. Always use the factory nameplate thermal parameters in the model.

---

## 9. Practical Application for Overload Assessment

When the network requires a transformer to carry more than rated current (contingency loading, n-1 condition), the following procedure applies:

1. **Identify the loading category** (IEC 60076-7 §7.3):
   - *Normal cyclic loading*: daily peak does not significantly accelerate ageing over the year.
   - *Long-time emergency loading*: hours to days; hot-spot limit 120 °C; top-oil limit 105 °C.
   - *Short-time emergency loading*: typically 0.5–1 hour; hot-spot limit 140 °C; top-oil limit 115 °C.

2. **Establish pre-load conditions**: what is the transformer's load immediately before the overload? A unit already at K = 0.9 will be hotter than one at K = 0.5 and will have less overload headroom.

3. **Call `permissible_overload()`** with the appropriate `max_hot_spot_C` and `max_top_oil_C` for the loading category.

4. **Assess loss-of-life impact** using `cumulative_loss_of_life()` over the full event duration to determine whether the event is acceptable from an asset-management perspective.

5. **Document** the result in the maintenance record, noting the overload magnitude, duration, ambient temperature, and estimated loss of insulation life.

---

## References

- IEC 60076-7:2018, *Power transformers — Part 7: Loading guide for oil-immersed power transformers*
- IEEE C57.91-2011, *IEEE Guide for Loading Mineral-Oil-Immersed Transformers*
- Montsinger, V.M. (1930). "Loading transformers by temperature." *AIEE Trans.* 49(2): 776–792.
- Oommen, T.V. (1984). "Moisture equilibrium in paper-oil insulation systems." *AIEE Proc.* 6th Electrical Insulation Conference.
