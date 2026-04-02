---
name: spectre
description: "Use this skill for Spectre simulation through virtuoso-bridge: preparing netlists, running remote simulations, downloading results, and reading simulation outputs. Does not cover live Virtuoso editing, OCEAN flows, or Calibre."
---

# Spectre Skill

## When To Use

Use this skill when the task is about:
- running Spectre examples or new Spectre jobs
- preparing or modifying `.scs` netlists
- sending simulations to the remote host
- downloading and reading simulation outputs
- adding analysis code around Spectre results

Do not use this skill for:
- schematic/layout editing in Virtuoso
- OCEAN script execution
- Calibre DRC/LVS/PEX

## Required Startup Check

Run this first:

```bash
source .venv/bin/activate
virtuoso-bridge status
```

If the bridge path is unhealthy, fix that first. Spectre examples depend on the same remote SSH / RAMIC path.

## API Priority

Prefer the highest-level API that fits:

1. `SpectreSimulator.from_env(...)`
2. packaged helper utilities in `examples/02_spectre/_result_io.py`
3. parser helpers in `src/virtuoso_bridge/spectre/parsers.py`
4. ad hoc file handling around returned result bundles

Do not shell out to remote Spectre manually if the packaged runner can do the job.

## Core APIs

Main package surface:

- `src/virtuoso_bridge/spectre/__init__.py`
  - `SpectreSimulator`
- `src/virtuoso_bridge/spectre/runner.py`
  - `SpectreSimulator.from_env(...)`
  - `SpectreSimulator.run_simulation(...)`
  - `spectre_mode_args(...)`
- `src/virtuoso_bridge/spectre/parsers.py`
  - PSF ASCII parsing helpers

Expected usage pattern:

```python
from virtuoso_bridge.spectre.runner import SpectreSimulator, spectre_mode_args

sim = SpectreSimulator.from_env(
    spectre_cmd="spectre",
    spectre_args=spectre_mode_args("ax"),
    work_dir=work_dir,
    output_format="psfascii",
)
result = sim.run_simulation(netlist_path, {})
```

## Preferred Workflow

1. start from the closest packaged example
2. keep source netlists under `examples/02_spectre/assets/` or a task-specific folder
3. write a run-specific netlist into a task output directory if parameters need patching
4. run through `SpectreSimulator`
5. inspect:
   - `result.status`
   - `result.errors`
   - `result.metadata`
   - downloaded output bundle
6. save post-processed CSV / JSON / plots next to the run output

When an example supports re-analysis, keep the default path as:
- simulate + analyze

Use an explicit flag such as `--analyze-only` only when the user wants to reuse an existing raw result bundle.

## Result Expectations

The runner returns a result object with:
- status / ok / errors / warnings
- parsed waveform data when available
- timing metadata for upload / execute / download phases

When debugging failures, inspect:
- returned `errors`
- remote log files referenced by metadata or output bundle
- generated run netlist

## Example Index

### Main Spectre Examples

- `examples/02_spectre/01_inverter_tran.py`
  - remote inverter transient run, CSV/JSON/plot generation, mode switching
- `examples/02_spectre/02_veriloga_adc_dac.py`
  - mixed Verilog-A ADC/DAC example
- `examples/02_spectre/03_sampling_nmos.py`
  - NMOS sampling testbench with run-time netlist patching
- `examples/02_spectre/04_strongarm_pss_pnoise.py`
  - StrongARM comparator single-point PSS + Pnoise
  - default mode is simulate + analyze
  - `--analyze-only` reuses an existing `.raw` directory
  - writes metrics JSON, summary JSON, and a 3-row time-domain plot:
    - `VCLK` / `VINP` / `VINN`
    - `LP` / `LM`
    - `DCMPP` / `DCMPN`

### Supporting Files

- `examples/02_spectre/_result_io.py`
  - common summary / CSV / timing print helpers
- `examples/02_spectre/assets/`
  - packaged source netlists

## Output Conventions

Preferred output artifacts:
- waveform CSV
- summary JSON
- plot PNG when useful
- metrics JSON for derived analysis values when the example computes them

Keep these inside the example-specific output directory under `examples/02_spectre/output/`.

## Guidance

- prefer packaged Python APIs over manual SSH or manual file copy logic
- keep “simulate” and “analyze” steps clearly separated in code
- for single-point examples, do not add parameter sweeps unless the example is explicitly about sweeping
- if a netlist needs host-specific path patching, write a derived run netlist instead of mutating the source asset
- use `output_format="psfascii"` unless there is a clear reason not to

## File Map

- Spectre runtime: `src/virtuoso_bridge/spectre/`
- examples: `examples/02_spectre/`
- helper output utilities: `examples/02_spectre/_result_io.py`
