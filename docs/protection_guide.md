# Transformer Protection Philosophy and Relay Coordination Guide

## Overview

Power transformer protection must balance two competing objectives: speed of fault clearance to limit damage and system disturbance; and security against undesired operation during normal transients such as energisation inrush and through-fault current. This guide explains the protection philosophy, relay types, and setting calculations implemented in `transformer/protection.py`, and provides practical coordination guidance.

---

## 1. Protection Philosophy

A transformer protection scheme is typically structured in **zones** aligned with the transformer's physical boundaries and the locations of current transformers (CTs):

```
Busbar A ──[CT1]─────────────────────[CT2]──── Busbar B
                    [TRANSFORMER]
                         │
                    [Tank/oil]
                         │
              [Buchholz relay / PRV]
```

The main protection functions for a medium/large power transformer are:

| ANSI function | Name | Zone |
|---|---|---|
| 87T | Percentage differential | Unit protection (CT1 to CT2) |
| 51/51N | Time-overcurrent / neutral OC | Backup, HV and LV side |
| 64REF | Restricted earth fault | LV winding to earth |
| 26/49 | Thermal overload | Winding thermal replica |
| 63 | Buchholz relay (gas/oil surge) | Tank — all internal faults |
| 63Q | OLTC Buchholz | OLTC compartment |
| 71 | Low oil level | Tank |
| 63PR | Pressure relief valve trip | Tank — catastrophic pressure |

For transformers above approximately 5 MVA, a numerical protection relay (e.g., Siemens SIPROTEC, GE T60, ABB RET series) is standard practice. For smaller units, overcurrent and Buchholz protection may be the primary system.

---

## 2. 87T — Percentage Differential Protection

### Principle

The differential relay (function 87T) is the **main unit protection** for a power transformer. It measures currents flowing into and out of the protected zone through the CTs on each winding. Under normal load or through-fault conditions the net current (the differential current) is approximately zero. An internal fault produces an imbalance that the relay detects.

**Operating and restraint quantities:**

```
I_op  = |I_r1 − I_r2|          (differential / operate current)
I_res = ½ (|I_r1| + |I_r2|)    (restraint current)
Slope = I_op / I_res × 100%     (operate characteristic)
```

where `I_r1` and `I_r2` are the secondary currents from the HV and LV CTs, corrected for the turns ratio so they represent the same rated current in secondary amps.

### Slope Characteristic

The relay operates when the operating current exceeds a percentage of the restraint current defined by the **slope characteristic** (also called the percentage-differential characteristic):

```
I_op > k₁ · I_res              (low-current zone, k₁ ≈ 0.15–0.25)
I_op > k₂ · I_res              (high-current zone, k₂ ≈ 0.40–0.50)
```

The dual-slope characteristic provides:
- **Sensitivity** at low currents where CT errors are small (slope k₁).
- **Security** at high through-fault currents where CT saturation increases the apparent differential current (slope k₂ begins above ≈ 2–3× rated current).

### Vector Group Compensation

For a Dyn11 transformer the HV (delta) and LV (star) windings have a 30° phase shift. The differential relay must compensate for this to avoid false operate signals. In numerical relays, software vector-group compensation is selected by setting. In older relay schemes, the CTs on the delta-connected winding were connected in star, and the star-winding CTs in delta, to introduce the compensating 30° shift.

### Inrush Restraint

Transformer energisation produces a high-magnitude magnetising inrush current that flows into the HV winding but not out of the LV winding — it appears as a large differential current. Inrush restraint prevents unwanted trips using two methods:

1. **Second-harmonic restraint:** Inrush contains a high second-harmonic component (typically 15–40% of fundamental). The relay blocks operation when the second harmonic in the differential current exceeds a threshold (typically 15–20%).
2. **Cross-blocking:** Detection of second harmonic in any phase blocks tripping on all phases (to handle asymmetric inrush that may only appear in one phase).

### Instantaneous High-Set (Unrestrained) Element

A high-set unrestrained differential element (87T-U) operates without slope restraint for very large internal fault currents (typically set at 7–10× rated current). This ensures fast clearance for bolted internal faults regardless of CT saturation.

### Settings Guidance (derived from `differential_current()`)

```python
prot = TransformerProtection()
i_op, i_res, slope = prot.differential_current(
    i_primary=175.5,      # Rated HV current [A]
    i_secondary=526.5,    # Rated LV current [A]
    ctr_primary=200,      # HV CT ratio (200/1)
    ctr_secondary=600,    # LV CT ratio (600/1)
)
# Under balanced rated load: slope ≈ CT mismatch error only
# Typical setting: minimum slope k₁ = 0.20 (20%)
```

Under a perfect balanced load with matched CTs, `I_op ≈ 0` and `slope ≈ 0%`. The slope setting must comfortably cover the worst-case CT mismatch (up to ±5% for class 5P CTs) and any residual tap-changer offset.

---

## 3. 51/51N — Overcurrent Protection

### Principle

Time-overcurrent relays provide **backup protection** for both the transformer and downstream faults that are not cleared by the primary protection. They are coordinated in time with downstream feeder protection to be selective.

### Pickup Setting (`overcurrent_pickup()`)

```
I_FL     = S / (√3 · V)         (full-load current)
I_pickup = multiplier × I_FL    (relay pickup current)
```

The default multiplier of 1.25 (125% of FLC) gives:
- Secure non-operation under maximum continuous load (including any permitted cyclic overload below 125%).
- Pickup on sustained overload that would cause thermal damage.

For protection of the HV winding against internal faults, a lower pickup (105–110% of FLC) may be used in conjunction with a definite-time delay to allow load management before tripping.

### Time-Current Characteristic

Standard IEC 60255-151 inverse-time characteristics are used:

| Characteristic | Application |
|---|---|
| Standard Inverse (SI) | Feeder and transformer backup OC |
| Very Inverse (VI) | Coordination with fuse-protected feeders |
| Extremely Inverse (EI) | Motor and inrush-heavy circuits |

The time-dial setting (TDS) is chosen to provide a coordination margin of at least 0.3 seconds above the downstream relay's operating time at the maximum fault current.

### 51N — Neutral Overcurrent

The 51N element monitors neutral current (residual or measured via a dedicated neutral CT) and provides earth-fault backup. Settings follow the same principle as the phase OC but at a lower pickup (typically 10–20% of rated current) to provide sensitivity to single-phase earth faults.

---

## 4. 64REF — Restricted Earth Fault Protection

### Principle

The restricted earth fault relay protects the **star-connected winding against earth faults**, including those near the neutral point where the driving voltage is low and differential protection sensitivity is poor.

A high-impedance REF scheme uses a neutral CT (measuring current into the transformer neutral bushing) and three-phase CTs on the LV terminals. Under normal conditions and through-fault conditions, the sum of the phase currents equals the neutral current. An internal earth fault causes a **spill current** between the two sets:

```
I_spill = I_N − (I_A + I_B + I_C)
```

The high-impedance element is set to operate when `|I_spill| > threshold` (typically 5% of rated CT secondary current, i.e., 0.05 A on a 1 A relay).

### Security Against External Faults

During external (through) faults, the phase CTs may saturate asymmetrically, producing a false spill current. The high-impedance voltage-operated design minimises this by imposing a high stabilising resistance in the relay circuit, ensuring external fault immunity even with one CT completely saturated.

### Coverage

A high-impedance REF scheme can detect earth faults down to approximately 5% from the neutral point, giving approximately 95% winding coverage. This is superior to percentage differential (87T) which typically covers only 80–85% of the winding (the bottom 15–20% is within the minimum differential current threshold).

---

## 5. Buchholz Relay (63)

### Principle

The Buchholz relay is a **non-electrical mechanical device** fitted in the oil pipe between the transformer tank and the conservator. It detects faults through two mechanisms:

1. **Gas accumulation alarm:** Slow, persistent gas generation from an incipient fault accumulates in the relay housing and eventually lifts a float, triggering an alarm. This is the most sensitive indication of a developing internal fault.
2. **Oil surge trip:** A sudden large internal fault (arcing, short circuit) causes a rapid oil pressure wave. The surge deflects a baffle plate in the Buchholz relay, triggering an instantaneous trip.

### Thresholds (from `buchholz_gas_volume_threshold_ml()`)

| Element | Threshold | Typical cause |
|---|---|---|
| Gas alarm | ≈ 100 mL accumulated gas | Slow thermal decomposition, incipient fault |
| Oil surge trip | Oil velocity ≈ 100 cm/s | Sudden internal arcing |
| Trip (gas volume) | ≈ 250 mL accumulated gas | Sustained slow fault not cleared by alarm |

When the Buchholz alarm operates, the gas should be collected and analysed using DGA methods (see [dga_interpretation_guide.md](dga_interpretation_guide.md)) before any decision is made to re-energise.

### OLTC Buchholz (63Q)

A separate Buchholz relay is fitted to the OLTC compartment. Because the OLTC oil is separate from the main tank, its gas accumulation diagnoses contact arcing and insulation problems within the tap-changer mechanism independently of the main tank.

---

## 6. Coordination Tips

### HV Overcurrent vs. Differential

The overcurrent relay (51) must be coordinated so that it does **not** trip before the downstream feeder protection for faults on the secondary bus, but **does** trip as a backup if the feeder relay fails. A typical coordination sequence for an HV-side earth fault:

```
Fault occurs (11 kV side)
→ LV feeder relay trips (t = 0.1 s)
→ If not cleared: HV 51N trips (t = 0.1 + 0.3 = 0.4 s coordination margin)
→ If not cleared (relay failure): HV 51 backup trips (t = 0.7 s)
```

### Differential vs. Buchholz

For an **internal arcing fault**, the 87T differential relay typically trips first (< 30 ms). The Buchholz oil surge element trips in parallel. Buchholz gas alarm is typically blocked from direct tripping to avoid spurious trips on oil-level variation or maintenance; instead it drives an alarm and initiates operator response.

### REF vs. Differential

For a **winding earth fault**:
- If above ≈ 15% from neutral: 87T differential will operate.
- If below ≈ 15% from neutral: 64REF is the primary protection.

Both should trip the same circuit breakers. Where possible, the 64REF trip and 87T trip should both trip the HV and LV breakers simultaneously to ensure complete isolation.

### Avoiding CT Saturation Issues

At high through-fault currents (> 10× CT rated primary), CTs may saturate and produce incorrect secondary currents. To minimise the risk:
- Specify CTs with a knee-point voltage of at least `2 × I_sc × (R_lead + R_relay)`.
- Use the high-slope region (k₂) of the differential characteristic for through-fault currents above 2–3× rated.
- Specify class 5P or 10P CTs with appropriate accuracy limiting factor for the fault level at the transformer terminals.

---

## References

- IEC 60255-87:2017, *Measuring relays and protection equipment — Functional requirements for differential protection*
- IEC 60255-151:2009, *Measuring relays and protection equipment — Functional requirements for over/under-current protection*
- IEEE C37.91-2008, *IEEE Guide for Protective Relay Applications to Power Transformers*
- Blackburn, J.L. and Domin, T.J. (2006). *Protective Relaying: Principles and Applications*. 3rd ed. CRC Press.
- Hewitson, L.G., Brown, M., and Ramesh, B. (2004). *Practical Power Systems Protection*. Elsevier.
