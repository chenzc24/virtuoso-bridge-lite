#!/usr/bin/env python3
"""Close the current layout cellview and delete the entire cell."""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from _timing import decode_skill, format_elapsed, timed_call
from virtuoso_bridge import BridgeClient


def main() -> int:
    client = BridgeClient()

    elapsed, design = timed_call(client.get_current_design)
    print(f"[get_current_design] [{format_elapsed(elapsed)}]")
    lib, cell, view = design
    if not lib or view != "layout":
        print("No active layout window.")
        return 1

    close_elapsed, close_resp = timed_call(lambda: client.close_current_cellview(timeout=15))
    if close_resp.get("ok", False):
        print(f"[close_current_cellview] [{format_elapsed(close_elapsed)}]")
        close_result = close_resp.get("result", {})
        if close_result.get("status") != "success":
            errors = close_result.get("errors") or ["close failed"]
            print(f"[close_current_cellview] {errors[0]}")
    else:
        print(f"[close_current_cellview] failed: {close_resp.get('error', 'request failed')}")

    delete_elapsed, response = timed_call(lambda: client.layout.delete_cell(lib, cell, timeout=30))
    print(f"[layout.delete_cell] [{format_elapsed(delete_elapsed)}]")
    print(decode_skill(response.get("result", {}).get("output", "")))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
