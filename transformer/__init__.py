"""
Transformer Design, Testing & Monitoring Toolkit
-------------------------------------------------
A professional Python library for power engineers providing:

- Nameplate rating calculations (IEC 60076-1)
- Thermal modelling and insulation ageing (IEC 60076-7)
- Protection relay setting calculations (IEC 60255-87, IEC 60255-151)
- On-load tap-changer analysis
- Dissolved-gas analysis (IEC 60599, IEEE C57.104)
- Permissible loading and loss-of-life assessment (IEC 60076-7)

Typical usage::

    from transformer.ratings import TransformerRatings
    from transformer.thermal import ThermalModel
    from transformer.loading import LoadingCalculator

    tr = TransformerRatings(kva=10_000, primary_kv=33, secondary_kv=11,
                            impedance_pct=6.25, no_load_loss_kw=14,
                            load_loss_kw=85)
    tm = ThermalModel(rated_top_oil_rise_K=55, rated_winding_gradient_K=23)
    lc = LoadingCalculator(tm, max_hot_spot_C=120)
"""
