"""Post-simulation result reads + OCEAN waveform export.

Two public entry points:

- :func:`read_results` — open the latest history in GUI mode and pull
  every output value + spec status + overall yield as structured data.
  This is *consumption-time* data (numbers users compute on), so the
  return is a dict — distinct from snapshot's "describe the setup"
  flow which keeps SKILL outputs as raw text.
- :func:`export_waveform` — call OCEAN's ``ocnPrint`` to dump one
  expression's waveform to a local text file via scp.
"""

from __future__ import annotations

import re

from virtuoso_bridge import VirtuosoClient

from ._parse_skill import _parse_sexpr, _parse_skill_str_list
from ._skill import _q, _get_test, _unique_remote_wave_path
from .session import natural_sort_histories


# ---------------------------------------------------------------------------
# read_results — GUI-mode scalar / spec-status reads
# ---------------------------------------------------------------------------

def read_results(client: VirtuosoClient, session: str,
                  lib: str = "", cell: str = "",
                  history: str = "",
                  *,
                  include_raw: bool = False) -> dict:
    """Read simulation results: output values, spec status, yield.

    Requires GUI mode (``deOpenCellView`` + ``maeMakeEditable``).
    Finds the latest valid history by walking the results dir
    newest-first (covers Interactive.N, sweep_*, ExplorerRun.*, any
    user-named history).  Returns ``{}`` if no results are available.

    Returns::

        {
          "history":       "Interactive.7",
          "tests":         [test_name, ...],
          "outputs":       [{"test", "name", "value", "spec_status"}, ...],
          "overall_spec":  "passed" | "failed" | None,
          "overall_yield": "100" | None,
        }

    With ``include_raw=True`` the raw SKILL output strings (pre-parse)
    are attached under ``"raw"`` for debug / audit.

    Args:
        session: active session string
        lib: library name (auto-detected if empty)
        cell: cell name (auto-detected if empty)
        history: explicit history name (preferred, e.g. "Interactive.7").
            If empty, falls back to scanning latest valid Interactive.N.
        include_raw: attach raw SKILL output strings under ``"raw"``.
    """
    def q(label, expr):
        return _q(client, label, expr)

    # Get lib/cell if not provided
    if not lib or not cell:
        test = _get_test(client, session)
        if test:
            if not lib:
                r = client.execute_skill(
                    f'maeGetEnvOption("{test}" ?option "lib" ?session "{session}")')
                lib = (r.output or "").strip('"')
            if not cell:
                r = client.execute_skill(
                    f'maeGetEnvOption("{test}" ?option "cell" ?session "{session}")')
                cell = (r.output or "").strip('"')

    if not lib or not cell:
        return {}

    test = _get_test(client, session)
    if history:
        latest_history = history.strip()
    else:
        # List the maestro results directory, accept any history name
        # (Interactive.N, sweep_*, ExplorerRun.*, user-named).  Anchor
        # on the ``<name>.rdb`` metadata file via natural_sort_histories.
        r = client.execute_skill(
            f'let((p d) '
            f'p = ddGetObj("{lib}")~>readPath '
            f'd = strcat(p "/{cell}/maestro/results/maestro") '
            f'if(isDir(d) getDirFiles(d) nil))'
        )
        files = _parse_skill_str_list(r.output or "")
        hist_list = natural_sort_histories(files)
        latest_history = ""
        # Natural-sort puts oldest-first; walk newest-first.
        for h in reversed(hist_list):
            r = client.execute_skill(
                f'when(maeOpenResults(?history "{h}") '
                f'  let((outs) '
                f'    outs = maeGetResultOutputs(?testName "{test}") '
                f'    maeCloseResults() '
                f'    outs))'
            )
            out = (r.output or "").strip()
            if out and out != "nil":
                latest_history = h
                break

    if not latest_history or latest_history == "nil":
        return {}

    # Open the valid history
    open_expr = f'maeOpenResults(?history "{latest_history}")'
    opened = q("maeOpenResults", open_expr)
    if not opened or opened.strip('"') in ("nil", ""):
        return {}

    # Raw SKILL captures — kept in a side-channel for debug / include_raw.
    raw_tests  = q("maeGetResultTests",   'maeGetResultTests()')
    # Returns: ((test outputName value specStatus) ...) — flat entries.
    raw_values = q("maeGetOutputValues", '''
let((tests info)
  info = list()
  tests = maeGetResultTests()
  foreach(test tests
    let((outputs)
      outputs = maeGetResultOutputs(?testName test)
      foreach(outName outputs
        let((val spec)
          val = maeGetOutputValue(outName test)
          spec = maeGetSpecStatus(outName test)
          info = append1(info list(test outName val spec))
        )
      )
    )
  )
  info
)
''')
    raw_overall = q("maeGetOverallSpecStatus", 'maeGetOverallSpecStatus()')
    raw_yield   = q("maeGetOverallYield",
                    f'maeGetOverallYield("{latest_history}")')
    client.execute_skill('maeCloseResults()')

    structured = _parse_results(
        raw_tests=raw_tests, raw_values=raw_values,
        raw_overall=raw_overall, raw_yield=raw_yield,
        history=latest_history,
    )
    if include_raw:
        structured["raw"] = {
            "maeGetResultTests":        raw_tests,
            "maeGetOutputValues":       raw_values,
            "maeGetOverallSpecStatus":  raw_overall,
            "maeGetOverallYield":       raw_yield,
        }
    return structured


def _parse_results(*, raw_tests: str, raw_values: str,
                    raw_overall: str, raw_yield: str,
                    history: str) -> dict:
    """Pure: decode the four SKILL result strings into a structured dict."""
    tests = _parse_skill_str_list(raw_tests)

    outputs: list[dict] = []
    parsed = _parse_sexpr(raw_values.strip())
    if isinstance(parsed, list):
        for entry in parsed:
            if isinstance(entry, list) and len(entry) >= 4:
                test_n, name, value, spec = entry[:4]
                outputs.append({
                    "test":        test_n if isinstance(test_n, str) else "",
                    "name":        name if isinstance(name, str) else "",
                    "value":       "" if value is None else str(value),
                    "spec_status": "" if spec is None else str(spec),
                })

    def _unquote_atom(raw: str) -> str | None:
        s = (raw or "").strip().strip('"')
        if not s or s.lower() == "nil":
            return None
        return s

    return {
        "history":       history,
        "tests":         tests,
        "outputs":       outputs,
        "overall_spec":  _unquote_atom(raw_overall),
        "overall_yield": _unquote_atom(raw_yield),
    }


# ---------------------------------------------------------------------------
# export_waveform — OCEAN-driven single-expression dump
# ---------------------------------------------------------------------------

def export_waveform(
    client: VirtuosoClient,
    session: str,
    expression: str,
    local_path: str,
    *,
    analysis: str = "ac",
    history: str = "",
) -> str:
    """Export a waveform via OCEAN to a local text file.

    Args:
        session: session string (used to find history if not given)
        expression: OCEAN expression, e.g. ``'dB20(mag(VF("/VOUT")))'``
        local_path: where to save locally
        analysis: which analysis to select ("ac", "tran", "noise", etc.)
        history: explicit history name; auto-detected if empty

    Returns the local file path.
    """
    # Auto-detect history name from the current results dir.
    # The path shape is `.../maestro/results/maestro/{history}/...` where
    # `{history}` can be any name Cadence wrote — Interactive.N, sweep_*,
    # ExplorerRun.0, user-named, etc.  We capture any non-slash run.
    if not history:
        r = client.execute_skill('asiGetResultsDir(asiGetCurrentSession())')
        rd = (r.output or "").strip('"')
        m = re.search(r'/maestro/results/maestro/([^/]+)/', rd)
        if m:
            history = m.group(1)
        else:
            raise RuntimeError(
                "No simulation history found from asiGetResultsDir. "
                "Pass history= explicitly, or ensure maestro GUI is open."
            )

    remote_path = _unique_remote_wave_path(history)

    # First maeOpenResults to point asiGetResultsDir at the correct history,
    # then use OCEAN openResults with that path.
    client.execute_skill(f'maeOpenResults(?history "{history}")')
    r = client.execute_skill('asiGetResultsDir(asiGetCurrentSession())')
    results_dir = (r.output or "").strip('"')
    client.execute_skill('maeCloseResults()')

    if not results_dir or results_dir == "nil" or "tmpADE" in results_dir:
        raise RuntimeError(f"No valid results directory for {history}")
    if f"/{history}/" not in results_dir:
        raise RuntimeError(
            f"History mismatch: expected {history}, got resultsDir={results_dir}"
        )

    client.execute_skill(f'openResults("{results_dir}")')
    client.execute_skill(f'selectResults("{analysis}")')
    client.execute_skill(
        f'ocnPrint({expression} '
        f'?numberNotation \'scientific ?numSpaces 1 '
        f'?output "{remote_path}")')

    client.download_file(remote_path, local_path)
    client.execute_skill(f'deleteFile("{remote_path}")')
    return local_path
