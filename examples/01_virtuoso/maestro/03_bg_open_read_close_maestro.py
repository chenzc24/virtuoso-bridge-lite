#!/usr/bin/env python3
"""Open a maestro in background, read config, then close it.

Edit LIB and CELL below.
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent / "src"))

from virtuoso_bridge import VirtuosoClient
from virtuoso_bridge.virtuoso.maestro import open_session, close_session, read_config

if len(sys.argv) < 2:
    print(f"Usage: python {Path(__file__).name} <LIB>")
    raise SystemExit(1)
LIB  = sys.argv[1]
CELL = "TB_AMP_5T_D2S_DC_AC"


def main() -> int:
    client = VirtuosoClient.from_env()

    session = open_session(client, LIB, CELL)

    for key, (skill_expr, raw) in read_config(client, session).items():
        print(f"[{key}] {skill_expr}")
        print(raw)

    close_session(client, session)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
