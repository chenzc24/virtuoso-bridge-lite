"""Read schematic placement — instances, pins, labels, wires.

Usage:
    from virtuoso_bridge.virtuoso.schematic.reader import read_placement

    placement = read_placement(client, "myLib", "myCell")
    placement = read_placement(client)  # from currently open schematic
"""

from __future__ import annotations

from virtuoso_bridge import VirtuosoClient

_READ_PLACEMENT_SKILL = '''
let((cv instList pinList labelList wireList)
  cv = {cv_expr}
  unless(cv return("ERROR"))
  instList = ""
  foreach(inst cv~>instances
    instList = strcat(instList sprintf(nil "%s|%s|%s|%L|%s\\n"
      inst~>name inst~>libName inst~>cellName inst~>xy inst~>orient)))
  pinList = ""
  foreach(term cv~>terminals
    pinList = strcat(pinList sprintf(nil "%s|%s\\n" term~>name term~>direction)))
  labelList = ""
  foreach(label cv~>shapes
    when(label~>objType == "label"
      labelList = strcat(labelList sprintf(nil "%s|%L\\n" label~>theLabel label~>xy))))
  wireList = ""
  foreach(shape cv~>shapes
    when(shape~>objType == "line"
      wireList = strcat(wireList sprintf(nil "%L\\n" shape~>points))))
  sprintf(nil "INSTANCES\\n%sPINS\\n%sLABELS\\n%sWIRES\\n%sEND" instList pinList labelList wireList))
'''


def _parse_placement(raw: str) -> dict:
    """Parse the SKILL output into a structured dict."""
    result: dict = {"instances": [], "pins": [], "labels": [], "wires": []}
    section = None
    for line in raw.splitlines():
        line = line.strip()
        if line in ("INSTANCES", "PINS", "LABELS", "WIRES"):
            section = line.lower()
        elif line == "END" or not line:
            continue
        elif section == "instances":
            parts = line.split("|")
            if len(parts) >= 5:
                result["instances"].append({
                    "name": parts[0], "lib": parts[1], "cell": parts[2],
                    "xy": parts[3], "orient": parts[4],
                })
        elif section == "pins":
            parts = line.split("|")
            if len(parts) >= 2:
                result["pins"].append({"name": parts[0], "direction": parts[1]})
        elif section == "labels":
            parts = line.split("|", 1)
            if len(parts) >= 2:
                result["labels"].append({"text": parts[0], "xy": parts[1]})
        elif section == "wires":
            result["wires"].append(line)
    return result


def read_placement(
    client: VirtuosoClient,
    lib: str | None = None,
    cell: str | None = None,
) -> dict:
    """Read all placement info from a schematic.

    If lib/cell provided, opens the cellview read-only.
    If omitted, reads from the currently open schematic.
    """
    if lib and cell:
        cv_expr = f'dbOpenCellViewByType("{lib}" "{cell}" "schematic" "schematic" "r")'
    else:
        cv_expr = "geGetEditCellView()"

    skill = _READ_PLACEMENT_SKILL.replace("{cv_expr}", cv_expr)
    r = client.execute_skill(skill, timeout=30)
    raw = (r.output or "").strip('"').replace("\\n", "\n").replace('\\"', '"')
    return _parse_placement(raw)
