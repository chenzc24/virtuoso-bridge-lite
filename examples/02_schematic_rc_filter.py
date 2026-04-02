#!/usr/bin/env python3
"""Create a testbench schematic using only analogLib (no PDK needed).

Demonstrates schematic editing: adding instances, wires, pins, and labels.
Uses only analogLib components (vdc, res, cap, gnd) which exist in every
Virtuoso installation.

Prerequisites:
  - .env configured, bridge running
  - A library exists in Virtuoso (default: PLAYGROUND_LLM)

Usage:
    python examples/02_schematic_rc_filter.py
    python examples/02_schematic_rc_filter.py --lib MY_LIB --cell RC_DEMO
"""

from __future__ import annotations

import argparse
import sys

from virtuoso_bridge import BridgeClient


def build_rc_filter(client: BridgeClient, lib: str, cell: str) -> None:
    """Create an RC low-pass filter schematic using only analogLib."""

    with client.schematic.edit(lib, cell) as sch:
        # Voltage source
        sch.add_instance("analogLib", "vdc", (-1.0, 0), "V0",
                         params={"vdc": "1.0"})

        # Resistor
        sch.add_instance("analogLib", "res", (0, 0), "R0",
                         params={"r": "1k"})

        # Capacitor
        sch.add_instance("analogLib", "cap", (1.0, 0), "C0",
                         params={"c": "1p"})

        # Ground
        sch.add_instance("analogLib", "gnd", (0, -1.0), "GND0")

        # Wires
        sch.add_wire([(-1.0, 0.5), (0, 0.5)])    # V0 → R0
        sch.add_wire([(0, -0.5), (0, -1.0)])      # node → GND
        sch.add_wire([(0.5, 0), (1.0, 0.5)])      # R0 out → C0
        sch.add_wire([(1.0, -0.5), (0, -0.5)])    # C0 → GND

        # Pins
        sch.add_pin("IN", "input", (-1.5, 0.5))
        sch.add_pin("OUT", "output", (1.5, 0.5))

        # Wire pins
        sch.add_wire([(-1.5, 0.5), (-1.0, 0.5)])
        sch.add_wire([(1.0, 0.5), (1.5, 0.5)])

    print(f"Created RC filter schematic: {lib}/{cell}/schematic")


def main() -> int:
    parser = argparse.ArgumentParser(description="Create RC filter schematic (analogLib only)")
    parser.add_argument("--lib", default="PLAYGROUND_LLM", help="Library name")
    parser.add_argument("--cell", default="RC_FILTER_DEMO", help="Cell name")
    args = parser.parse_args()

    client = BridgeClient()
    if not client.test_connection().get("alive"):
        print("Bridge not running. Run: virtuoso-bridge start")
        return 1

    build_rc_filter(client, args.lib, args.cell)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
