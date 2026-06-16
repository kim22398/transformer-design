"""
main.py
-------
Command-line entry point for the Transformer Design, Testing & Monitoring
Toolkit.

Run the flagship audit demo, the pytest suite, or call individual library
calculations directly from the shell::

    python main.py                 # run the full 10 MVA audit demo
    python main.py --help          # list all subcommands
    python main.py audit           # same as the bare demo
    python main.py test            # run the pytest suite
    python main.py dga --h2 180 --ch4 290 --c2h2 4 --c2h4 310 --c2h6 75
    python main.py thermal --load 1.1 --ambient 40

All subcommands are built on the :mod:`transformer` package and the standards
it implements (IEC 60076-7, IEC 60599, IEEE C57.104).
"""

from __future__ import annotations

# Make the ``transformer`` package importable when run as ``python main.py``
# from any directory, without needing PYTHONPATH set externally.
import os
import sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import argparse
import subprocess

from transformer.oil_analysis import OilAnalysis
from transformer.thermal import ThermalModel


# ──────────────────────────────────────────────────────────────────────────────
# Small formatting helpers
# ──────────────────────────────────────────────────────────────────────────────

def _section(title: str) -> None:
    """Print a boxed section header, matching the audit demo style."""
    width = 68
    print("\n" + "=" * width)
    print(f"  {title}")
    print("=" * width)


# ──────────────────────────────────────────────────────────────────────────────
# Subcommand: audit (flagship demo)
# ──────────────────────────────────────────────────────────────────────────────

def cmd_audit(args: argparse.Namespace) -> int:
    """Run the full transformer health-check audit (the flagship demo)."""
    from examples.transformer_audit import audit
    audit()
    return 0


# ──────────────────────────────────────────────────────────────────────────────
# Subcommand: test
# ──────────────────────────────────────────────────────────────────────────────

def cmd_test(args: argparse.Namespace) -> int:
    """Run the pytest suite via ``python -m pytest tests/ -q``."""
    repo_root = os.path.dirname(os.path.abspath(__file__))
    env = dict(os.environ)
    # Ensure the package resolves for the spawned pytest process too.
    env["PYTHONPATH"] = repo_root + os.pathsep + env.get("PYTHONPATH", "")
    completed = subprocess.run(
        [sys.executable, "-m", "pytest", "tests/", "-q"],
        cwd=repo_root,
        env=env,
    )
    return completed.returncode


# ──────────────────────────────────────────────────────────────────────────────
# Subcommand: dga (dissolved-gas analysis)
# ──────────────────────────────────────────────────────────────────────────────

def cmd_dga(args: argparse.Namespace) -> int:
    """Diagnose a dissolved-gas sample via Duval Triangle + Rogers Ratios."""
    oil = OilAnalysis()
    result = oil.parse_dissolved_gas(
        h2   = args.h2,
        ch4  = args.ch4,
        c2h2 = args.c2h2,
        c2h4 = args.c2h4,
        c2h6 = args.c2h6,
        co   = args.co,
        co2  = args.co2,
    )

    _section("DISSOLVED GAS ANALYSIS (DGA)")
    print("  Gas concentrations [ppm]:")
    for gas, val in result["gases_ppm"].items():
        print(f"    {gas:<6s}: {val:>8.1f} ppm")

    print(f"\n  TDCG                  : {result['tdcg_ppm']:.0f} ppm")
    print(f"  TDCG condition        : {result['tdcg_condition']}")
    print(f"  Cellulose involvement : "
          f"{'YES (CO/CO2 ratio elevated)' if result['cellulose_involved'] else 'No'}")

    d = result["duval"]
    print("\n  Duval Triangle:")
    print(f"    Fault code       : {d.fault_code}")
    print(f"    Classification   : {d.fault_description}")
    print(f"    Recommendation   : {d.recommendation}")

    r = result["rogers"]
    print("\n  Rogers Ratios:")
    print(f"    Fault code       : {r.fault_code}")
    print(f"    Classification   : {r.fault_description}")
    print(f"    Recommendation   : {r.recommendation}")
    print()
    return 0


# ──────────────────────────────────────────────────────────────────────────────
# Subcommand: thermal (hot-spot + loss-of-life)
# ──────────────────────────────────────────────────────────────────────────────

def cmd_thermal(args: argparse.Namespace) -> int:
    """Compute steady-state hot-spot temperature and loss-of-life rate."""
    tm = ThermalModel(
        rated_top_oil_rise_K       = args.top_oil_rise,
        rated_winding_gradient_K   = args.winding_gradient,
        ratio_load_to_no_load_loss = args.loss_ratio,
        cooling_mode               = args.cooling,
        hot_spot_factor            = args.hot_spot_factor,
    )

    K = args.load
    amb = args.ambient
    top_oil_rise = tm.top_oil_rise(K, amb)
    top_oil_C = amb + top_oil_rise
    hot_spot_C = tm.hot_spot_temp(K, amb)
    aaf = tm.aging_acceleration_factor(hot_spot_C)
    lol_per_h = tm.loss_of_life_pct_per_hour(hot_spot_C)
    lol_window = lol_per_h * args.hours

    _section(f"THERMAL ASSESSMENT - IEC 60076-7 ({args.cooling})")
    print(f"  Load factor (K)       : {K:>10.3f} pu")
    print(f"  Ambient temperature   : {amb:>10.1f} C")
    print(f"  Cooling mode          : {args.cooling:>10s}  "
          f"(x={tm.x}, y={tm.y})")
    print()
    print(f"  Top-oil rise          : {top_oil_rise:>10.2f} K")
    print(f"  Top-oil temperature   : {top_oil_C:>10.2f} C")
    print(f"  Hot-spot temperature  : {hot_spot_C:>10.2f} C")
    print()
    print(f"  Ageing accel. factor V: {aaf:>10.4f}  "
          f"({'accelerated' if aaf > 1.0 else 'retarded'} ageing)")
    print(f"  Loss of life          : {lol_per_h:>10.6f} %/h")
    print(f"  Loss of life ({args.hours:g} h)   : {lol_window:>10.6f} %")
    print()
    return 0


# ──────────────────────────────────────────────────────────────────────────────
# Argument parser
# ──────────────────────────────────────────────────────────────────────────────

def build_parser() -> argparse.ArgumentParser:
    """Construct the top-level argument parser with all subcommands."""
    parser = argparse.ArgumentParser(
        prog="main.py",
        description=(
            "Transformer Design, Testing & Monitoring Toolkit "
            "(IEC 60076-7 / IEC 60599 / IEEE C57.104). "
            "Run with no subcommand to launch the full audit demo."
        ),
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    subparsers = parser.add_subparsers(dest="command", metavar="<command>")

    # audit -----------------------------------------------------------------
    p_audit = subparsers.add_parser(
        "audit",
        help="run the full 10 MVA transformer health-check audit (the demo)",
    )
    p_audit.set_defaults(func=cmd_audit)

    # test ------------------------------------------------------------------
    p_test = subparsers.add_parser(
        "test",
        help="run the pytest suite (python -m pytest tests/ -q)",
    )
    p_test.set_defaults(func=cmd_test)

    # dga -------------------------------------------------------------------
    p_dga = subparsers.add_parser(
        "dga",
        help="diagnose a dissolved-gas sample (Duval Triangle + Rogers Ratios)",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    p_dga.add_argument("--h2",   type=float, default=180.0, help="Hydrogen [ppm]")
    p_dga.add_argument("--ch4",  type=float, default=290.0, help="Methane [ppm]")
    p_dga.add_argument("--c2h2", type=float, default=4.0,   help="Acetylene [ppm]")
    p_dga.add_argument("--c2h4", type=float, default=310.0, help="Ethylene [ppm]")
    p_dga.add_argument("--c2h6", type=float, default=75.0,  help="Ethane [ppm]")
    p_dga.add_argument("--co",   type=float, default=620.0, help="Carbon monoxide [ppm]")
    p_dga.add_argument("--co2",  type=float, default=4100.0, help="Carbon dioxide [ppm]")
    p_dga.set_defaults(func=cmd_dga)

    # thermal ---------------------------------------------------------------
    p_thermal = subparsers.add_parser(
        "thermal",
        help="compute hot-spot temperature and loss-of-life (IEC 60076-7)",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    p_thermal.add_argument("--load", type=float, default=1.0,
                           help="load factor K (per-unit, 1.0 = rated)")
    p_thermal.add_argument("--ambient", type=float, default=20.0,
                           help="ambient temperature [C]")
    p_thermal.add_argument("--hours", type=float, default=1.0,
                           help="duration over which to integrate loss-of-life [h]")
    p_thermal.add_argument("--cooling", default="ONAN",
                           choices=["ONAN", "ONAF", "OFAF", "ODAF"],
                           help="cooling mode (sets thermal exponents)")
    p_thermal.add_argument("--top-oil-rise", type=float, default=55.0,
                           dest="top_oil_rise",
                           help="rated top-oil rise above ambient [K]")
    p_thermal.add_argument("--winding-gradient", type=float, default=23.0,
                           dest="winding_gradient",
                           help="rated hot-spot-to-top-oil gradient [K]")
    p_thermal.add_argument("--loss-ratio", type=float, default=6.07,
                           dest="loss_ratio",
                           help="ratio of load losses to no-load losses (R)")
    p_thermal.add_argument("--hot-spot-factor", type=float, default=1.3,
                           dest="hot_spot_factor",
                           help="hot-spot factor H")
    p_thermal.set_defaults(func=cmd_thermal)

    return parser


# ──────────────────────────────────────────────────────────────────────────────
# Entry point
# ──────────────────────────────────────────────────────────────────────────────

def main(argv: list[str] | None = None) -> int:
    """Parse arguments and dispatch to the selected subcommand.

    With no subcommand, run the flagship transformer audit demo.
    """
    parser = build_parser()
    args = parser.parse_args(argv)

    if args.command is None:
        # No subcommand: run the flagship demo.
        return cmd_audit(args)

    return args.func(args)


if __name__ == "__main__":
    raise SystemExit(main())
