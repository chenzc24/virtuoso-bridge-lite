"""Window-state probes for the focused maestro session.

Three internal helpers used by :mod:`snapshot` and the CLI brief:

- ``_fetch_window_state`` — single SKILL call → focused title, focused
  window's ``davSession`` (its bound maestro session id), every window
  title, open sessions list.
- ``_match_mae_title`` — pure regex over a maestro window title →
  lib / cell / view / mode / unsaved.
- ``natural_sort_histories`` — filter + sort a ``results/maestro/``
  directory listing into ordered history names.

All three are module-private (no ``__all__`` here, no public re-export).
"""

from __future__ import annotations

import re

from virtuoso_bridge import VirtuosoClient

from ._parse_skill import _parse_skill_str_list, _tokenize_top_level


_MAE_TITLE_RE = re.compile(
    r"ADE\s+(Assembler|Explorer)\s+(Editing|Reading):\s+"
    r"(\S+)\s+(\S+)\s+([^\s*]+)(\*?)"
    # Optional OpenAccess library checkout suffix:
    # ``... maestro Version: 1 -CheckedOut`` or ``... maestro Version:7-CheckedOut``.
    r"(?:\s+Version:\s*\S+(?:\s*-\s*\S+)?)?"
    r"\s*$"
)
# A history is anchored by its .rdb metadata file (any user-given name —
# Interactive.0.RO, closeloop_PVT_postsim, sweep_set.3, etc.).  Bare
# directories matching Cadence's ``Interactive.N`` / ``MonteCarlo.N``
# shape are also accepted for setups without .rdb anchors.
_HISTORY_RDB_RE = re.compile(r"^(?!\.)[^/\\]+\.rdb$")
_HISTORY_DIR_RE = re.compile(r"^(Interactive|MonteCarlo)\.[0-9]+(?:\.[A-Z]{2,4})?$")


def _match_mae_title(titles) -> dict:
    """Parse the first maestro-like title into structured fields.

    Title format::

        Virtuoso® ADE {Assembler|Explorer} {Editing|Reading}: LIB CELL VIEW[*]

    ``*`` at the end is Virtuoso's "unsaved changes" indicator.

    Returns a dict with keys application, lib, cell, view, editable,
    unsaved_changes — empty dict if no title matches.  ``application``
    is ``"assembler"`` or ``"explorer"`` (lower-case).
    """
    for n in titles or ():
        if not n:
            continue
        m = _MAE_TITLE_RE.search(n)
        if m:
            app, mode, lib, cell, view, star = m.groups()
            return {
                "application": app.lower(),
                "lib": lib,
                "cell": cell,
                "view": view,
                "editable": mode == "Editing",
                "unsaved_changes": star == "*",
            }
    return {}


def _fetch_window_state(client: VirtuosoClient) -> tuple[str, str, list[str], list[str]]:
    """One SKILL round-trip: (focused_name, focused_session, all_names, all_sessions).

    The focused-window's bound maestro session is read directly from
    its ``davSession`` attribute — Cadence stores the session id there
    for ADE Assembler windows.  Empty string for non-maestro windows
    (schematic / layout / waveform / ...).

    No ``geGetEditCellView`` / ``geGetWindowCellView`` here — those warn
    on non-graphic windows like the maestro Assembler (GE-2067).
    """
    r = client.execute_skill(
        'let((cw) '
        'cw = hiGetCurrentWindow() '
        'list('
        '  if(cw hiGetWindowName(cw) nil) '
        '  if(cw cw->davSession nil) '
        '  mapcar(lambda((w) hiGetWindowName(w)) hiGetWindowList()) '
        '  maeGetSessions()))'
    )
    body = (r.output or "").strip()
    if body.startswith("(") and body.endswith(")"):
        body = body[1:-1]
    chunks = _tokenize_top_level(
        body, include_strings=True, include_atoms=True, max_tokens=4,
    )
    while len(chunks) < 4:
        chunks.append("nil")
    cur_name = chunks[0].strip().strip('"') if chunks[0] != "nil" else ""
    cur_sess = chunks[1].strip().strip('"') if chunks[1] != "nil" else ""
    return (cur_name, cur_sess,
            _parse_skill_str_list(chunks[2]),
            _parse_skill_str_list(chunks[3]))


def natural_sort_histories(hist_files: list[str]) -> list[str]:
    """Extract history names from a ``results/maestro`` dir listing.

    Histories anchor on ``<name>.rdb`` metadata files; bare directories
    matching ``Interactive.N`` / ``MonteCarlo.N`` are also accepted.
    Sorts naturally so ``Interactive.2`` < ``Interactive.10``.

    Pure function — no I/O.  Used internally by snapshot to populate
    ``info["history_list"]`` and by the CLI brief to find the latest
    history's ``.log`` / ``.scs`` / ``.out`` paths.
    """
    seen: set[str] = set()
    for h in hist_files:
        if _HISTORY_RDB_RE.match(h):
            seen.add(h[:-4])
        elif _HISTORY_DIR_RE.match(h):
            seen.add(h)

    def _natkey(s: str):
        return [
            (int(tok) if tok.isdigit() else 0, tok)
            for tok in re.findall(r"\d+|\D+", s)
        ]

    return sorted(seen, key=_natkey)
