"""Single-round-trip SKILL bundle for ``snapshot()``.

:func:`full_bundle` composes every SKILL probe ``snapshot()`` needs
into one ``let((...) ... list(...))`` expression — the wire-side
cost collapses to one round-trip.

Returns brief-shaped fields (test name, analyses names, output count,
run mode, latest-history info) plus ``raw_sections`` — an ordered
list of ``(label, raw_skill_text)`` tuples for the
``state_from_skill.txt`` dump.  No XML→dict / SKILL alist→dict
parsing — raw text is the canonical format.

Caller extracts ``sess`` / ``lib`` / ``cell`` / ``view`` from the
focused window title via :func:`_fetch_window_state` first — that's
a tiny separate SKILL call.
"""

from __future__ import annotations

from virtuoso_bridge import VirtuosoClient

from ._parse_skill import _parse_skill_str_list, _tokenize_top_level


def _split_top_level(raw: str, expected: int) -> list[str]:
    """Strip outer parens, tokenize top-level into ``expected`` slots,
    pad with empty strings if the response was truncated.
    """
    body = (raw or "").strip()
    if body.startswith("(") and body.endswith(")"):
        body = body[1:-1]
    slots = _tokenize_top_level(
        body,
        include_strings=True,
        include_atoms=True,
        include_groups=True,
        max_tokens=expected,
    )
    while len(slots) < expected:
        slots.append("")
    return slots


def _unquote(s: str) -> str:
    s = (s or "").strip()
    if s.startswith('"') and s.endswith('"'):
        return s[1:-1]
    return "" if s in ("", "nil") else s


def _unwrap_errset(s: str) -> str:
    """``errset(X)`` returns ``(X)`` on success or ``nil`` on error.
    Strip the outer parens (or return "" on error)."""
    s = (s or "").strip()
    if s in ("", "nil"):
        return ""
    if s.startswith("(") and s.endswith(")"):
        return s[1:-1].strip()
    return s


def _parse_int(s: str) -> int:
    s = (s or "").strip()
    try:
        return int(s)
    except (TypeError, ValueError):
        return 0


def _scratch_root_from_run_dir(run_dir: str, lib: str, cell: str, view: str) -> str:
    """Strip ``/{lib}/{cell}/{view}/results/maestro/...`` suffix from
    ``asiGetAnalogRunDir`` output to recover the install prefix."""
    if not (run_dir and lib and cell and view):
        return ""
    marker = f"/{lib}/{cell}/{view}/results/maestro"
    idx = run_dir.find(marker)
    return run_dir[:idx] if idx > 0 else ""


def full_bundle(client: VirtuosoClient, *,
                sess: str, lib: str, cell: str, view: str) -> dict:
    """Single SKILL round-trip → brief fields + raw SKILL section dump.

    Returns::

        {<all brief_bundle fields>,
         "errors_count": int,
         "raw_sections": [(label, raw_text), ...]}

    ``raw_sections`` is an ordered list of ``(label, raw_text)`` tuples
    suitable for serializing to ``state_from_skill.txt``.  Each label
    names the SKILL function that produced ``raw_text``; the text is
    untouched (no alist→dict parsing).

    The user's design cellview (config vs schematic) is not fetched —
    no SKILL path returns the unresolved cellview reliably; truth lives
    in ``active.state``'s adeInfo.designInfo (read the filtered XML).
    """
    if not sess:
        return {}

    expr = f'''
let((tests test enabled libPath histDir runDirOK outsExpr)
  tests    = maeGetSetup(?session "{sess}")
  test     = if(tests car(tests) "")
  enabled  = if(test maeGetEnabledAnalysis(test ?session "{sess}") nil)
  libPath  = errset(ddGetObj("{lib}")~>readPath)
  histDir  = strcat(car(libPath) "/{cell}/{view}/results/maestro")
  runDirOK = errset(asiGetAnalogRunDir(asiGetSession("{sess}")))
  outsExpr = if(test
    let((outs result)
      outs = maeGetTestOutputs(test ?session "{sess}")
      result = list()
      foreach(o outs
        result = append1(result
          list(o~>name o~>type o~>signal o~>expression
               o~>plot o~>save o~>evalType o~>yaxisUnit o~>spec)))
      result)
    nil)
  list(
    car(libPath)
    tests
    test
    enabled
    mapcar(lambda((a) maeGetAnalysis(test a ?session "{sess}")) enabled)
    if(test maeGetEnvOption(test ?session "{sess}") nil)
    if(test maeGetSimOption(test ?session "{sess}") nil)
    outsExpr
    maeGetCurrentRunMode(?session "{sess}")
    maeGetJobControlMode(?session "{sess}")
    errset(maeGetRunPlan(?session "{sess}"))
    errset(axlGetCurrentHistory("{sess}"))
    errset(maeGetSimulationMessages(?session "{sess}" ?msgType "error"))
    errset(maeGetSimulationMessages(?session "{sess}" ?msgType "warning"))
    errset(maeGetSimulationMessages(?session "{sess}" ?msgType "info"))
    if(isDir(histDir) getDirFiles(histDir) nil)
    car(runDirOK)
  ))
'''
    r = client.execute_skill(expr)

    # Unpack the bundle response into named slots.  Order MUST match the
    # ``list(...)`` body in the SKILL expression above; adding/removing
    # a slot means updating both sides together.
    (s_libpath, s_tests, s_test, s_enabled, s_analyses,
     s_env, s_sim, s_outputs,
     s_runmode, s_jobcontrol, s_runplan, s_currhist,
     s_errors, s_warnings, s_infos,
     s_histfiles, s_rundir) = _split_top_level(r.output or "", expected=17)

    test_name = _unquote(s_test)
    enabled = _parse_skill_str_list(_unwrap_errset(s_enabled))

    # outputs_count: count top-level groups in the expanded outputs slot.
    # The expansion shape is ``((name type ... ) (name type ...) ...)`` —
    # one group per defined output.
    outputs_count = len(_tokenize_top_level(
        _unwrap_errset(s_outputs),
        include_groups=True, include_strings=False, include_atoms=False,
    ))

    # errors_count: maeGetSimulationMessages error returns ("...", "..."),
    # one entry per error message.  Empty messages ("") shouldn't count.
    errors_count = sum(1 for m in _parse_skill_str_list(_unwrap_errset(s_errors))
                       if m.strip())

    # raw_sections: ordered list for state_from_skill.txt.  Per-analysis
    # entries are split out so the .txt has one section per maeGetAnalysis
    # call (cleaner than a nested list dump).
    analyses_raw = _split_top_level(s_analyses, expected=len(enabled)) if enabled else []
    sections: list[tuple[str, str]] = [
        (f'ddGetObj("{lib}")~>readPath',                 s_libpath),
        (f'maeGetSetup(?session "{sess}")',              s_tests),
        (f'maeGetEnabledAnalysis("{test_name}")',        s_enabled),
    ]
    for ana, raw in zip(enabled, analyses_raw):
        sections.append(
            (f'maeGetAnalysis("{test_name}" "{ana}")', raw))
    sections.extend([
        (f'maeGetEnvOption("{test_name}")',              s_env),
        (f'maeGetSimOption("{test_name}")',              s_sim),
        (f'maeGetTestOutputs("{test_name}") expanded',   s_outputs),
        (f'maeGetCurrentRunMode(?session "{sess}")',     s_runmode),
        (f'maeGetJobControlMode(?session "{sess}")',     s_jobcontrol),
        (f'maeGetRunPlan(?session "{sess}")',            s_runplan),
        (f'axlGetCurrentHistory("{sess}")',              s_currhist),
        (f'maeGetSimulationMessages error',              s_errors),
        (f'maeGetSimulationMessages warning',            s_warnings),
        (f'maeGetSimulationMessages info',               s_infos),
        (f'getDirFiles(<results/maestro>)',              s_histfiles),
        (f'asiGetAnalogRunDir(asiGetSession("{sess}"))', s_rundir),
    ])

    return {
        "lib_path":      _unquote(s_libpath),
        "test":          test_name,
        "analyses":      enabled,
        "outputs_count": outputs_count,
        "run_mode":      _unquote(s_runmode),
        "job_control":   _unquote(s_jobcontrol),
        "errors_count":  errors_count,
        "hist_files":    _parse_skill_str_list(_unwrap_errset(s_histfiles)),
        "scratch_root":  _scratch_root_from_run_dir(
            _unquote(s_rundir), lib, cell, view),
        "raw_sections":  sections,
    }
