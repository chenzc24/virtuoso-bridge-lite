---
name: optimizer
description: "Optimize analog circuit parameters (transistor sizing, biasing, passive values) by looping Spectre simulations with Bayesian optimization (TuRBO). TRIGGER when the user wants to sweep, tune, or optimize circuit parameters to meet specs — e.g., minimize power-delay product, maximize bandwidth, find optimal W/L ratios, or any design-space exploration that requires repeated simulation."
---

# Circuit Optimizer Skill

## How it works

The optimizer wraps a Spectre simulation inside a black-box optimization loop. Each iteration: substitute parameter values into a netlist template → run Spectre remotely → extract a scalar metric from the results → feed it to the optimizer. TuRBO (Trust Region Bayesian Optimization) is the default algorithm — it handles noisy, expensive simulations well by maintaining a local Gaussian Process model inside adaptive trust regions.

The key components you need to define:
1. **Parameters + bounds** — what to optimize (e.g. transistor widths, bias currents)
2. **Netlist template** — a `.scs` file with `@@PARAM@@` placeholders
3. **Objective function** — run simulation, extract metrics, return a scalar to minimize

## Before you start

1. **Get the spectre skill working first** — the optimizer depends on `SpectreSimulator`. Make sure `virtuoso-bridge status` shows Spectre available.
2. **Start from the template** — copy `assets/turbo_optimize_template.py` to your project and adapt it. The template includes logging, convergence plotting, and error handling out of the box.
3. **Install dependencies**:
   ```bash
   pip install torch gpytorch
   pip install -e TuRBO/    # local TuRBO repo
   ```
   For simpler cases (few parameters, smooth landscape), `scipy.optimize.minimize` works without the GP overhead.

## Core pattern

```python
import numpy as np
from virtuoso_bridge.spectre.runner import SpectreSimulator

sim = SpectreSimulator.from_env(work_dir="./opt_output", output_format="psfascii")

# 1. Parameters and bounds
PARAMS = ["W_tail", "W_inp", "W_lat"]
LB = np.array([0.5, 0.5, 0.5])
UB = np.array([10., 10., 6.])

# 2. Objective: netlist → simulate → scalar
def objective(x):
    netlist = generate_netlist(x, PARAMS)
    result = sim.run_simulation(netlist, {})
    if not result.ok:
        return 1e6  # penalty for failed sims
    power = extract_power(result)
    delay = extract_delay(result)
    return power * delay

# 3. Run TuRBO
from turbo import Turbo1
turbo = Turbo1(f=objective, lb=LB, ub=UB,
               n_init=2*len(LB), max_evals=100, batch_size=1)
turbo.optimize()

# 4. Best result
best_idx = turbo.fX.argmin()
for name, val in zip(PARAMS, turbo.X[best_idx]):
    print(f"  {name} = {val:.3f}")
```

## Netlist parameterization

Use `@@PARAM@@` placeholders in a template netlist, then replace with Python:

```python
def generate_netlist(x, param_names):
    template = Path("tb_template.scs").read_text()
    for name, val in zip(param_names, x):
        template = template.replace(f"@@{name}@@", f"{val:.6g}")
    out = Path("opt_output/tb_run.scs")
    out.write_text(template)
    return out
```

See the **spectre** skill's `references/netlist_syntax.md` for Spectre netlist format details.

## Objective function design

The objective must return a **scalar float**. Return `1e6` on failure — never `nan` or `inf` (breaks the GP model).

| Goal | Return value |
|------|-------------|
| Minimize power-delay product | `power * delay` |
| Minimize noise-power FOM | `power * noise**2` |
| Maximize gain-bandwidth | `-(gain_db + 20*log10(bw))` (negate for minimization) |
| With constraint penalty | `obj + 1e3 * max(0, noise - 500e-6)**2` |

For multi-objective optimization, combine metrics into a single scalar via weighted sum or constraint penalties. True Pareto optimization is not built in.

## Template file

`assets/turbo_optimize_template.py` — a ready-to-adapt template with:
- Parameter definition and bounds
- Pluggable `apply_params()` / `run_simulation()` / `extract_metrics()` hooks
- JSON result logging after every evaluation
- Convergence plot generation
- Best-result summary output

Copy it and fill in the four `# TODO` functions. Run with `python turbo_optimize_<your_circuit>.py`.

## Related skills

- **spectre** — the underlying simulation runner (`SpectreSimulator`). Read this skill for netlist syntax, result parsing, and simulation modes.
- **virtuoso** — if the circuit lives in Virtuoso, use the virtuoso skill to create/edit the schematic and export a netlist template before optimizing.
