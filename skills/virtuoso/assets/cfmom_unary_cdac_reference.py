#!/usr/bin/env python3
"""Reference builder for a 4-bit unary CFMOM CDAC in vertical style.

This script captures the working pattern discovered during live debugging:
- `tsmcN28/cfmom_2t` must be resized through `Lfinger` and `Nfinger`
- the unit is placed as `R90`
- the `TOP` rail must overlap the transformed left plate stripe
- each `CODE` breakout must start from the transformed right plate stripe
- labels should stay on metal
"""

from __future__ import annotations

from datetime import datetime
from pathlib import Path

from virtuoso_bridge import BridgeClient
from virtuoso_bridge.virtuoso.ops import escape_skill_string

LIB_NAME = "PLAYGROUND_LLM"
MASTER_LIB = "tsmcN28"
MASTER_CELL = "cfmom_2t"
CELL_NAME = f"CFMOM_UNARY4_VERT_L2U_N12_{datetime.now().strftime('%Y%m%d_%H%M%S')}"

UNIT_COUNT = 16
INSTANCE_X = 5.26
INSTANCE_Y0 = -0.585
ROW_PITCH = 1.52
ORIENTATION = "R90"

# Measured from the tested `R90` unit after applying `Lfinger=2u`, `Nfinger=12`.
TOP_RAIL_X = 2.895
TOP_RAIL_W = 0.11
BOTTOM_CONTACT_X = 5.205
BOTTOM_CONTACT_DY = 0.58
BOTTOM_W = 0.11
TRUNK_X0 = 6.72
TRUNK_DX = 0.23
TRUNK_BOTTOM_Y = -1.00
LABEL_Y = -0.55
LABEL_HEIGHT = 0.10

OUTPUT_DIR = Path("examples/01_virtuoso/layout/output")
SCREENSHOT_IL = Path("examples/01_virtuoso/assets/screenshot.il").resolve()


def build_cdac_skill() -> str:
    body: list[str] = [
        f'cv = dbOpenCellViewByType("{LIB_NAME}" "{CELL_NAME}" "layout" "maskLayout" "w")'
    ]

    for idx in range(UNIT_COUNT):
        y = INSTANCE_Y0 + idx * ROW_PITCH
        body.extend(
            [
                (
                    f'inst{idx} = dbCreateParamInstByMasterName('
                    f'cv "{MASTER_LIB}" "{MASTER_CELL}" "layout" '
                    f'"C{idx}" list({INSTANCE_X:g} {y:g}) "{ORIENTATION}")'
                ),
                f'dbReplaceProp(inst{idx} "Lfinger" "string" "2u")',
                f'dbReplaceProp(inst{idx} "Nfinger" "string" "12")',
            ]
        )

    top_y0 = INSTANCE_Y0
    top_y1 = INSTANCE_Y0 + (UNIT_COUNT - 1) * ROW_PITCH + 1.16
    top_label_y = INSTANCE_Y0 + 0.5 * ((UNIT_COUNT - 1) * ROW_PITCH + 1.16)
    body.extend(
        [
            (
                'dbCreatePath(cv list("M3" "drawing") '
                f'list(list({TOP_RAIL_X:g} {top_y0:g}) list({TOP_RAIL_X:g} {top_y1:g})) '
                f"{TOP_RAIL_W:g})"
            ),
            (
                'dbCreateLabel(cv list("M3" "pin") '
                f'list({TOP_RAIL_X:g} {top_label_y:g}) '
                f'"TOP" "centerCenter" "R90" "roman" {LABEL_HEIGHT:g})'
            ),
        ]
    )

    for idx in range(UNIT_COUNT):
        y = INSTANCE_Y0 + idx * ROW_PITCH + BOTTOM_CONTACT_DY
        trunk_x = TRUNK_X0 + idx * TRUNK_DX
        body.extend(
            [
                (
                    'dbCreatePath(cv list("M3" "drawing") '
                    f'list(list({BOTTOM_CONTACT_X:g} {y:g}) '
                    f'list({trunk_x:g} {y:g}) '
                    f'list({trunk_x:g} {TRUNK_BOTTOM_Y:g})) '
                    f"{BOTTOM_W:g})"
                ),
                (
                    'dbCreateLabel(cv list("M3" "pin") '
                    f'list({trunk_x:g} {LABEL_Y:g}) '
                    f'"CODE<{idx}>" "centerCenter" "R90" "roman" {LABEL_HEIGHT:g})'
                ),
            ]
        )

    body.extend(["dbSave(cv)", "dbClose(cv)", "t"])
    inst_vars = " ".join(f"inst{i}" for i in range(UNIT_COUNT))
    return f"let((cv {inst_vars}) {' '.join(body)})"


def main() -> int:
    client = BridgeClient()

    client.execute_skill(build_cdac_skill(), timeout=180)
    client.open_window(LIB_NAME, CELL_NAME, view="layout")
    client.layout.fit_view(timeout=20)

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    client.load_il(SCREENSHOT_IL)
    remote_path = f"/tmp/virtuoso_bridge_screenshots/{CELL_NAME}.png"
    client.run_shell_command("mkdir -p /tmp/virtuoso_bridge_screenshots", timeout=10)
    client.execute_skill(
        f'takeScreenshot("{escape_skill_string(remote_path)}")',
        timeout=30,
    )
    local_path = OUTPUT_DIR / f"{CELL_NAME}.png"
    client.download_file(remote_path, local_path, timeout=30)

    print(f"cell={CELL_NAME}")
    print(f"screenshot={local_path.resolve()}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
