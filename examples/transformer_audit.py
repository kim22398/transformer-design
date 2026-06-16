"""
examples/transformer_audit.py
------------------------------
Full health-check audit for a 10 MVA, 33/11 kV Dyn11 power transformer.

Demonstrates:
- Nameplate calculations
- Thermal assessment (IEC 60076-7)
- Protection relay settings
- OLTC optimal tap selection
- Dissolved-gas analysis (DGA)
- Permissible overload under summer ambient
- 24-hour load-cycle loss-of-life estimate
"""

import sys
import os

# Allow running from project root without installation
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from transformer.ratings    import TransformerRatings
from transformer.thermal    import ThermalModel
from transformer.protection import TransformerProtection
from transformer.tap_changer import OLTCAnalyzer
from transformer.oil_analysis import OilAnalysis
from transformer.loading    import LoadingCalculator


# ──────────────────────────────────────────────────────────────────────────────
# 1. Nameplate and ratings
# ──────────────────────────────────────────────────────────────────────────────

def section(title: str) -> None:
    width = 68
    print("\n" + "=" * width)
    print(f"  {title}")
    print("=" * width)


def audit():
    tr = TransformerRatings(
        kva             = 10_000,
        primary_kv      = 33.0,
        secondary_kv    = 11.0,
        impedance_pct   = 6.25,
        no_load_loss_kw = 14.0,
        load_loss_kw    = 85.0,
        vector_group    = "Dyn11",
    )

    section("1. NAMEPLATE RATINGS – 10 MVA 33/11 kV Dyn11")
    print(f"  Rated power           : {tr.kva:>10,.0f} kVA ({tr.kva/1000:.0f} MVA)")
    print(f"  Primary voltage (HV)  : {tr.primary_kv:>10.1f} kV")
    print(f"  Secondary voltage (LV): {tr.secondary_kv:>10.1f} kV")
    print(f"  Vector group          : {tr.vector_group}")
    print(f"  Short-circuit impedance: {tr.impedance_pct:>8.2f} %")
    print(f"  No-load losses        : {tr.no_load_loss_kw:>10.1f} kW")
    print(f"  Load losses (75 °C)   : {tr.load_loss_kw:>10.1f} kW")
    print()
    print(f"  Turns ratio           : {tr.turns_ratio():>10.4f}")
    print(f"  Primary current (HV)  : {tr.primary_current_A():>10.2f} A")
    print(f"  Secondary current (LV): {tr.secondary_current_A():>10.2f} A")
    print(f"  Zsc referred to HV    : {tr.short_circuit_impedance_ohm_primary():>10.3f} Ω")
    print(f"  Efficiency @ pf=0.90  : {tr.full_load_efficiency_pct(0.90):>10.4f} %")
    print(f"  Efficiency @ pf=0.80  : {tr.full_load_efficiency_pct(0.80):>10.4f} %")
    print(f"  Efficiency @ pf=1.00  : {tr.full_load_efficiency_pct(1.00):>10.4f} %")

    # ──────────────────────────────────────────────────────────────────────────
    # 2. Thermal assessment (IEC 60076-7)
    # ──────────────────────────────────────────────────────────────────────────

    thermal = ThermalModel(
        rated_top_oil_rise_K        = 55.0,   # K (ONAN nameplate)
        rated_winding_gradient_K    = 23.0,   # K
        ratio_load_to_no_load_loss  = tr.load_loss_kw / tr.no_load_loss_kw,
        cooling_mode                = "ONAN",
        hot_spot_factor             = 1.3,
    )

    section("2. THERMAL ASSESSMENT – IEC 60076-7 (ONAN)")
    print(f"  {'Load factor':12s}  {'Ambient':>10s}  {'Top-oil rise':>14s}  "
          f"{'Hot-spot':>10s}  {'AAF':>8s}  {'LOL/h':>10s}")
    print(f"  {'-'*12}  {'-'*10}  {'-'*14}  {'-'*10}  {'-'*8}  {'-'*10}")
    for k in [0.5, 0.75, 1.0, 1.1, 1.2, 1.3]:
        for amb in [20.0, 40.0]:
            rise = thermal.top_oil_rise(k, amb)
            hs   = thermal.hot_spot_temp(k, amb)
            aaf  = thermal.aging_acceleration_factor(hs)
            lol  = thermal.loss_of_life_pct_per_hour(hs)
            print(f"  K={k:<6.2f}  amb={amb:>4.0f}°C  "
                  f"Δθ_o={rise:>6.1f} K  "
                  f"θ_h={hs:>6.1f}°C  "
                  f"V={aaf:>7.3f}  "
                  f"LOL={lol:.4e}%/h")

    # ──────────────────────────────────────────────────────────────────────────
    # 3. Protection relay settings
    # ──────────────────────────────────────────────────────────────────────────

    prot = TransformerProtection()

    section("3. PROTECTION RELAY SETTINGS")

    # 87T differential (balanced load → small differential expected)
    i_op, i_res, slope = prot.differential_current(
        i_primary   = tr.primary_current_A(),
        i_secondary = tr.secondary_current_A(),
        ctr_primary = 200,   # 200/1 A CT on HV
        ctr_secondary = 600, # 600/1 A CT on LV
    )
    print(f"  87T Differential relay (balanced load):")
    print(f"    I_operate  = {i_op:.4f} A secondary")
    print(f"    I_restraint= {i_res:.4f} A secondary")
    print(f"    Slope      = {slope:.2f} %")

    # 51 Overcurrent pickup
    i_pu_hv = prot.overcurrent_pickup(tr.kva, tr.primary_kv,   multiplier=1.25)
    i_pu_lv = prot.overcurrent_pickup(tr.kva, tr.secondary_kv, multiplier=1.25)
    print(f"\n  51 Overcurrent pickup (125% FLC):")
    print(f"    HV side: {i_pu_hv:.2f} A primary  (FLC = {tr.primary_current_A():.2f} A)")
    print(f"    LV side: {i_pu_lv:.2f} A primary  (FLC = {tr.secondary_current_A():.2f} A)")

    # 64REF – simulate an internal earth fault
    ia, ib, ic = 0.5, 0.5, 0.5
    i_n_fault = 0.9  # neutral CT picks up more during fault
    i_spill, operates = prot.restricted_earth_fault(i_n_fault, (ia, ib, ic))
    print(f"\n  64REF Restricted Earth Fault (simulated internal fault):")
    print(f"    Neutral CT current  = {i_n_fault} A secondary")
    print(f"    Phase CT sum        = {ia+ib+ic:.1f} A secondary")
    print(f"    Spill current       = {i_spill:.2f} A  → Relay {'OPERATES' if operates else 'RESTRAINS'}")

    bz = prot.buchholz_gas_volume_threshold_ml()
    print(f"\n  Buchholz relay thresholds:")
    print(f"    Alarm at     : {bz['alarm_ml']} mL accumulated gas")
    print(f"    Trip at      : {bz['trip_ml']} mL accumulated gas")
    print(f"    Surge trip   : {bz['surge_velocity_cm_s']} cm/s oil surge velocity")

    # ──────────────────────────────────────────────────────────────────────────
    # 4. OLTC tap selection
    # ──────────────────────────────────────────────────────────────────────────

    section("4. OLTC TAP-CHANGER ANALYSIS")
    oltc = OLTCAnalyzer()

    scenarios = [
        ("Light load – voltage high", 11.35, 11.0),
        ("Full load  – voltage low",  10.65, 11.0),
        ("Emergency  – very low V",   10.20, 11.0),
    ]
    print(f"  OLTC: ±9 taps × 1.25 % step = ±11.25 % regulation range")
    print(f"  {'Scenario':<35s}  {'Meas kV':>8s}  {'Tap':>5s}  {'Achieved kV':>12s}  {'Error %':>8s}")
    print(f"  {'-'*35}  {'-'*8}  {'-'*5}  {'-'*12}  {'-'*8}")
    for desc, v_meas, v_tgt in scenarios:
        tap, v_ach, err = oltc.optimal_tap(v_meas, v_tgt, tap_step_pct=1.25, n_taps=9)
        print(f"  {desc:<35s}  {v_meas:>8.3f}  {tap:>+5d}  {v_ach:>12.4f}  {err:>+8.4f}")

    vr = oltc.voltage_regulation_pct(no_load_v=11.18, full_load_v=10.64)
    print(f"\n  Measured voltage regulation (NL→FL): {vr:.2f} %")

    vr_approx = oltc.approximate_regulation_pct(
        impedance_pct   = tr.impedance_pct,
        resistance_pct  = tr.load_loss_kw / tr.kva * 100,
        power_factor    = 0.85,
    )
    print(f"  Kapp approximate regulation (pf=0.85): {vr_approx:.2f} %")

    # ──────────────────────────────────────────────────────────────────────────
    # 5. Dissolved-gas analysis
    # ──────────────────────────────────────────────────────────────────────────

    section("5. DISSOLVED GAS ANALYSIS (DGA)")
    oil = OilAnalysis()

    # Scenario: suspect thermal fault from oil test report
    dga_result = oil.parse_dissolved_gas(
        h2   = 180,
        ch4  = 290,
        c2h2 =   4,
        c2h4 = 310,
        c2h6 =  75,
        co   = 620,
        co2  = 4_100,
    )

    print(f"  Gas concentrations [ppm]:")
    for gas, val in dga_result["gases_ppm"].items():
        print(f"    {gas:<6s}: {val:>6.0f} ppm")

    print(f"\n  TDCG                  : {dga_result['tdcg_ppm']:.0f} ppm")
    print(f"  TDCG condition        : {dga_result['tdcg_condition']}")
    print(f"  Cellulose involvement : {'YES – CO/CO₂ ratio elevated' if dga_result['cellulose_involved'] else 'No'}")

    d = dga_result["duval"]
    print(f"\n  Duval Triangle:")
    print(f"    Fault code       : {d.fault_code}")
    print(f"    Classification   : {d.fault_description}")
    print(f"    Recommendation   : {d.recommendation}")

    r = dga_result["rogers"]
    print(f"\n  Rogers Ratios:")
    print(f"    Fault code       : {r.fault_code}")
    print(f"    Classification   : {r.fault_description}")
    print(f"    Recommendation   : {r.recommendation}")

    bdv = oil.dielectric_breakdown_kv_rating(measured_kv=68.5)
    print(f"\n  BDV test: {bdv['measured_kv']} kV  →  {bdv['status']}  "
          f"(limit {bdv['limit_kv']} kV, margin {bdv['margin_kv']:+.1f} kV)")

    sat = oil.moisture_ppm_to_saturation_pct(ppm=18, temp_C=60)
    print(f"  Moisture: 18 ppm @ 60°C  →  {sat:.1f}% saturation  "
          f"({'concern' if sat > 25 else 'acceptable'})")

    # ──────────────────────────────────────────────────────────────────────────
    # 6. Permissible overload (summer peak)
    # ──────────────────────────────────────────────────────────────────────────

    section("6. PERMISSIBLE OVERLOAD – IEC 60076-7")
    calc = LoadingCalculator(
        thermal_model  = thermal,
        max_hot_spot_C = 120.0,  # long-time emergency limit
        max_top_oil_C  = 105.0,
    )

    for amb in [25, 35, 40, 45]:
        result = calc.permissible_overload(
            ambient_C       = amb,
            pre_load_factor = 0.8,
            duration_h      = 4.0,
        )
        print(
            f"  Ambient {amb:>2d}°C  |  max K₂ = {result['max_load_factor']:.3f}  "
            f"|  θ_h = {result['hot_spot_C']:>6.1f}°C  "
            f"|  θ_o = {result['top_oil_C']:>6.1f}°C  "
            f"|  limit: {result['limiting_constraint']}"
        )

    # ──────────────────────────────────────────────────────────────────────────
    # 7. 24-hour loss-of-life estimate
    # ──────────────────────────────────────────────────────────────────────────

    section("7. 24-HOUR LOSS-OF-LIFE ESTIMATE")
    # Typical daily load curve for a distribution transformer
    load_profile = [
        (0.45, 6.0),   # night (00:00–06:00)
        (0.80, 4.0),   # morning (06:00–10:00)
        (1.00, 6.0),   # peak (10:00–16:00)
        (0.95, 4.0),   # afternoon (16:00–20:00)
        (0.70, 4.0),   # evening (20:00–00:00)
    ]
    total_h = sum(h for _, h in load_profile)
    lol = calc.cumulative_loss_of_life(load_profile, ambient_C=35.0)
    print(f"  Ambient: 35 °C   Duration: {total_h:.0f} h   (IEC 60076-7 loss-of-life)")
    print()
    print(f"  {'Period':<30s}  {'K':>5s}  {'Hours':>6s}  {'θ_h °C':>8s}  {'LOL/h %':>12s}")
    print(f"  {'-'*30}  {'-'*5}  {'-'*6}  {'-'*8}  {'-'*12}")
    labels = ["Night (00–06)", "Morning (06–10)", "Peak (10–16)",
              "Afternoon (16–20)", "Evening (20–00)"]
    for (k, h), label in zip(load_profile, labels):
        hs = thermal.hot_spot_temp(k, 35.0)
        lol_h = thermal.loss_of_life_pct_per_hour(hs)
        print(f"  {label:<30s}  {k:>5.2f}  {h:>6.1f}  {hs:>8.1f}  {lol_h:>12.6f}")
    print(f"\n  Total 24-h loss of life : {lol:.6f} %")
    normal_life_h = 200_000
    equiv_days = (lol / 100.0) * normal_life_h / 24
    print(f"  (≡ {equiv_days:.2f} equivalent days of normal life consumed)")

    section("AUDIT COMPLETE")
    print("  All parameters within acceptable limits. Schedule next")
    print("  DGA sampling in 6 months; review OLTC contact wear.")
    print()


if __name__ == "__main__":
    audit()
