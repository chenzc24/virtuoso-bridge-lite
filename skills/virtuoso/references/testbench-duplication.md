# Duplicate a Testbench Within the Same Library

Workflow for cloning an existing testbench cell (schematic + config + maestro)
to a new cell name in the **same library** — i.e. `CELL` → `CELL_2` — so the
clone can be edited/simulated independently without touching the original.

Different from `testbench-migration.md` (which copies a testbench across
libraries by rebuilding the schematic). This doc is about file-level cloning
where the DUT and testbench are left intact; only the containing cell is
renamed.

## The three views, three copy mechanisms

Maestro testbenches typically have three views — **each needs a different
approach** because only `schematic` is a true DFII cellview:

| View | Mechanism | Why |
|------|-----------|-----|
| `schematic` | `dbCopyCellView` | Standard DFII cellview |
| `config` | shell `cp -r` + text patch | CDB, not db; `dbCopyCellView` returns nil |
| `maestro` | shell `cp -r` + text patch | SDB (XML), not db; `dbCopyCellView` returns nil |

Attempting `dbCopyCellView` on config or maestro **silently returns nil** —
no error, no copy. You must shell-cp those directories.

## Full procedure

Assume `LIB=PLAYGROUND_AGENTS`, source `SRC=_TB_CMP_PNOISE`, target
`DST=_TB_CMP_PNOISE_2`, all views: `schematic`, `config`, `maestro`.

### 1. Verify source views + target slot is free

```python
r = client.execute_skill(f'ddGetObj("{LIB}" "{SRC}")~>views~>name')
# e.g. ("maestro" "schematic" "config")

r = client.execute_skill(f'if(ddGetObj("{LIB}" "{DST}") "EXISTS" "free")')
assert r.output.strip('"') == "free"
```

### 2. Copy schematic via SKILL API

```python
r = client.execute_skill(f'''
let((src new)
  src = dbOpenCellViewByType("{LIB}" "{SRC}" "schematic" nil "r")
  new = dbCopyCellView(src "{LIB}" "{DST}" "schematic" nil)
  dbClose(src)
  when(new dbClose(new))
  if(new "OK" "FAIL"))
''')
assert r.output.strip('"') == "OK"
```

This creates `{LIB}/{DST}/schematic/` on the filesystem and registers the
new cell in the library index.

### 3. Copy config + maestro directories via shell

```python
src = f"/path/to/{LIB}/{SRC}"
dst = f"/path/to/{LIB}/{DST}"  # created by step 2
client.run_shell_command(
    f'cp -r {src}/config {dst}/config && cp -r {src}/maestro {dst}/maestro')
```

You can get `/path/to/{LIB}/{CELL}` via `ddGetObj(LIB CELL)~>readPath`.

### 4. Refresh the library index

```python
client.execute_skill(f'ddSyncWriteLock(ddGetObj("{LIB}"))')

# Verify all three views are now registered:
r = client.execute_skill(f'ddGetObj("{LIB}" "{DST}")~>views~>name')
# Should show ("maestro" "schematic" "config")
```

Skip this step and Library Manager will not display the new views until
Virtuoso is restarted.

### 5. Patch the config (`expand.cfg`)

The config declares two things that reference the old cell name:

```
config _TB_CMP_PNOISE;                              ← config name
design PLAYGROUND_AGENTS._TB_CMP_PNOISE:schematic;  ← top-level binding
```

Both must change to `_TB_CMP_PNOISE_2`. Use full-context sed to avoid
matching cells that happen to contain the old name as a substring:

```python
client.run_shell_command(
    f"sed -i "
    f"-e 's/config {SRC};/config {DST};/g' "
    f"-e 's/design {LIB}\\.{SRC}:schematic;/design {LIB}.{DST}:schematic;/g' "
    f"{dst}/config/expand.cfg"
)
```

Ignore the sibling `expand.cfg%` — that's a Cadence backup/undo file,
regenerated on next save.

### 6. Patch the maestro (`maestro.sdb`)

The sdb typically has ~10-20 references to the old cell name, distributed
across:

- `<option>cell <value>SRC</value></option>` — **authoritative design binding**
- `<loggingdatabasedir>` — historical run paths (breadcrumbs)
- `<resultsname>`, `<psfdir>`, `<simdir>`, `<runlog>` — ditto

**Full substitution is the right move.** The history-breadcrumb paths may
become garbage (point at non-existent `{DST}` histories), but Cadence
rediscovers runs from the filesystem at open time — stale breadcrumbs don't
block anything.

**Do not use `run_shell_command` with `sed`/`perl` for this** — that goes
through `csh()` in SKILL, and csh eats `!` as history expansion, silently
mangling any Perl negative-lookahead (`(?!_2)`). Download → patch locally in
Python → upload back:

```python
import re
from pathlib import Path

local = Path("tmp/sdb_edit.sdb")
client.download_file(f"{dst}/maestro/maestro.sdb", str(local))

text = local.read_text(encoding="utf-8")
# Negative lookahead ensures idempotency if you re-run
new = re.sub(rf'{re.escape(SRC)}(?!_2)', DST, text)
assert new.count(DST) == text.count(SRC), "substitution count mismatch"
local.write_text(new, encoding="utf-8", newline="")

client.upload_file(str(local), f"{dst}/maestro/maestro.sdb")
```

### 7. Verify

```python
from virtuoso_bridge.virtuoso.maestro import open_session, close_session

# Background open — no GUI
sess = open_session(client, LIB, DST)
r = client.execute_skill(f'maeGetSetup(?session "{sess}")')
# Should list test names; session opens without errors
close_session(client, sess)
```

Or eyeball it in GUI:

```python
from virtuoso_bridge.virtuoso.maestro import open_gui_session
open_gui_session(client, LIB, DST)
```

Confirm the design-binding row at the top of the Maestro window shows
`LIB/DST/config`, and double-click → config opens → references the new
schematic.

## Gotchas

### `upload_file` preserves the **source** filename

`client.upload_file(local, remote)` tars up the file at `local`, extracts
into `dirname(remote)`, and keeps the source basename. If your local file is
named `new_sdb.xml` but the target is `maestro.sdb`, you'll end up with a
file called `new_sdb.xml` in the target directory.

**Rename locally before uploading:**

```python
import shutil
shutil.copy("tmp/edit.xml", "tmp/maestro.sdb")
client.upload_file("tmp/maestro.sdb", f"{dst}/maestro/maestro.sdb")
```

### `run_shell_command` stdout is not returned

It calls `csh("...")` in SKILL, which returns `t`/`nil` (success/fail) and
sends stdout to the CIW log — not back to Python. For anything that needs
output, either:

- Redirect to a file and `download_file` it
- Use `execute_skill` with `infile`/`gets`/`close` to read the file via
  SKILL directly

### Special characters in `run_shell_command`

Because the shell is `csh`, watch out for:

- `!` — history expansion; escape as `\!` or avoid entirely
- `$` — variable expansion; usually fine if using `sed` with single quotes
- `#` — comment marker in csh scripts

When in doubt, patch files locally in Python and upload.

### `dbCopyCellView` silently returns nil for non-db views

No error is raised. Always check the return value:

```python
r = client.execute_skill('... dbCopyCellView(...) ...')
if "FAIL" in (r.output or ""):
    # fall back to shell cp
```

### Stale history paths in the new sdb are harmless

After substitution, paths like
`/path/to/OLD_LIB/DST/maestro/results/maestro/Interactive.N.log` may point
at directories that don't exist. This is fine — Cadence rediscovers
histories by walking `{cellview_path}/results/maestro/` at open time, not
by trusting the sdb's breadcrumbs. New simulations will write to the
correct `{LIB}/{DST}/maestro/results/maestro/` path automatically.

## Reference substitution counts (for sanity check)

A typical maestro testbench with ~6 analyses and ~5 historical runs:

| File | `{OLD_CELL}` occurrences |
|------|--------------------------|
| `expand.cfg` | 2 |
| `maestro.sdb` | 10-30 |
| Schematic `.oa*` | 0 (cell name stored in `data.dm`, updated by `dbCopyCellView`) |

If `maestro.sdb` has dramatically more (100+), there's likely Monte-Carlo
or sweep history bloat — still safe to substitute, just confirms you
want the full replace.
