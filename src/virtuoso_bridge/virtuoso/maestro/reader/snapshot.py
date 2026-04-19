"""Top-level aggregator: ``snapshot()``.

One function, two modes — selected by the ``output_root`` kwarg:

- ``output_root=None`` (default) — pure SKILL, returns the in-memory
  dict (~150ms wall, 2 SKILL round-trips, 0 scp).
- ``output_root="..."`` — also writes the disk dump to
  ``{output_root}/{YYYYMMDD_HHMMSS}__{lib}__{cell}/`` (raw + filtered
  XMLs, raw SKILL section dump, latest run's artifacts).  The same
  dict is returned, with ``output_dir`` added.

Three "tracks" of state, deliberately split (when writing to disk):

  1. ``state_from_skill.txt`` — raw SKILL outputs, one labeled section
     per probe (``maeGetEnvOption``, ``maeGetAnalysis(test, "stb")``,
     ``maeGetSimulationMessages``, ...).  No alist→dict parsing — AI /
     human consumers read the SKILL output verbatim.
  2. ``state_from_sdb.xml`` — what's persisted in ``maestro.sdb``
     (corners / vars / parameters / tests / specs / parametersets),
     YAML-filtered subset of the raw sdb.
  3. ``state_from_active_state.xml`` — what's persisted in
     ``active.state`` (per-analysis options for pss / pnoise / tran /
     ac / dc / noise / sp / stb), YAML-filtered.

Filtered XMLs use ``resources/snapshot_filter.yaml`` as the keep-list.
The three tracks never duplicate each other.
"""

from __future__ import annotations

from datetime import datetime
from pathlib import Path

from virtuoso_bridge import VirtuosoClient

from ._parse_sdb import filter_active_state_xml, filter_sdb_xml
from .bundle import full_bundle
from .session import _fetch_window_state, _match_mae_title, natural_sort_histories


# ---------------------------------------------------------------------------
# Disk-dump helpers — only used when output_root is given
# ---------------------------------------------------------------------------

def _scp_quietly(client: VirtuosoClient, remote: str, local: Path) -> bool:
    """scp ``remote`` → ``local``; swallow errors.  Returns True on success."""
    if not remote:
        return False
    try:
        client.download_file(remote, str(local))
    except Exception:
        return False
    return local.exists()


def _write_filtered_xml(local_raw: Path, target: Path, filter_fn) -> None:
    """Read ``local_raw``, apply ``filter_fn``, write to ``target``.
    No-op if raw is missing or filter returns empty."""
    if not local_raw.exists():
        return
    try:
        xml = local_raw.read_text(encoding="utf-8", errors="replace")
        filt = filter_fn(xml)
        if filt:
            target.write_text(filt, encoding="utf-8")
    except OSError:
        pass


def _format_skill_sections(sections: list[tuple[str, str]]) -> str:
    """Render the bundle's raw_sections as a labeled plain-text dump.

    Each section gets a ``== {label} ==`` header followed by the raw
    SKILL output verbatim.  Consumers (AI or human) read SKILL alists
    directly — no JSON conversion.
    """
    out_parts: list[str] = []
    for label, raw in sections:
        out_parts.append(f"== {label} ==")
        out_parts.append((raw or "").rstrip())
        out_parts.append("")   # blank line between sections
    return "\n".join(out_parts).rstrip() + "\n"


def _dump_to_dir(client: VirtuosoClient, *, bundle: dict, lib: str, cell: str,
                 view: str, sess: str, latest_history: str,
                 output_root: str) -> Path:
    """Write the disk-dump artifacts.  Returns the snapshot directory."""
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    snap_dir = Path(output_root) / f"{ts}__{lib}__{cell}"
    snap_dir.mkdir(parents=True, exist_ok=True)

    # --- raw + filtered XMLs (the "golden" setup data) ---
    lib_path = bundle.get("lib_path") or ""
    if lib_path:
        sdb_remote = f"{lib_path}/{cell}/{view}/{view}.sdb"
        local_sdb = snap_dir / "maestro.sdb"
        if _scp_quietly(client, sdb_remote, local_sdb):
            _write_filtered_xml(local_sdb, snap_dir / "state_from_sdb.xml",
                                filter_sdb_xml)
        # active.state is a sibling of maestro.sdb in the OA view dir.
        state_remote = f"{lib_path}/{cell}/{view}/active.state"
        local_state = snap_dir / "active.state"
        if _scp_quietly(client, state_remote, local_state):
            _write_filtered_xml(local_state,
                                snap_dir / "state_from_active_state.xml",
                                filter_active_state_xml)

    # --- raw SKILL dump ---
    sections = bundle.get("raw_sections") or []
    if sections:
        (snap_dir / "state_from_skill.txt").write_text(
            _format_skill_sections(sections), encoding="utf-8")

    # --- latest history's run artifacts (under <history_name>/) ---
    test = bundle.get("test") or ""
    scratch_root = bundle.get("scratch_root") or ""
    results_base = f"{lib_path}/{cell}/{view}/results/maestro" if lib_path else ""
    if latest_history and results_base:
        hist_dir = snap_dir / latest_history
        hist_dir.mkdir(parents=True, exist_ok=True)
        # .log lives in the OA library at a deterministic path.
        _scp_quietly(client,
                     f"{results_base}/{latest_history}.log",
                     hist_dir / f"{latest_history}.log")
        # input.scs / spectre.out live in scratch under /1/{test}/.
        if scratch_root and test:
            scr = (f"{scratch_root}/{lib}/{cell}/{view}"
                   f"/results/maestro/{latest_history}/1/{test}")
            _scp_quietly(client, f"{scr}/netlist/input.scs",
                         hist_dir / "input.scs")
            _scp_quietly(client, f"{scr}/psf/spectre.out",
                         hist_dir / "spectre.out")

    return snap_dir


# ---------------------------------------------------------------------------
# Public entry point
# ---------------------------------------------------------------------------

def snapshot(client: VirtuosoClient, *,
             output_root: str | None = None) -> dict:
    """Aggregate snapshot of the currently-focused maestro session.

    Always uses the focused window (``hiGetCurrentWindow()``) as the
    source of truth — there is no session parameter.  If the user
    wants a specific maestro, they click its window first.

    Mode selector:

    - ``output_root=None`` (default) — SKILL-only; returns a sparse
      in-memory dict.  ~150ms wall, 2 SKILL round-trips, 0 scp.
    - ``output_root="..."`` — also writes the disk dump to
      ``{output_root}/{YYYYMMDD_HHMMSS}__{lib}__{cell}/``:

      * ``maestro.sdb``                  (raw)
      * ``state_from_sdb.xml``           (YAML-filtered)
      * ``active.state``                 (raw)
      * ``state_from_active_state.xml``  (YAML-filtered)
      * ``state_from_skill.txt``         (raw SKILL outputs, sectioned)
      * ``<history_name>/{name}.log``    (latest run)
      * ``<history_name>/input.scs``     (latest run)
      * ``<history_name>/spectre.out``   (latest run)

      The same dict is returned, with ``output_dir`` (str) added.

    Returned dict keys::

        {"location":         "LIB/CELL/VIEW",
         "session":          "fnxSessionN",
         "app":              "assembler" | "explorer" | None,
         "mode":             "Editing" | "Reading" | None,
         "unsaved":          bool,
         "test":             str,
         "enabled_analyses": [name, ...],
         "outputs_count":    int,
         "run_mode":         str,
         "job_control":      str,
         "errors_count":     int,
         "scratch_root":     str | None,
         "lib_path":         str,
         "results_base":     str,
         "latest_history":   str,
         "history_list":     [name, ...]}

    Setup details (variables / corners / parameters / per-analysis
    settings / env options / sim options) are *not* in this dict by
    design — pass ``output_root=...`` and read the XML / .txt files,
    which are the canonical format.
    """
    cur_name, cur_sess, all_names, _all_sessions = _fetch_window_state(client)
    title_match = _match_mae_title([cur_name]) or _match_mae_title(all_names)
    lib  = title_match.get("lib", "")
    cell = title_match.get("cell", "")
    view = title_match.get("view", "") or "maestro"

    bundle = full_bundle(client, sess=cur_sess, lib=lib, cell=cell, view=view) \
             if cur_sess else {}

    lib_path = bundle.get("lib_path") or ""
    history_list = natural_sort_histories(bundle.get("hist_files") or [])
    latest_history = history_list[-1] if history_list else ""

    out: dict = {
        "location":         "/".join(p for p in (lib, cell, view) if p),
        "session":          cur_sess,
        "app":              title_match.get("application"),
        "mode":             ("Editing" if title_match.get("editable")
                             else "Reading" if title_match.get("editable") is False
                             else None),
        "unsaved":          bool(title_match.get("unsaved_changes")),
        "test":             bundle.get("test", ""),
        "enabled_analyses": bundle.get("analyses") or [],
        "outputs_count":    bundle.get("outputs_count", 0),
        "run_mode":         bundle.get("run_mode", ""),
        "job_control":      bundle.get("job_control", ""),
        "errors_count":     bundle.get("errors_count", 0),
        "scratch_root":     bundle.get("scratch_root") or None,
        "lib_path":         lib_path,
        "results_base":     (f"{lib_path}/{cell}/{view}/results/maestro"
                             if lib_path and cell and view else ""),
        "latest_history":   latest_history,
        "history_list":     history_list,
    }

    if output_root is not None:
        if not cur_sess:
            raise RuntimeError("No focused maestro window.")
        snap_dir = _dump_to_dir(
            client, bundle=bundle, lib=lib, cell=cell, view=view,
            sess=cur_sess, latest_history=latest_history,
            output_root=output_root,
        )
        out["output_dir"] = str(snap_dir)

    return out
