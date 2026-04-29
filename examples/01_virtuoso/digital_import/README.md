# digital_import — recipes for pulling P&R products into Virtuoso

Two cookbook scripts that complete the **RTL → GDS → integrate into
Virtuoso** loop after Genus + Innovus finish.  Both scripts drive a
*standalone Cadence batch tool* through SKILL ``system()`` (no GUI
forms, no ``hiFormDone`` gymnastics).

## Platform support

These scripts are pure Python with no host-OS-specific calls — they
work on Linux, macOS, and Windows.  All paths passed in are *remote*
Linux paths (the Virtuoso box's filesystem); the local OS only ferries
strings through ``argparse`` and SSH.

The one Windows catch is **Git Bash / Cygwin / MSYS2**: those
environments mangle Linux-style absolute paths
(``/home/zhangz/foo`` becomes ``C:/Program Files/Git/home/zhangz/foo``)
before argv reaches Python.  Use PowerShell, native ``cmd``, or WSL on
Windows; Linux and macOS users have nothing to worry about.

## Common prerequisites

1. ``virtuoso-bridge start`` is running and ``virtuoso-bridge status``
   shows the daemon as OK.
2. The Virtuoso work directory's ``cds.lib`` already contains a
   ``DEFINE`` line for every library these scripts touch, e.g.:

   ```
   DEFINE DIG_OUTPUT                  /home/you/work/DIG_OUTPUT
   DEFINE tsmcN28                     /home/process/.../tsmcN28        ← tech library
   DEFINE tcbn28hpcplusbwp12t30p140   /home/process/.../bwp12t30p140   ← std-cell ref library
   ```

   Both ``strmin`` and ``ihdl`` create cellview directories on disk
   but do **not** edit ``cds.lib`` — if a library is not registered,
   Virtuoso simply won't see the result.

## ``import_gds.py`` — physical layout via ``strmin``

Wraps Cadence's standalone ``strmin`` tool.

```
python import_gds.py /path/to/foo.route_tapeout.gds \
       --target-lib DIG_OUTPUT \
       --tech-lib   tsmcN28 \
       --ref-libs   /path/to/ref_libs_dir
```

After completion the script prints ``instances=N shapes=M bbox=...`` for
the new ``layout`` view as a sanity check.

## ``add_power_labels.py`` — drop VDD/VSS labels onto a routed layout

``strmin`` produces a layout that's pure geometry — no power-net labels.
This script walks the layout's instance list, finds the first one whose
master has both the named power and ground pins, reads those pins'
geometry, transforms through the instance xform (handles R0 / MX / MY /
R180), and drops a label centered on each rail at the layout's middle x.

```
python add_power_labels.py --target-lib DIG_OUTPUT --cell LFSR_32BIT
```

Defaults assume a typical TSMC-style PDK (``--power-pin VDD --ground-pin
VSS --layer M1 --purpose pin --font roman --height 1.0``).  Override via
flags for other PDKs:

```
python add_power_labels.py --target-lib DIG_OUTPUT --cell my_block \
    --power-pin VPWR --ground-pin VGND \
    --power-label "VPWR!" --ground-label "VGND!"
```

User has to know nothing about which std-cell library the design uses —
the script auto-discovers a reference cell from the instance list.

## ``import_verilog.py`` — schematic + symbol via ``ihdl``

Wraps Cadence's standalone ``ihdl`` tool — the Cadence-documented
"command-line / batch" entry point for Verilog Import (see *Verilog In
for Virtuoso Design Environment User Guide*).  Generates a
``schematic`` view and a ``symbol`` view in the target library; on
behavioural modules an additional ``functional`` view is created.

```
python import_verilog.py /path/to/foo_import.v \
       --target-lib DIG_OUTPUT \
       --ref-libs   tcbn28hpcplusbwp12t30p140
```

The script writes a temporary ``ihdl_parameter`` file under ``/tmp`` (via
SKILL ``outfile``), runs ``ihdl`` from Virtuoso's working directory, and
verifies the imported cell by opening its schematic view and counting
instances/nets/terms.

If ``import_verilog.py`` ever fails, look at
``<virtuoso_workdir>/verilogIn.batch.log`` — that's where ``ihdl``
writes detailed diagnostics.

## Porting to a non-TSMC-N28 PDK

Three CLI flags are PDK-sensitive — defaults below were chosen for the
TSMC N28 12-track family this repo grew up with.  When you switch to a
different PDK or different cell library, override them on the command
line (none of the scripts hard-code paths or library names).

| Flag | Where | Default | Override when... |
|---|---|---|---|
| `--tech-lib` | `import_gds.py` | `tsmcN28` | The OA tech library that supplies your design rules / layer table is named differently in your `cds.lib` |
| `--ref-libs` | `import_verilog.py` | `tcbn28hpcplusbwp12t30p140` | You're targeting a different std-cell library (e.g. `sky130_fd_sc_hd`) |
| `--power-pin`, `--ground-pin` | `add_power_labels.py` | `VDD`, `VSS` | Open-source PDKs often use `VPWR`/`VGND` instead |
| `--height` | `add_power_labels.py` | `1.0` µm | Std-cell row height differs.  28 nm 12T row = 1.2 µm so 1 µm fits.  For 7 nm 5T cells (row ≈ 0.5 µm) drop to 0.3–0.4 |

Examples for sky130:

```bash
python import_gds.py        my.gds         --target-lib MY_LIB --tech-lib sky130A --ref-libs $PDK_ROOT/sky130A/libs.tech/sky130_fd_pr
python import_verilog.py    my_import.v    --target-lib MY_LIB --ref-libs sky130_fd_sc_hd
python add_power_labels.py  --target-lib MY_LIB --cell my --power-pin VPWR --ground-pin VGND --height 0.4
```

There's also one IC-version dependency (not PDK):
``import_verilog.py`` writes ``structural_views := 5`` into the
``ihdl_parameter`` file, which is the IC618 batch encoding for "schematic +
functional".  Cross-tested only on IC618 SP201; if a future IC release
renumbers the encoding, the fix is a one-line lookup-table update in
``STRUCTURAL_VIEWS`` at the top of the script.

## Why these are recipes, not first-class CLI commands

Both scripts delegate to vendor batch tools whose option semantics are
private to a specific Cadence IC release (tested on **IC618 SP201**).
They **may need adjustments on other IC versions** if Cadence renames a
parameter key or moves a tool.  Keeping them here as cookbook examples
— rather than as ``virtuoso-bridge import-*`` subcommands — limits the
blast radius when a Cadence upgrade shifts the ground.
