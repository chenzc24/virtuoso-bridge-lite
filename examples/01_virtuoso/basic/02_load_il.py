#!/usr/bin/env python3
"""Load a SKILL .il file into Virtuoso CIW.

Prerequisites:
- virtuoso-bridge service running (virtuoso-bridge start)
- RAMIC daemon loaded in Virtuoso CIW
"""

import sys, pathlib; sys.path.insert(0, str(pathlib.Path(__file__).parent.parent.parent))
from pathlib import Path
from _timing import print_elapsed
from virtuoso_bridge import BridgeClient

SONNET_IL = Path(__file__).resolve().parent.parent / "assets" / "sonnet18.il"

client = BridgeClient()
response = client.load_il(SONNET_IL)
print_elapsed("load_il", response.get("_elapsed", 0.0))
meta = response.get("result", {}).get("metadata", {})
upload_tag = "uploaded" if meta.get("uploaded") else "cache hit"
print(f"[{upload_tag}]")
print(f"[OK] local:  {SONNET_IL}")
print(f"[OK] remote: {meta.get('skill_command')}")
