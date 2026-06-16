"""
examples/loading_profile_plot.py
--------------------------------
24-hour loading-profile thermal simulation (IEC 60076-7).

Computes the steady-state hot-spot and top-oil temperatures for a typical
daily load cycle on a 10 MVA ONAN distribution transformer, integrates the
loss of life over the 24 h cycle, and saves a publication-quality figure
to ``examples/output/loading_profile_24h.png``.

The figure shows, on a shared 24 h time axis:
  * the per-unit load factor profile (right axis), and
  * the resulting hot-spot and top-oil temperatures (left axis),
with the IEC 60076-7 Table 1 hot-spot limits (98 °C normal ageing,
120 °C long-time emergency) drawn as reference lines.

Run with::

    PYTHONPATH=. python examples/loading_profile_plot.py
"""

from __future__ import annotations

import os

import matplotlib

matplotlib.use("Agg")  # headless / no-display backend
import matplotlib.pyplot as plt

from transformer.thermal import ThermalModel
from transformer.loading import LoadingCalculator


# ---------------------------------------------------------------------------
# Daily load cycle: (start_hour, load_factor) sampled hourly.
# A typical utility distribution profile: low overnight, morning ramp,
# midday peak (slight overload), evening shoulder.
# ---------------------------------------------------------------------------
HOURLY_LOAD = [
    0.45, 0.42, 0.40, 0.40, 0.45, 0.55,   # 00–06 night
    0.70, 0.80, 0.85, 0.88, 0.95, 1.00,   # 06–12 morning ramp
    1.05, 1.05, 1.00, 0.98, 0.95, 0.92,   # 12–18 midday peak
    0.88, 0.80, 0.72, 0.65, 0.55, 0.48,   # 18–24 evening
]
AMBIENT_C = 35.0


def main() -> str:
    tm = ThermalModel(
        rated_top_oil_rise_K=55.0,
        rated_winding_gradient_K=23.0,
        ratio_load_to_no_load_loss=6.07,
        cooling_mode="ONAN",
        hot_spot_factor=1.3,
    )
    calc = LoadingCalculator(tm)

    hours = list(range(24))
    hot_spot = [tm.hot_spot_temp(k, AMBIENT_C) for k in HOURLY_LOAD]
    top_oil = [AMBIENT_C + tm.top_oil_rise(k, AMBIENT_C) for k in HOURLY_LOAD]

    # Cumulative loss of life over the 24 h cycle (1 h per step).
    profile = [(k, 1.0) for k in HOURLY_LOAD]
    total_lol_pct = calc.cumulative_loss_of_life(profile, AMBIENT_C)
    peak_hs = max(hot_spot)
    peak_hour = hours[hot_spot.index(peak_hs)]

    print("24-hour loading-profile thermal simulation (IEC 60076-7)")
    print(f"  Ambient                : {AMBIENT_C:.0f} °C")
    print(f"  Peak load factor       : {max(HOURLY_LOAD):.2f} pu")
    print(f"  Peak hot-spot          : {peak_hs:.1f} °C at hour {peak_hour:02d}:00")
    print(f"  Peak top-oil           : {max(top_oil):.1f} °C")
    print(f"  24-h loss of life      : {total_lol_pct:.6f} %")
    print(f"  (= {total_lol_pct / 100 * 200_000 / 24:.2f} equivalent days of normal life)")

    # ---- Plot ----------------------------------------------------------
    fig, ax1 = plt.subplots(figsize=(11, 6))

    ax1.plot(hours, hot_spot, "o-", color="#c0392b", lw=2, label="Hot-spot θ_h")
    ax1.plot(hours, top_oil, "s-", color="#e67e22", lw=2, label="Top-oil θ_o")
    ax1.axhline(98, color="#7f8c8d", ls="--", lw=1.2,
                label="98 °C — normal-ageing limit")
    ax1.axhline(120, color="#34495e", ls=":", lw=1.2,
                label="120 °C — long-time emergency limit")
    ax1.set_xlabel("Hour of day")
    ax1.set_ylabel("Temperature [°C]")
    ax1.set_xlim(0, 23)
    ax1.set_xticks(range(0, 24, 2))
    ax1.set_ylim(40, 130)
    ax1.grid(True, alpha=0.3)

    ax2 = ax1.twinx()
    ax2.fill_between(hours, HOURLY_LOAD, step="mid", alpha=0.12, color="#2980b9")
    ax2.plot(hours, HOURLY_LOAD, drawstyle="steps-mid", color="#2980b9",
             lw=1.5, alpha=0.8, label="Load factor K")
    ax2.set_ylabel("Load factor K [pu]", color="#2980b9")
    ax2.tick_params(axis="y", labelcolor="#2980b9")
    ax2.set_ylim(0, 1.6)

    lines1, labels1 = ax1.get_legend_handles_labels()
    lines2, labels2 = ax2.get_legend_handles_labels()
    ax1.legend(lines1 + lines2, labels1 + labels2, loc="upper left", fontsize=9)

    fig.suptitle(
        "10 MVA ONAN Transformer — 24 h Loading Profile Thermal Simulation\n"
        f"Ambient {AMBIENT_C:.0f} °C   |   24-h loss of life {total_lol_pct:.4f} %"
        f"   |   peak θ_h {peak_hs:.1f} °C",
        fontsize=12,
    )
    fig.tight_layout()

    out_dir = os.path.join(os.path.dirname(__file__), "output")
    os.makedirs(out_dir, exist_ok=True)
    out_path = os.path.join(out_dir, "loading_profile_24h.png")
    fig.savefig(out_path, dpi=130)
    plt.close(fig)
    print(f"\n  Figure saved: {out_path}")
    return out_path


if __name__ == "__main__":
    main()
