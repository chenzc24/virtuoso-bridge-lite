#!/usr/bin/env python3
"""Run DC + AC simulation on a capacitor and extract capacitance value.

Capacitance is extracted from AC current at 100 MHz:
    C = d|I(C0/PLUS)| / dfreq / (2 * pi)

Usage::

    python examples/02_spectre/02_cap_dc_ac.py
"""

from __future__ import annotations

import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from _result_io import print_result_counts, print_timing_summary, save_summary_json

ROOT = Path(__file__).resolve().parent
NETLIST = ROOT / "assets" / "cap_dc_ac" / "tb_cap_dc_ac.scs"
OUT_DIR = ROOT / "output" / "cap_dc_ac"


def main() -> int:
    try:
        from dotenv import load_dotenv
        load_dotenv()
    except ImportError:
        pass

    from virtuoso_bridge.spectre.runner import SpectreSimulator, spectre_mode_args

    OUT_DIR.mkdir(parents=True, exist_ok=True)

    sim = SpectreSimulator.from_env(
        spectre_cmd=os.getenv("SPECTRE_CMD", "spectre"),
        spectre_args=spectre_mode_args("ax"),
        work_dir=OUT_DIR,
        output_format="psfascii",
    )

    print("[Run] Capacitor DC + AC simulation ...")
    result = sim.run_simulation(NETLIST, {})

    print(f"Status : {result.status.value}")
    print_result_counts(result)
    if result.errors:
        print("Errors :")
        for e in result.errors[:5]:
            print(f"  {e}")
    if not result.ok:
        return 1

    # DC operating point
    dc_vdd = result.data.get("dc_VDD")
    if dc_vdd is not None:
        print(f"\nDC operating point:")
        print(f"  VDD = {dc_vdd:.4f} V")

    # Capacitance from AC current: C = d|I(C0)| / df / (2*pi)
    import math
    freq = result.data.get("ac_freq", [])
    i_cap = result.data.get("ac_C0:1", [])

    if freq and i_cap and len(freq) > 1:
        # Find index closest to 100 MHz
        target_f = 1e8
        idx = min(range(len(freq)), key=lambda i: abs(freq[i] - target_f))

        if idx > 0:
            df = freq[idx] - freq[idx - 1]
            di = abs(i_cap[idx]) - abs(i_cap[idx - 1])
            cap_val = di / df / (2 * math.pi)
            print(f"\nCapacitance from AC (at {freq[idx]:.2e} Hz):")
            print(f"  C = {cap_val:.4e} F  ({cap_val * 1e15:.2f} fF)")
            print(f"  Expected: 50.00 fF")

        # Also show formula at a few frequencies
        print(f"\nAC sweep: {freq[0]:.2e} – {freq[-1]:.2e} Hz ({len(freq)} points)")
        print(f"  |I(C0)| at f={freq[0]:.2e}: {i_cap[0]:.6e} A")
        print(f"  |I(C0)| at f={freq[-1]:.2e}: {i_cap[-1]:.6e} A")
    else:
        print(f"\nAC data not available for capacitance extraction")

    save_summary_json(result, OUT_DIR / "cap_dc_ac_result.json")
    print(f"\nSummary saved to: {OUT_DIR / 'cap_dc_ac_result.json'}")
    print_timing_summary(result)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
