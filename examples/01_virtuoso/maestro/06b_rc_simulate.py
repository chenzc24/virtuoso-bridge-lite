#!/usr/bin/env python3
"""Step 2: Run simulation on the RC filter Maestro setup.

Prerequisite: run 06a_rc_create.py first.
After this completes, use 06c_rc_read_results.py to read results.

NOTE: Must open Maestro in GUI mode (deOpenCellView + maeMakeEditable)
for maeWaitUntilDone to work. Background sessions (maeOpenSetup) return
immediately from maeWaitUntilDone, causing the simulation to be canceled
when the session closes.
"""

import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent / "src"))

from virtuoso_bridge import VirtuosoClient
from virtuoso_bridge.virtuoso.maestro import save_setup

LIB = "PLAYGROUND_LLM"
CELL = "TB_RC_FILTER"


def main() -> int:
    client = VirtuosoClient.from_env()
    print(f"[info] {LIB}/{CELL}")

    # Must use GUI mode for maeWaitUntilDone to block properly
    client.execute_skill(
        f'deOpenCellView("{LIB}" "{CELL}" "maestro" "maestro" nil "r")')
    client.execute_skill('maeMakeEditable()')

    print("[sim] Running...")
    t0 = time.time()
    r = client.execute_skill('maeRunSimulation()')
    run_name = (r.output or "").strip('"')
    print(f"[sim] Started: {run_name}")

    client.execute_skill("maeWaitUntilDone('All)", timeout=600)
    print(f"[sim] Done ({time.time() - t0:.1f}s)")

    # Save so results persist after closing
    save_setup(client, LIB, CELL)

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
