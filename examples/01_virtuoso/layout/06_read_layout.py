#!/usr/bin/env python3
"""Read detailed geometry from the current layout cell."""

from __future__ import annotations

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from _timing import decode_skill, format_elapsed, timed_call
from virtuoso_bridge import BridgeClient


def _format_value(value: object) -> str:
    return json.dumps(value, ensure_ascii=False)


def _print_object(obj: dict[str, object]) -> None:
    print("{")
    items = list(obj.items())
    for index, (key, value) in enumerate(items):
        suffix = "," if index < len(items) - 1 else ""
        print(f'  "{key}": {_format_value(value)}{suffix}')
    print("}")


def main() -> int:
    client = BridgeClient()

    elapsed, design = timed_call(client.get_current_design)
    print(f"[get_current_design] [{format_elapsed(elapsed)}]")
    lib, cell, _ = design
    if not lib:
        print("Open a layout in Virtuoso first.")
        return 1

    read_elapsed, response = timed_call(lambda: client.layout.read_geometry(lib, cell, timeout=30))
    print(f"[layout.read_geometry] [{format_elapsed(read_elapsed)}]")
    print()

    output = decode_skill(response.get("result", {}).get("output", ""))
    if output.startswith("ERROR"):
        print(output)
        return 1

    geometry = response.get("geometry") or []
    print(json.dumps({"lib": lib, "cell": cell, "view": "layout"}, ensure_ascii=False))
    for obj in geometry:
        _print_object(obj)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
