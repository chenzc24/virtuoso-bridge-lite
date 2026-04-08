---
name: virtuoso
description: "MANDATORY — MUST load this skill when the user mentions: Virtuoso, Maestro, ADE, CIW, SKILL (Cadence), layout, schematic, cellview, OCEAN, design variables, or any Cadence EDA operation. Bridge to remote Cadence Virtuoso: SKILL execution, layout/schematic editing, ADE Maestro simulation setup via Python API. TRIGGER when the user mentions Virtuoso, SKILL (the Cadence language), Cadence IC, layout editing, schematic creation, cellview operations, CIW commands, ADE setup, Maestro configuration, design variables, OCEAN results, or any EDA task involving a Cadence design database — even if they just say 'draw a circuit' or 'place some transistors'."
---

# Virtuoso Skill

## Mental Model

You control a remote Cadence Virtuoso through `virtuoso-bridge`. Python runs locally; SKILL executes remotely in the Virtuoso CIW. SSH tunneling is automatic.

```
 Local (Python)                    Remote (Virtuoso)
┌──────────────────┐   SSH tunnel  ┌──────────────────┐
│ VirtuosoClient   │ ────────────► │ CIW (SKILL)      │
│                  │               │                  │
│ • schematic.*    │               │ • dbCreateInst   │
│ • layout.*       │               │ • schCreateWire  │
│ • execute_skill  │               │ • mae*           │
│ • load_il        │               │ • dbOpenCellView │
└──────────────────┘               └──────────────────┘
```

### Three abstraction levels

| Level | When to use | Example |
|-------|-------------|---------|
| **Python API** | Schematic/layout editing — structured, safe | `client.schematic.edit(lib, cell)` |
| **Inline SKILL** | Maestro, CDF params, anything the API doesn't cover | `client.execute_skill('maeRunSimulation()')` |
| **SKILL file** | Bulk operations, complex loops | `client.load_il("my_script.il")` |

Always use the highest level that works. Drop to a lower level only when needed.

**Never guess function names.** If the function isn't in the examples below, read the relevant `references/` file before writing the call. Fabricating a wrong name wastes time debugging in CIW.

### Four domains

| Domain | What it does | Python package | API docs |
|--------|-------------|----------------|----------|
| **Schematic** | Create/edit schematics, wire instances, add pins | `client.schematic.*` | `references/schematic-python-api.md`, `references/schematic-skill-api.md` |
| **Layout** | Create/edit layout, add shapes/vias/instances | `client.layout.*` | `references/layout-python-api.md`, `references/layout-skill-api.md` |
| **Maestro** | Read/write ADE Assembler config, run simulations | `virtuoso_bridge.virtuoso.maestro` | `references/maestro-python-api.md`, `references/maestro-skill-api.md` |
| **General** | File transfer, screenshots, raw SKILL, .il loading | `client.*` | See below |

## Before you start

### Environment setup

> **Always use `uv` + virtual environment.** Never install into the global Python. `uv` refuses global installs by default, preventing accidental pollution.

```bash
uv venv .venv && source .venv/bin/activate   # Windows: source .venv/Scripts/activate
uv pip install -e .
```

All `virtuoso-bridge` CLI commands and Python scripts must run inside the activated venv.

### Connection sequence (follow in order)

1. **Check `.env`** — if the project has no `.env` yet, run **`virtuoso-bridge init`** to create one. If `.env` already exists, skip `init`.
2. **`virtuoso-bridge start`** — starts the local bridge service and SSH tunnel.
3. **If status is `degraded`** — the user must load the setup script in Virtuoso CIW (the `start` output tells them exactly what to run).
4. **`virtuoso-bridge status`** — verify everything is `healthy` before proceeding.

### Then

- **Check examples first**: `examples/01_virtuoso/` — don't reinvent from scratch.
- **Open the window**: `client.open_window(lib, cell, view="layout")` so the user sees what you're doing.

## Client basics

```python
from virtuoso_bridge import VirtuosoClient
client = VirtuosoClient.from_env()

client.execute_skill('...')                     # run SKILL expression
client.load_il("my_script.il")                  # upload + load .il file
client.upload_file(local_path, remote_path)      # local → remote
client.download_file(remote_path, local_path)    # remote → local
client.open_window(lib, cell, view="layout")     # open GUI window
client.run_shell_command("ls /tmp/")             # run shell on remote
```

### CIW output vs return value

`execute_skill()` returns the result to Python but does **not** print anything in the CIW window. This is by design — the bridge is a programmatic API, not an interactive REPL.

```python
# Return value only — CIW stays silent
r = client.execute_skill("1+2")        # Python gets 3, CIW shows nothing

# To also display in CIW, use printf explicitly
r = client.execute_skill(r'let((v) v=1+2 printf("1+2 = %d\n" v) v)')
#   Python gets 3, CIW shows "1+2 = 3"
```

Full example: `examples/01_virtuoso/basic/00_ciw_output_vs_return.py`

## Printing multi-line text to CIW

Sending multiple `printf` in a single `execute_skill()` loses newlines — the CIW concatenates everything on one line. To print multi-line text, write it as a Python multiline string and send one `execute_skill()` per line:

```python
text = """\
========================================
  Title goes here
========================================
  First paragraph line one.
  First paragraph line two.

  Second paragraph.
========================================"""

for line in text.splitlines():
    client.execute_skill('printf("' + line + '\\n")')
```

Constraints:
- **ASCII only** — emojis and CJK characters cause a JSON encoding error on the remote SKILL interpreter
- **No unescaped SKILL special chars** in the text — if the line may contain `"` or `%`, escape them (`\\"`, `%%`) or use `load_il()` instead (see `03_load_il.py`)

> **IMPORTANT: Always write `.py` files, never use `python -c`.**
> `python -c "..."` has shell 引号 + Python 引号 + SKILL 引号三层转义叠加，`\\n` 很容易变成 `\\\\n` 导致 `printf` 静默失败（不报错但不输出）。
> 正确做法：将代码写入 `.py` 文件再用 `python script.py` 执行，转义只有 Python + SKILL 两层，与例子一致。

Full example: `examples/01_virtuoso/basic/02_ciw_print.py`

## References

Load on demand — each contains detailed API docs and edge-case guidance:

| File | Contents |
|------|----------|
| `references/schematic-skill-api.md` | Schematic SKILL API, terminal-aware helpers, CDF params |
| `references/schematic-python-api.md` | SchematicEditor, SchematicOps, low-level builders |
| `references/layout-skill-api.md` | Layout SKILL API, read/query, mosaic, layer control |
| `references/layout-python-api.md` | LayoutEditor, LayoutOps, shape/via/instance creation |
| `references/maestro-skill-api.md` | mae* SKILL functions, OCEAN, corners, known blockers |
| `references/maestro-python-api.md` | Session, read_config (verbose 0/1/2), writer functions |
| `references/netlist.md` | CDL/Spectre netlist formats, spiceIn import |

## Examples

**Always check these before writing new code.**

### `examples/01_virtuoso/basic/`
- `00_ciw_output_vs_return.py` — CIW output vs Python return value (when CIW prints, when it doesn't)
- `01_execute_skill.py` — run arbitrary SKILL expressions
- `02_ciw_print.py` — print messages to CIW (one `execute_skill` per line)
- `03_load_il.py` — upload and load .il files
- `04_list_library_cells.py` — list libraries and cells
- `05_multiline_skill.py` — multi-line SKILL with comments, loops, procedures
- `06_screenshot.py` — capture layout/schematic screenshots

### `examples/01_virtuoso/schematic/`
- `01a_create_rc_stepwise.py` — create RC schematic via operations
- `01b_create_rc_load_skill.py` — create RC schematic via .il script
- `02_read_connectivity.py` — read instance connections and nets
- `03_read_instance_params.py` — read CDF instance parameters
- `05_rename_instance.py` — rename schematic instances
- `06_delete_instance.py` — delete instances
- `07_delete_cell.py` — delete cells from library
- `08_import_cdl_cap_array.py` — import CDL netlist via spiceIn (SSH)

### `examples/01_virtuoso/layout/`
- `01_create_layout.py` — create layout with rects, paths, instances
- `02_add_polygon.py` — add polygons
- `03_add_via.py` — add vias
- `04_multilayer_routing.py` — multi-layer routing
- `05_bus_routing.py` — bus routing
- `06_read_layout.py` — read layout shapes
- `07–10` — delete/clear operations

### `examples/01_virtuoso/maestro/`
- `01_read_open_maestro.py` — read config from the currently open maestro
- `02_gui_open_read_close_maestro.py` — GUI open → read config → close
- `03_bg_open_read_close_maestro.py` — background open → read config → close
- `04_read_env.py` — read environment settings (model files, sim options, run mode)
- `05_read_results.py` — read simulation results (output values, specs, yield)
- `06a_rc_create.py` — create RC schematic + Maestro setup
- `06b_rc_simulate.py` — run simulation
- `06c_rc_read_results.py` — read results, export waveforms, open GUI

## Common workflows

### Find which library contains a cell

`ddGetObj(cellName)` with a single argument returns nil — must iterate `ddGetLibList()`:

```python
r = client.execute_skill(f'''
let((result)
  result = nil
  foreach(lib ddGetLibList()
    when(ddGetObj(lib~>name "{CELL}")
      result = cons(lib~>name result)))
  result)
''')
# r.output e.g. '("2025_FIA")'
```

No need for a separate script — inline in any workflow that needs to locate a cell before operating on it.

### Read a design (schematic + maestro + netlist)

```python
from virtuoso_bridge import VirtuosoClient
from virtuoso_bridge.virtuoso.maestro import read_config

client = VirtuosoClient.from_env()
LIB, CELL = "myLib", "myCell"

# 1. Schematic — structured data via IL helper
client.load_il("examples/01_virtuoso/assets/read_connectivity.il")
r = client.execute_skill(f'ReadSchematic("{LIB}" "{CELL}")')
# r.output is a SKILL list: (("lib" ...) ("instances" ...) ("nets" ...) ("pins" ...))

# 2. Maestro — open GUI, read config, close
client.open_window(LIB, CELL, view="schematic")  # must open schematic first
r = client.execute_skill(f'''
let((before after session)
  before = maeGetSessions()
  deOpenCellView("{LIB}" "{CELL}" "maestro" "maestro" nil "r")
  after = maeGetSessions()
  session = nil
  foreach(s after unless(member(s before) session = s))
  session
)
''')
session = (r.output or "").strip('"')
config = read_config(client, session)           # dict of key → (skill_expr, raw)
# close maestro window after reading

# 3. Netlist — generate on remote, download via SSH
test = client.execute_skill(f'car(maeGetSetup(?session "{session}"))').output.strip('"')
client.execute_skill(
    f'maeCreateNetlistForCorner("{test}" "Nominal" "/tmp/nl_{CELL}" ?session "{session}")')
client.download_file(f"/tmp/nl_{CELL}/netlist/input.scs", "output/netlist.scs")
```

### Run a simulation

**Follow this sequence exactly. Do not skip steps.**

```python
session = "fnxSession33"  # from find_open_session() or maeGetSessions()

# 1. Set variables
client.execute_skill(f'maeSetVar("CL" "1p" ?session "{session}")')

# 2. Save before running — REQUIRED, skipping causes stale state
client.execute_skill(
    f'maeSaveSetup(?lib "{LIB}" ?cell "{CELL}" ?view "maestro" ?session "{session}")')

# 3. Run (async — NEVER use ?waitUntilDone t, it deadlocks the event loop)
r = client.execute_skill(f'maeRunSimulation(?session "{session}")', timeout=30)
history = (r.output or "").strip('"')

# 4. Wait — blocks until simulation finishes (GUI mode only)
r = client.execute_skill("maeWaitUntilDone('All)", timeout=300)

# 5. Check for GUI dialog blockage — if wait returned empty/nil,
#    a dialog is blocking CIW. Try dismissing it:
if not r.output or r.output.strip() in ("", "nil"):
    client.execute_skill("hiFormDone(hiGetCurrentForm())", timeout=5)
    # If still stuck, user must manually dismiss the dialog in Virtuoso

# 6. Read results
client.execute_skill(f'maeOpenResults(?history "{history}")', timeout=15)
r = client.execute_skill(f'maeGetOutputValue("myOutput" "myTest")', timeout=30)
value = float(r.output) if r.output else None
client.execute_skill("maeCloseResults()", timeout=10)
```

**In optimization loops:** add `maeSaveSetup` and dialog-recovery in every iteration. GUI dialogs ("Specify history name", "No analyses enabled") block the entire SKILL channel — all subsequent `execute_skill` calls will timeout until the dialog is dismissed.

### Gotchas

- **`csh()` returns `t`/`nil`**, not command output. Never use it to verify files. Use `download_file` (SSH/SCP) for all remote file operations.
- **`procedurep()` returns `nil` for compiled functions** like `maeCreateNetlistForCorner`. The function still exists — test by calling it with wrong args instead.
- **Netlist files are on the remote.** `maeCreateNetlistForCorner` writes to the remote filesystem. Always use `client.download_file()` to retrieve them.
- **Design variables:** `maeGetSetup(?typeName "globalVar")` may return nil. Use `asiGetDesignVarList(asiGetCurrentSession())` instead.

## Related skills

- **spectre** — standalone netlist-driven Spectre simulation (no Virtuoso GUI). Use when the user has a `.scs` netlist and wants to run it directly.
