---
name: virtuoso
description: "Use this skill for live Virtuoso work through virtuoso-bridge: bridge startup/status, SKILL/IL execution, library/cellview queries, screenshots, and schematic/layout editing through the namespace APIs. Does not cover Spectre, OCEAN, or Calibre flows."
---

# Virtuoso Skill

## When To Use

Use this skill when the task is about:
- starting, checking, or restarting the bridge service
- loading `.il` files or running raw SKILL in Virtuoso
- reading Virtuoso library, cellview, instance, or geometry data
- editing schematic or layout through `BridgeClient`
- taking screenshots from schematic/layout windows

Do not use this skill for:
- Spectre simulation pipelines
- OCEAN analysis flows
- Calibre DRC/LVS/PEX

## Required Startup Check

Run these before any live Virtuoso action:

```bash
source .venv/bin/activate
virtuoso-bridge status
```

If status is not healthy:
- try `virtuoso-bridge restart`
- if the service says to load `virtuoso_setup.il`, do that in Virtuoso CIW first

## Preferred Entry Points

Use the installed CLI for service lifecycle:

```bash
virtuoso-bridge init
virtuoso-bridge start
virtuoso-bridge restart
virtuoso-bridge status
```

Use Python for live operations:

```python
from virtuoso_bridge import BridgeClient

client = BridgeClient()
client.layout.edit(...)
client.schematic.edit(...)
```

## Visibility During Trial Layout Work

When doing temporary layout trials, parameter probes, or geometry experiments, do not work only in the background.

Required behavior:
- open the layout window for the trial cell with `client.open_window(..., view="layout")`
- fit the view after meaningful edits
- keep the user able to see the intermediate layout you are testing

Reason:
- the user wants visibility into the live trial-and-error process
- visual feedback often catches bad assumptions before the final screenshot step

## API Priority

Prefer the highest-level API that fits:

1. `client.schematic.edit(...)` / `client.layout.edit(...)`
2. `client.schematic.*` / `client.layout.*`
3. formal builder functions under `src/virtuoso_bridge/virtuoso/`
4. raw `client.execute_skill(...)`
5. `client.load_il(...)` + `execute_skill(...)`

Do not hand-write low-level SKILL in examples or automation if a formal Python API already exists.

## Core Client APIs

Main `BridgeClient` methods that should be preferred:

- session / control
  - `status()`
  - `ensure_ready()`
  - `warm_remote_session()`
  - `get_current_design()`
  - `open_window()`
  - `open_cell_view()`
  - `save_current_cellview()`
  - `close_current_cellview()`
  - `download_file()`
  - `run_shell_command()`
- raw Virtuoso interaction
  - `execute_skill()`
  - `load_il()`
  - `execute_operations()`
- namespaces
  - `client.layout.*`
  - `client.schematic.*`

## References

Read these only when needed. Load only the layout reference for layout work, and only the schematic reference for schematic work:

- layout-specific API, mosaic guidance, and examples:
  - `references/layout.md`
- reusable skill-local layout assets:
  - `assets/cfmom_unary_cdac_reference.py`
- metal pixel-art workflow for portraits / images drawn with metal layers:
  - `references/metal_pixel_art.md`
- process-node metal-rule notes for layout sizing / spacing questions:
  - `references/t28_metal_rules.md`
- CDAC / unit-cap usage guidance:
  - `references/cdac.md`
- schematic-specific API, terminal-aware helpers, and examples:
  - `references/schematic.md`
- bindkey-derived operation/API lookup:
  - `references/bindkey_operation_index.md`
  - raw archive: `references/raw_bindkeys.il`

## Raw SKILL And IL

Use raw SKILL only when there is no formal API yet.

Preferred order:
- add a formal builder in `src/virtuoso_bridge/virtuoso/schematic/ops.py`
- or `src/virtuoso_bridge/virtuoso/layout/ops.py`
- expose it through the matching editor/namespace layer
- only then use it from examples or agent code

If you must use IL:
- prefer packaged files under `examples/01_virtuoso/assets/`
- load them through `client.load_il(...)`
- for repeated skill workflows, prefer a checked-in helper under `.agents/skills/virtuoso/assets/` instead of rebuilding the script from scratch each time

## Large Layout Edit Guardrail

Do not submit very large layout shape batches as one `execute_operations(...)` or one giant raw SKILL payload.

Reason:
- the bridge / Virtuoso execution path can truncate oversized payloads
- the failure can show up as partial symbols such as `dbCreat...`
- the resulting errors are misleading, for example `unbound variable` or malformed `dbCreateRect` bboxes

Required pattern for large artwork, dense mosaics, or bulk rect/path generation:
- split layout edits into smaller chunks
- open the first chunk with `mode="w"` and later chunks with `mode="a"`
- save after each chunk through the normal editor context manager
- if a bulk edit fails with a truncated-looking symbol or impossible geometry error, suspect payload length first and reduce chunk size before debugging coordinates

Default bias:
- prefer conservative chunking for thousands of shapes
- only increase chunk size after the smaller batch size is proven stable in the current bridge/session

For very large generated layouts, prefer packaged `.il` helpers over giant inline SKILL strings.

Recommended pattern:
- put the generation loop in an `.il` file
- load it with `client.load_il(...)`
- call a short entry-point function with a small parameter list

Do not:
- send a giant one-shot raw SKILL string containing thousands of `dbCreate*` calls
- assume `.il` automatically fixes the problem if the call site still passes an oversized payload

The real guardrail is keeping each request payload small. `.il` is preferred because it lets Python send a short command while the heavy loop runs inside Virtuoso.

## Screenshot Review Rule

For layout work, screenshot review is mandatory.

After every screenshot comes back, visually inspect the image before concluding the work is correct.

Screenshot review is necessary but not sufficient.
For any nontrivial routing edit, perform an explicit short-check before claiming success.

Minimum short-check expectation:
- identify the intended conductors and the conductors that must stay isolated
- compare the new route geometry against the known landing metals or master-cell geometry
- if available, use connectivity readback or net highlighting
- if connectivity tooling is not available, do a bbox / overlap sanity check and state that this was a geometric short check, not extraction

Minimum required checks:
- any abnormal geometry
- accidental shorts
- route heads that only connect halfway
- route heads that overshoot or stick out past the intended contact
- elbows that are not full-width
- floating labels
- leftover shapes from previous attempts

Do not rely only on coordinates, bbox dumps, or geometry text when judging routed layout quality.
If the screenshot disagrees with the numeric reasoning, trust the screenshot and fix the geometry.
