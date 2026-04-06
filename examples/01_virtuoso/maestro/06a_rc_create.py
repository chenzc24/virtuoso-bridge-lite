#!/usr/bin/env python3
"""Step 1: Create RC filter schematic + Maestro setup.

Creates:
- Schematic: vdc (AC=1) → R (1k) → C (c_val) → GND, with pin OUT
- Maestro: AC analysis 1Hz–10GHz, sweep c_val = 1p,100f, BW spec > 1GHz

Run this once, then use 06b to simulate and 06c to read results.
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent))
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent / "src"))

from virtuoso_bridge import VirtuosoClient
from virtuoso_bridge.virtuoso.maestro import (
    open_session, close_session, create_test, set_analysis,
    add_output, set_spec, set_var, save_setup,
)

LIB = "PLAYGROUND_LLM"
CELL = "TB_RC_FILTER"


def main() -> int:
    client = VirtuosoClient.from_env()
    print(f"[info] {LIB}/{CELL}")

    # --- Create schematic ---
    print("[schematic] Creating RC filter...")
    with client.schematic.edit(LIB, CELL) as sch:
        sch.add_instance("analogLib", "vdc", (0, 0), name="V0")
        sch.add_instance("analogLib", "gnd", (0, -0.625), name="GND0")
        sch.add_instance("analogLib", "res", (1.5, 0.5), orientation="R90", name="R0")
        sch.add_instance("analogLib", "cap", (3.0, 0), name="C0")
        sch.add_instance("analogLib", "gnd", (3.0, -0.625), name="GND1")
        sch.add_wire_between_instance_terms("V0", "PLUS", "R0", "PLUS")
        sch.add_wire_between_instance_terms("R0", "MINUS", "C0", "PLUS")
        sch.add_wire_between_instance_terms("C0", "MINUS", "GND1", "gnd!")
        sch.add_wire_between_instance_terms("V0", "MINUS", "GND0", "gnd!")
        sch.add_pin_to_instance_term("C0", "PLUS", "OUT")

    # Set CDF parameters
    cv = "_rcfCv"
    client.execute_skill(f'{cv} = dbOpenCellViewByType("{LIB}" "{CELL}" "schematic" nil "a")')
    for inst, param, val in [("V0", "vdc", "0"), ("V0", "acm", "1"),
                              ("R0", "r", "1k"), ("C0", "c", "c_val")]:
        client.execute_skill(
            f'cdfFindParamByName(cdfGetInstCDF('
            f'car(setof(i {cv}~>instances i~>name == "{inst}")))'
            f' "{param}")~>value = "{val}"')
    client.execute_skill(f"schCheck({cv})")
    client.execute_skill(f"dbSave({cv})")
    r = client.execute_skill(f"{cv}~>instances~>name")
    print(f"[schematic] {LIB}/{CELL}/schematic")
    print(f"  Instances: {r.output}")
    print(f"  V0: vdc=0, acm=1 | R0: r=1k | C0: c=c_val | Pin: OUT")

    # --- Create Maestro ---
    print("[maestro] Creating setup...")
    session = open_session(client, LIB, CELL)

    create_test(client, "AC", lib=LIB, cell=CELL, session=session)
    set_analysis(client, "AC", "tran", enable=False, session=session)
    set_analysis(client, "AC", "ac",
                 options='(("start" "1") ("stop" "10G") '
                         '("incrType" "Logarithmic") ("stepTypeLog" "Points Per Decade") '
                         '("dec" "20"))',
                 session=session)
    add_output(client, "Vout", "AC", output_type="net", signal_name="/OUT", session=session)
    add_output(client, "BW", "AC", output_type="point",
               expr='bandwidth(mag(VF(\\"/OUT\\")) 3 \\"low\\")', session=session)
    set_spec(client, "BW", "AC", gt="1G", session=session)
    set_var(client, "c_val", "1p,100f", session=session)

    save_setup(client, LIB, CELL, session=session)
    close_session(client, session)
    print(f"[maestro] {LIB}/{CELL}/maestro")
    print(f"  Test: AC | Analysis: ac 1Hz-10GHz, 20pts/dec")
    print(f"  Outputs: Vout (net /OUT), BW (bandwidth expr)")
    print(f"  Spec: BW > 1GHz")
    print(f"  Sweep: c_val = 1p, 100f")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
