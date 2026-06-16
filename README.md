# Transformer Design, Testing & Monitoring Toolkit

[![Python](https://img.shields.io/badge/python-3.10%2B-blue.svg)](https://www.python.org/)
[![License: MIT](https://img.shields.io/badge/license-MIT-green.svg)](LICENSE)
[![Tests](https://img.shields.io/badge/tests-pytest-brightgreen.svg)](tests/)
[![IEC 60076-7](https://img.shields.io/badge/standard-IEC%2060076--7-orange.svg)](https://www.iec.ch/)
[![IEEE C57](https://img.shields.io/badge/standard-IEEE%20C57-orange.svg)](https://www.ieee.org/)

A professional Python toolkit for power engineers covering transformer ratings, thermal modelling per IEC 60076-7, protection relay coordination, on-load tap-changer (OLTC) analysis, dissolved-gas analysis (DGA), and permissible loading calculations. Every module is grounded in published IEC and IEEE standards and is intended for use in engineering studies, commissioning reports, and in-service condition monitoring.

---

## Table of Contents

1. [Theory & Standards](#theory--standards)
2. [Features](#features)
3. [Project Structure](#project-structure)
4. [Installation](#installation)
5. [Quick Start](#quick-start)
6. [API Reference](#api-reference)
7. [Use Cases](#use-cases)
8. [Engineering Standards](#engineering-standards)
9. [Running the Tests](#running-the-tests)
10. [License](#license)

---

## Theory & Standards

This toolkit is built on the following body of standards and engineering theory:

### IEC 60076 Series — Power Transformers

| Standard | Scope |
|---|---|
| **IEC 60076-1:2011** | General requirements; rated quantities, nameplate markings, vector groups |
| **IEC 60076-3:2013** | Insulation levels, dielectric tests, and external clearances |
| **IEC 60076-5:2006** | Ability to withstand short circuit; electrodynamic and thermal withstand |
| **IEC 60076-7:2018** | Loading guide for oil-immersed power transformers; thermal model, loss-of-life |

### IEEE C57 Series — Transformers

| Standard | Scope |
|---|---|
| **IEEE C57.91-2011** | Guide for loading mineral-oil-immersed transformers; Arrhenius ageing model |
| **IEEE C57.104-2019** | Dissolved gas analysis (DGA) of mineral insulating oil; TDCG limits |
| **IEEE C57.13-2016** | Requirements for instrument transformers used for protection |

### DGA & Oil Quality

| Standard | Scope |
|---|---|
| **IEC 60599:2022** | Interpretation of DGA results from mineral oil; Duval Triangle method |
| **IEC 60156:2018** | Dielectric breakdown voltage (BDV) measurement and acceptance limits |
| **IEC 60422:2013** | Maintenance and supervision guide for mineral insulating oil |

### Protection

| Standard | Scope |
|---|---|
| **IEC 60255-87:2017** | Functional requirements for transformer differential protection (87T) |
| **IEC 60255-151:2009** | Functional requirements for overcurrent protection (51/51N) |
| **NFPA 70E** | Electrical safety in the workplace; arc-flash hazard boundary |

### Thermal Model Overview

The IEC 60076-7 exponential (non-linear) thermal model computes steady-state temperatures via two coupled equations:

**Top-oil temperature rise** (IEC 60076-7 Eq. 2):

```
Δθ_o = Δθ_or · [(1 + R·K²) / (1 + R)]^x
```

**Hot-spot temperature** (IEC 60076-7 Eq. 3):

```
θ_h = θ_a + Δθ_o + H · Δθ_hr · K^y
```

**Arrhenius ageing acceleration factor** (IEC 60076-7 Annex B, Eq. B.1):

```
V = exp[B/(θ_hr,ref + 273) − B/(θ_h + 273)]
```

where `B = 15 000 K`, `θ_hr,ref = 98 °C`, and normal insulation life is 200 000 hours.

The thermal exponents `x` and `y` depend on the cooling mode (ONAN/ONAF/OFAF/ODAF) and are tabulated in IEC 60076-7 Table 2.

---

## Features

| Module | Capability | Standard |
|---|---|---|
| `transformer.ratings` | Nameplate calculations, turns ratio, current ratings, impedance, efficiency | IEC 60076-1 |
| `transformer.thermal` | Top-oil & hot-spot temperature rise, ageing acceleration, loss-of-life | IEC 60076-7 |
| `transformer.protection` | Differential (87T), overcurrent (51), REF (64REF), Buchholz settings | IEC 60255-87, IEC 60255-151 |
| `transformer.tap_changer` | OLTC optimal-tap selection, voltage regulation, Kapp formula | IEC 60076-1 |
| `transformer.oil_analysis` | DGA via Duval Triangle + Rogers Ratios, BDV assessment, moisture saturation | IEC 60599, IEEE C57.104 |
| `transformer.loading` | Permissible overload factor; cyclic and emergency loading; loss-of-life | IEC 60076-7 §7.3 |

---

## Project Structure

```
transformer-design/
│
├── transformer/                  # Core library package
│   ├── __init__.py               # Package metadata
│   ├── ratings.py                # Nameplate & electrical rating calculations
│   ├── thermal.py                # IEC 60076-7 exponential thermal model
│   ├── protection.py             # 87T, 51, 64REF, Buchholz relay settings
│   ├── tap_changer.py            # OLTC tap selection and voltage regulation
│   ├── oil_analysis.py           # DGA (Duval Triangle + Rogers), BDV, moisture
│   └── loading.py                # Permissible loading and loss-of-life cycle
│
├── examples/
│   └── transformer_audit.py      # Full health-check audit for a 10 MVA unit
│
├── docs/
│   ├── thermal_model_guide.md    # IEC 60076-7 thermal model deep-dive
│   ├── dga_interpretation_guide.md  # DGA methods, Duval Triangle, Rogers Ratios
│   ├── protection_guide.md       # Protection philosophy and relay coordination
│   ├── loading_guide.md          # Permissible loading, overload assessment
│   └── getting_started.md        # Tutorial: running transformer_audit.py
│
├── tests/
│   └── test_thermal.py           # Pytest suite for the thermal module
│
├── requirements.txt              # numpy, pandas, matplotlib, scipy, pytest
└── README.md                     # This file
```

---

## Installation

**Prerequisites:** Python 3.10 or later.

```bash
git clone https://github.com/<your-org>/transformer-design.git
cd transformer-design
pip install -r requirements.txt
```

No compiled extensions are required; all dependencies are pure Python or wheel-distributed.

---

## Quick Start

### Ratings

```python
from transformer.ratings import TransformerRatings

tr = TransformerRatings(
    kva=10_000,
    primary_kv=33.0,
    secondary_kv=11.0,
    impedance_pct=6.25,
    no_load_loss_kw=14.0,
    load_loss_kw=85.0,
    vector_group="Dyn11",
)

print(f"Turns ratio       : {tr.turns_ratio():.4f}")
print(f"Primary current   : {tr.primary_current_A():.2f} A")
print(f"Secondary current : {tr.secondary_current_A():.2f} A")
print(f"Efficiency (pf=0.9): {tr.full_load_efficiency_pct():.3f} %")
print(f"Zsc (HV side)     : {tr.short_circuit_impedance_ohm_primary():.3f} Ω")
```

### Thermal Model

```python
from transformer.thermal import ThermalModel

thermal = ThermalModel(
    rated_top_oil_rise_K=55.0,
    rated_winding_gradient_K=23.0,
    ratio_load_to_no_load_loss=6.07,
    cooling_mode="ONAN",
    hot_spot_factor=1.3,
)

for k in [0.75, 1.0, 1.2]:
    hs = thermal.hot_spot_temp(k, ambient_C=35.0)
    aaf = thermal.aging_acceleration_factor(hs)
    print(f"K={k:.2f}  θ_h={hs:.1f}°C  AAF={aaf:.3f}")
```

### DGA

```python
from transformer.oil_analysis import OilAnalysis

oil = OilAnalysis()
result = oil.parse_dissolved_gas(
    h2=180, ch4=290, c2h2=4, c2h4=310, c2h6=75, co=620, co2=4100
)
print(result["duval"].fault_description)
print(result["rogers"].recommendation)
print(result["tdcg_condition"])
```

### Permissible Overload

```python
from transformer.loading import LoadingCalculator

calc = LoadingCalculator(
    thermal_model=thermal,
    max_hot_spot_C=120.0,   # long-time emergency limit per IEC 60076-7
    max_top_oil_C=105.0,
)
result = calc.permissible_overload(ambient_C=40.0, pre_load_factor=0.8, duration_h=4.0)
print(f"Max overload: {result['max_load_factor']:.3f} pu")
print(f"Hot-spot    : {result['hot_spot_C']:.1f} °C")
print(f"Constraint  : {result['limiting_constraint']}")
```

### Full Audit

```bash
python examples/transformer_audit.py
```

---

## API Reference

### `transformer.ratings.TransformerRatings`

```
TransformerRatings(kva, primary_kv, secondary_kv, impedance_pct,
                   no_load_loss_kw, load_loss_kw, vector_group="Dyn11")
```

| Method | Returns | Description |
|---|---|---|
| `turns_ratio()` | `float` | Voltage turns ratio V₁/V₂ |
| `primary_current_A()` | `float` | Rated HV line current [A] |
| `secondary_current_A()` | `float` | Rated LV line current [A] |
| `full_load_efficiency_pct(pf=0.9)` | `float` | Full-load efficiency [%] |
| `short_circuit_impedance_ohm_primary()` | `float` | Zsc referred to HV side [Ω] |

---

### `transformer.thermal.ThermalModel`

```
ThermalModel(rated_top_oil_rise_K=55.0, rated_winding_gradient_K=23.0,
             ratio_load_to_no_load_loss=6.0, cooling_mode="ONAN",
             hot_spot_factor=1.3)
```

`cooling_mode` choices: `"ONAN"` | `"ONAF"` | `"OFAF"` | `"ODAF"`

| Method | Returns | Description |
|---|---|---|
| `top_oil_rise(load_factor, ambient_C=20.0)` | `float` | Steady-state top-oil rise above ambient [K] |
| `hot_spot_temp(load_factor, ambient_C=20.0)` | `float` | Steady-state hot-spot temperature [°C] |
| `aging_acceleration_factor(hot_spot_C)` | `float` | Arrhenius ageing factor *V* relative to 98 °C |
| `loss_of_life_pct_per_hour(hot_spot_C)` | `float` | Insulation life consumed per hour [%] |

---

### `transformer.protection.TransformerProtection`

| Method | Returns | Description |
|---|---|---|
| `differential_current(i_primary, i_secondary, ctr_primary, ctr_secondary)` | `(i_op, i_res, slope_pct)` | 87T operate/restraint currents and slope [%] |
| `overcurrent_pickup(load_kva, voltage_kv, multiplier=1.25)` | `float` | 51/51N relay pickup current [A] |
| `restricted_earth_fault(i_neutral, i_phases)` | `(i_spill, operate)` | 64REF spill current and operate flag |
| `buchholz_gas_volume_threshold_ml()` | `dict` | Buchholz alarm/trip gas-volume thresholds |

---

### `transformer.tap_changer.OLTCAnalyzer`

| Method | Returns | Description |
|---|---|---|
| `optimal_tap(measured_voltage_kv, target_voltage_kv, tap_step_pct, n_taps)` | `(tap_pos, achieved_kv, residual_pct)` | Best OLTC tap position and achieved voltage |
| `voltage_regulation_pct(no_load_v, full_load_v)` | `float` | Measured voltage regulation [%] |
| `approximate_regulation_pct(impedance_pct, resistance_pct, power_factor=0.9)` | `float` | Kapp formula voltage regulation [%] |

---

### `transformer.oil_analysis.OilAnalysis`

| Method | Returns | Description |
|---|---|---|
| `parse_dissolved_gas(h2, ch4, c2h2, c2h4, c2h6, co, co2)` | `dict` | Full DGA report: Duval + Rogers + TDCG condition |
| `dielectric_breakdown_kv_rating(measured_kv)` | `dict` | BDV PASS/FAIL assessment vs IEC 60156 |
| `moisture_ppm_to_saturation_pct(ppm, temp_C)` | `float` | Relative water saturation [%] at oil temperature |

The `dict` returned by `parse_dissolved_gas` contains:

| Key | Type | Description |
|---|---|---|
| `"duval"` | `DGAResult` | Duval Triangle diagnosis |
| `"rogers"` | `DGAResult` | Rogers Ratios diagnosis |
| `"gases_ppm"` | `dict` | Raw gas concentrations |
| `"tdcg_ppm"` | `float` | Total dissolved combustible gas |
| `"tdcg_condition"` | `str` | IEEE C57.104 condition (1–4) |
| `"cellulose_involved"` | `bool` | True if CO/CO₂ ratio > 0.1 |

---

### `transformer.loading.LoadingCalculator`

```
LoadingCalculator(thermal_model, max_hot_spot_C=98.0, max_top_oil_C=105.0)
```

| Method | Returns | Description |
|---|---|---|
| `permissible_overload(ambient_C, pre_load_factor, duration_h)` | `dict` | Maximum load factor K₂ within thermal limits |
| `cumulative_loss_of_life(load_profile, ambient_C)` | `float` | Insulation life consumed for a load cycle [%] |

`permissible_overload` result keys: `max_load_factor`, `hot_spot_C`, `top_oil_C`, `limiting_constraint`, `ambient_C`, `pre_load_factor`, `duration_h`.

`load_profile` is a list of `(load_factor, duration_h)` tuples representing successive load steps.

---

## Use Cases

### 1. New Transformer Commissioning

Run `transformer_audit.py` (or call the individual modules) immediately after energisation to establish baseline values:

- Verify nameplate turns ratio, impedance, and current ratings against factory test certificates.
- Perform a thermal pre-assessment to confirm that the unit can meet its rated capacity at the site's maximum ambient temperature.
- Record the initial dissolved-gas fingerprint from a commissioning oil sample to use as a reference for future trend analysis.
- Calculate the recommended overcurrent pickup settings (51/51N) and differential relay slope (87T) based on the confirmed CT ratios and nameplate data.

### 2. In-Service Condition Monitoring

Schedule periodic oil sampling (typically annually for sealed units; more frequently if TDCG is elevated) and pass the laboratory results directly to `OilAnalysis.parse_dissolved_gas()`:

```python
oil = OilAnalysis()
result = oil.parse_dissolved_gas(**lab_report)
if result["tdcg_condition"].startswith("Condition 3"):
    alert("Plan outage — high TDCG")
if result["cellulose_involved"]:
    alert("Cellulose degradation indicated — check moisture and CO/CO₂ trend")
```

Compare successive TDCG values to identify rate-of-rise trends, which are often more diagnostic than absolute values alone.

### 3. Overload Assessment

During network contingency events (loss of a parallel transformer, sudden load transfer), use `LoadingCalculator` to determine whether the transformer can carry the overload without exceeding insulation life limits:

```python
calc = LoadingCalculator(thermal, max_hot_spot_C=140.0, max_top_oil_C=115.0)
result = calc.permissible_overload(ambient_C=40.0, pre_load_factor=0.9, duration_h=0.5)
print(f"Short-time emergency: {result['max_load_factor']:.2f} pu for 30 min")
```

The three loading categories (normal cyclic, long-time emergency, short-time emergency) are discussed in detail in [docs/loading_guide.md](docs/loading_guide.md).

### 4. DGA Fault Diagnosis

When unexpected gas generation is detected, correlate the Duval Triangle and Rogers Ratios results to narrow the fault type:

| Both methods agree → | High confidence — act on the recommendation |
|---|---|
| Methods disagree → | Use Duval as primary (it is generally more reliable for mixed faults) |
| Rapid gas rate-of-rise → | De-energise regardless of fault type classification |

A step-by-step interpretation walkthrough is provided in [docs/dga_interpretation_guide.md](docs/dga_interpretation_guide.md).

---

## Engineering Standards

| Standard | Edition | Application in this toolkit |
|---|---|---|
| **IEC 60076-1** | 2011 | Ratings, turns ratio, short-circuit impedance (`ratings.py`) |
| **IEC 60076-3** | 2013 | Insulation levels referenced in BDV acceptance criteria |
| **IEC 60076-5** | 2006 | Short-circuit withstand; fault current magnitude in protection |
| **IEC 60076-7** | 2018 | Thermal model, ageing, loss-of-life, loading limits (`thermal.py`, `loading.py`) |
| **IEC 60599** | 2022 | Duval Triangle DGA classification (`oil_analysis.py`) |
| **IEC 60156** | 2018 | BDV acceptance criterion (60 kV for > 72.5 kV systems) |
| **IEEE C57.91** | 2011 | Arrhenius ageing model, B = 15 000 K constant |
| **IEEE C57.104** | 2019 | Rogers Ratios, TDCG condition thresholds 1–4 (`oil_analysis.py`) |
| **IEC 60255-87** | 2017 | 87T differential protection functional requirements (`protection.py`) |
| **IEC 60255-151** | 2009 | 51/51N overcurrent protection (`protection.py`) |
| **NFPA 70E** | 2024 | Electrical safety; arc-flash boundaries during relay work |

---

## Running the Tests

```bash
pytest tests/ -v
```

The test suite validates the IEC 60076-7 thermal model against analytically derived expected values, including rated-load identity, monotonicity, Arrhenius factor at reference temperature, and cooling-mode exponent assignments.

---

## Documentation

| Guide | Description |
|---|---|
| [Thermal Model Guide](docs/thermal_model_guide.md) | Deep-dive into IEC 60076-7 thermal equations, cooling modes, and ageing |
| [DGA Interpretation Guide](docs/dga_interpretation_guide.md) | Duval Triangle, Rogers Ratios, TDCG limits, worked example |
| [Protection Guide](docs/protection_guide.md) | 87T, 51, 64REF, Buchholz — settings philosophy and coordination |
| [Loading Guide](docs/loading_guide.md) | Normal, emergency, and short-time overload assessment per IEC 60076-7 |
| [Getting Started Tutorial](docs/getting_started.md) | Walk through transformer_audit.py output section by section |

---

## License

MIT — see [LICENSE](LICENSE) for full text.
