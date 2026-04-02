#!/usr/bin/env python3
"""Create a layout with basic shapes (no PDK needed).

Demonstrates layout editing: rectangles, paths, labels, and vias using
only generic layers (M1, M2, VIA1). Works with any tech file.

Prerequisites:
  - .env configured, bridge running
  - A library exists in Virtuoso (default: PLAYGROUND_LLM)

Usage:
    python examples/03_layout_shapes.py
    python examples/03_layout_shapes.py --lib MY_LIB --cell SHAPES_DEMO
"""

from __future__ import annotations

import argparse

from virtuoso_bridge import BridgeClient


def build_shapes(client: BridgeClient, lib: str, cell: str) -> None:
    """Draw basic shapes on M1/M2 layers."""

    with client.layout.edit(lib, cell) as layout:
        # M1 rectangles
        layout.add_rect("M1", "drawing", (0, 0, 2.0, 0.5))
        layout.add_rect("M1", "drawing", (0, 1.0, 2.0, 1.5))

        # M2 vertical path connecting the two M1 bars
        layout.add_path("M2", "drawing", [(1.0, 0.25), (1.0, 1.25)], width=0.1)

        # Labels
        layout.add_label("M1", "drawing", (1.0, 0.25), "NET_A")
        layout.add_label("M1", "drawing", (1.0, 1.25), "NET_B")

        # Read back what we created
        shapes = layout.get_shapes()
        print(f"Shapes created: {len(shapes) if isinstance(shapes, list) else shapes}")

    print(f"Created layout: {lib}/{cell}/layout")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--lib", default="PLAYGROUND_LLM")
    parser.add_argument("--cell", default="SHAPES_DEMO")
    args = parser.parse_args()

    client = BridgeClient()
    if not client.test_connection().get("alive"):
        print("Bridge not running. Run: virtuoso-bridge start")
        return 1

    build_shapes(client, args.lib, args.cell)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
