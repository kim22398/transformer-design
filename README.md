# Transformer Design, Testing & Monitoring Toolkit

A professional Python toolkit for power engineers covering transformer ratings, thermal modelling (IEC 60076-7), protection coordination, OLTC analysis, dissolved-gas analysis, and permissible loading calculations.

## Features

| Module | Capability |
|---|---|
| `transformer.ratings` | Nameplate calculations, turns ratio, current ratings, efficiency |
| `transformer.thermal` | IEC 60076-7 top-oil & hot-spot temperature rise, loss-of-life |
| `transformer.protection` | Differential, overcurrent, REF relay settings, Buchholz threshold |
| `transformer.tap_changer` | OLTC optimal-tap selection, voltage regulation |
| `transformer.oil_analysis` | Dissolved-gas analysis (Duval Triangle + Rogers Ratios), BDV, moisture |
| `transformer.loading` | Permissible overload factor per IEC 60076-7 cyclic loading |

## Installation

```bash
git clone https://github.com/<your-org>/transformer-design.git
cd transformer-design
pip install -r requirements.txt
```

## Quick Start

```python
from transformer.ratings import TransformerRatings
from transformer.thermal import ThermalModel

tr = TransformerRatings(
    kva=10_000,
    primary_kv=33,
    secondary_kv=11,
    impedance_pct=6.25,
    no_load_loss_kw=14.0,
    load_loss_kw=85.0,
    vector_group="Dyn11",
)

print(f"Turns ratio       : {tr.turns_ratio():.4f}")
print(f"Primary current   : {tr.primary_current_A():.2f} A")
print(f"Secondary current : {tr.secondary_current_A():.2f} A")
print(f"Efficiency (pf=0.9): {tr.full_load_efficiency_pct():.3f} %")

thermal = ThermalModel(rated_top_oil_rise_K=55, rated_winding_gradient_K=23)
print(f"Hot-spot @ 1.0 pu, 30 °C: {thermal.hot_spot_temp(1.0, 30):.1f} °C")
```

Run the full health-check audit:

```bash
python examples/transformer_audit.py
```

Run tests:

```bash
pytest tests/ -v
```

## Standards References

- **IEC 60076-7:2018** — Loading guide for oil-immersed power transformers
- **IEC 60599:2022** — Dissolved gas analysis and interpretation
- **IEEE C57.104-2019** — Dissolved gas analysis of mineral insulating oil
- **IEC 60076-1:2011** — General requirements (ratings)
- **IEEE C57.13-2016** — Instrument transformers for protection

## Project Structure

```
transformer-design/
├── transformer/
│   ├── __init__.py
│   ├── ratings.py
│   ├── thermal.py
│   ├── protection.py
│   ├── tap_changer.py
│   ├── oil_analysis.py
│   └── loading.py
├── examples/
│   └── transformer_audit.py
├── tests/
│   └── test_thermal.py
├── requirements.txt
└── README.md
```

## License

MIT
