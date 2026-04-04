---
name: spectre
description: "Run Cadence Spectre simulations remotely via virtuoso-bridge: upload netlists, execute, parse PSF results. TRIGGER when the user wants to run a SPICE/Spectre simulation from a netlist file, do transient/AC/PSS/pnoise analysis outside Virtuoso GUI, parse PSF waveform data, or mentions Spectre APS/AXS modes. Use this for standalone netlist-driven simulation — for GUI-based ADE Maestro simulation, use the virtuoso skill instead."
---

# Spectre Skill

## How it works

`SpectreSimulator` uploads a `.scs` netlist to a remote machine via SSH, runs Spectre there, downloads the PSF results, and parses them into Python dicts. You write the netlist locally, the simulation runs remotely — no Virtuoso GUI needed. SSH is managed automatically by `SpectreSimulator.from_env()` — just configure `.env` with the remote host and Cadence environment path.

`SpectreSimulator` is independent of `VirtuosoClient` (see the **virtuoso** skill). You can run standalone Spectre simulations without a Virtuoso GUI session.

The typical workflow:
1. Write or prepare a `.scs` netlist (see `references/netlist_syntax.md` for syntax)
2. Create a `SpectreSimulator` instance
3. Call `sim.run_simulation(netlist, options)` — returns a result object with parsed waveforms
4. Analyze `result.data` (dict of signal name → list of float)

## Before you start

1. **Check connection**: `virtuoso-bridge status` — shows Spectre path, version, and license info.
2. **Check examples first**: look at `examples/02_spectre/` below — if similar functionality exists, use it as a basis.
3. **Env requirement**: `VB_CADENCE_CSHRC` must be set in `.env` to source the Cadence environment on the remote machine.

## Core pattern

```python
from virtuoso_bridge.spectre.runner import SpectreSimulator, spectre_mode_args

sim = SpectreSimulator.from_env(
    spectre_args=spectre_mode_args("ax"),  # APS extended (recommended)
    work_dir="./output",
    output_format="psfascii",
)
result = sim.run_simulation("my_netlist.scs", {})

# Check status
if result.ok:
    time = result.data["time"]
    vout = result.data["VOUT"]
else:
    print(result.errors)
```

### With Verilog-A include files

```python
result = sim.run_simulation("tb_adc.scs", {
    "include_files": ["adc_ideal.va", "dac_ideal.va"],
})
```

## Result object

| Attribute | Type | Content |
|-----------|------|---------|
| `result.ok` | bool | Whether simulation succeeded |
| `result.status` | enum | `SUCCESS` / `FAILURE` / `ERROR` |
| `result.data` | dict | Signal name → list of float (parsed waveforms) |
| `result.errors` | list | Error messages from Spectre log |
| `result.warnings` | list | Warning messages |
| `result.metadata["timings"]` | dict | Upload, exec, download, parse durations |
| `result.metadata["output_dir"]` | str | Local path to downloaded `.raw` directory |
| `result.metadata["output_files"]` | list | PSF files in the raw directory |

### Parsing PSF files directly

When you have raw PSF files without going through `run_simulation`:

```python
from virtuoso_bridge.spectre.parsers import parse_psf_ascii_directory
data = parse_psf_ascii_directory("output/tb.raw")
# data = {"time": [...], "VOUT": [...], "VIN": [...]}

# Or a single PSF file (e.g. PSS results)
from virtuoso_bridge.spectre.parsers import parse_spectre_psf_ascii
result = parse_spectre_psf_ascii("output/tb.raw/pss.td.pss")
```

## Simulation modes

Choose based on license availability and performance needs:

```python
spectre_mode_args("spectre")  # basic Spectre (least license demand)
spectre_mode_args("aps")      # APS
spectre_mode_args("ax")       # APS extended (recommended)
spectre_mode_args("cx")       # Spectre X custom
```

## License check

```python
info = sim.check_license()
print(info["spectre_path"])  # which spectre binary
print(info["version"])       # version string
print(info["licenses"])      # license feature availability
```

## References

Load only when needed:

- `references/netlist_syntax.md` — Spectre netlist format, analysis statements, instance syntax, parameterization

## Existing examples

**Always check these before writing new code.**

- `examples/02_spectre/01_inverter_tran.py` — basic inverter transient simulation
- `examples/02_spectre/01_veriloga_adc_dac.py` — 4-bit ADC/DAC transient with Verilog-A
- `examples/02_spectre/02_cap_dc_ac.py` — capacitor DC + AC analysis
- `examples/02_spectre/04_strongarm_pss_pnoise.py` — StrongArm comparator PSS + Pnoise
- Netlists in `examples/02_spectre/assets/`

## Related skills

- **virtuoso** — GUI-based Virtuoso workflow (schematic/layout editing, ADE Maestro simulation). Use when the user is working inside the Virtuoso GUI.
