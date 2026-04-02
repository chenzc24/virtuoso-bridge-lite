#!/usr/bin/env python3
"""Create a new schematic cellview, run schCheck, and save it."""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from _timing import format_elapsed
from virtuoso_bridge import BridgeClient
from virtuoso_bridge.virtuoso.basic.composition import compose_skill_script
from virtuoso_bridge.virtuoso.ops import open_cell_view, open_window, save_current_cellview
from virtuoso_bridge.virtuoso.schematic.ops import (
    schematic_check,
    schematic_create_pin,
    schematic_create_wire_label,
)


def _build_script(lib: str, cell: str) -> str:
    commands = [
        open_cell_view(lib, cell, view="schematic", mode="a"),
        open_window(lib, cell, view="schematic", mode="a"),
        schematic_create_pin("IN", -1.0, 0.0, "R0", direction="input"),
        schematic_create_pin("OUT", 1.0, 0.0, "R180", direction="output"),
        schematic_create_wire_label(0.0, 0.2, "NET0", "lowerLeft", "R0"),
        schematic_check(),
        save_current_cellview(),
        'sprintf(nil "created=%s checked_and_saved=t" cv~>cellName)',
    ]
    return compose_skill_script(commands)


def main() -> int:
    scratch_cell = "bridge_new_schematic"
    client = BridgeClient()
    lib, _, _ = client.get_current_design()
    if not lib:
        print("No active design in Virtuoso. Open a schematic first.")
        return 1

    response = client.execute_skill(_build_script(lib, scratch_cell), timeout=30)
    print(f"[mode] bridge service  [{format_elapsed(response.get('_elapsed', 0.0))}]")
    print(f"Active library: {lib}  ->  new schematic cell: {scratch_cell}")
    print(response.get("result", {}).get("output") or "<empty>")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
