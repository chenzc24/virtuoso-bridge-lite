"""Runtime inspection helpers for the local bridge process graph."""

from __future__ import annotations

import json
import os
import re
import shutil
import subprocess
import time
from datetime import datetime
from pathlib import Path
from typing import Any

from dotenv import load_dotenv

from virtuoso_bridge.virtuoso.basic.service import BridgeService
from virtuoso_bridge.transport.ssh import SSHRunner, remote_ssh_env_from_os

_LSOF_LINE_RE = re.compile(
    r"^(?P<command>\S+)\s+(?P<pid>\d+)\s+(?P<user>\S+)\s+.*?\sTCP\s+(?P<name>.+)$"
)
_RULE_WIDTH = 72
_COLUMN_GAP = "    "
_SHORT_VALUE_WIDTH = 24

def _rb_host() -> str:
    return "127.0.0.1"

def _rb_port() -> int:
    from virtuoso_bridge.virtuoso.basic.bridge import _default_remote_port
    try:
        raw = os.getenv("VB_REMOTE_PORT", "").strip()
        return int(raw) if raw else _default_remote_port()
    except (TypeError, ValueError, AttributeError):
        return _default_remote_port()

def _format_epoch(value: Any) -> str | None:
    if not isinstance(value, (int, float)):
        return None
    return datetime.fromtimestamp(value).strftime("%Y-%m-%d %H:%M:%S")

def _run_text_command(args: list[str]) -> subprocess.CompletedProcess[str] | None:
    try:
        return subprocess.run(args, capture_output=True, text=True, timeout=5, check=False)
    except (FileNotFoundError, OSError, subprocess.TimeoutExpired):
        return None

def _process_snapshot(pid: int | None) -> dict[str, Any] | None:
    if not pid:
        return None

    proc = _run_text_command(["ps", "-o", "pid=,ppid=,lstart=,command=", "-p", str(pid)])
    if proc is None or proc.returncode != 0 or not proc.stdout.strip():
        return None

    line = proc.stdout.strip()
    parts = line.split(None, 7)
    if len(parts) < 8:
        return {
            "pid": pid,
            "raw": line,
        }

    started_at = " ".join(parts[2:7])
    command = parts[7]
    return {
        "pid": int(parts[0]),
        "ppid": int(parts[1]),
        "started_at": started_at,
        "command": command,
    }

def _parse_lsof_output(output: str) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for line in output.splitlines():
        if not line.strip() or line.startswith("COMMAND"):
            continue
        match = _LSOF_LINE_RE.match(line)
        if not match:
            continue
        name = match.group("name").strip()
        state_match = re.search(r"\(([^)]+)\)\s*$", name)
        state = state_match.group(1) if state_match else None
        rows.append(
            {
                "command": match.group("command"),
                "pid": int(match.group("pid")),
                "user": match.group("user"),
                "name": name,
                "state": state,
            }
        )
    return rows

def _list_tcp_entries(port: int, *, state: str | None = None) -> list[dict[str, Any]]:
    lsof_cmd = shutil.which("lsof")
    if not lsof_cmd:
        return []

    args = [lsof_cmd, "-nP", f"-iTCP:{port}"]
    if state:
        args.append(f"-sTCP:{state}")
    proc = _run_text_command(args)
    if proc is None or proc.returncode not in (0, 1):
        return []
    entries = _parse_lsof_output(proc.stdout)
    by_pid: dict[int, dict[str, Any] | None] = {}
    for entry in entries:
        pid = entry["pid"]
        if pid not in by_pid:
            by_pid[pid] = _process_snapshot(pid)
        if by_pid[pid] is not None:
            entry["process"] = by_pid[pid]
    return entries

def _service_summary(service: BridgeService) -> dict[str, Any]:
    state = service.read_state()
    pid = state.get("pid") if isinstance(state, dict) else None
    process = _process_snapshot(pid if isinstance(pid, int) else None)
    return {
        "port": service.port,
        "state_path": str(service.state_path),
        "state": state,
        "process": process,
        "listeners": _list_tcp_entries(service.port, state="LISTEN"),
        "connections": _list_tcp_entries(service.port),
    }

def _jump_host_summary(
    jump_host: str | None,
    jump_user: str | None,
    remote_user: str | None = None,
) -> dict[str, Any]:
    if not jump_host:
        return {
            "configured": False,
            "host": None,
            "user": None,
            "reachable": None,
            "elapsed": None,
        }

    effective_user = jump_user or remote_user
    started = time.time()
    runner = SSHRunner(
        host=jump_host,
        user=effective_user,
        connect_timeout=2,
        persistent_shell=False,
    )
    ssh_cmd = " ".join(runner._build_ssh_base() + ["-T", "exit", "0"])
    reachable = runner.test_connection(timeout=2)
    return {
        "configured": True,
        "host": jump_host,
        "user": effective_user,
        "ssh_cmd": ssh_cmd,
        "reachable": reachable,
        "elapsed": round(time.time() - started, 3),
    }

def _daemon_summary(port: int) -> dict[str, Any]:
    listeners = _list_tcp_entries(port, state="LISTEN")
    return {
        "host": _rb_host(),
        "port": port,
        "listeners": listeners,
        "connections": _list_tcp_entries(port),
    }

def _port_usage_summary(host: str, port: int) -> dict[str, Any]:
    listeners = _condense_entries(_list_tcp_entries(port, state="LISTEN"))
    occupied = bool(listeners)
    owners: list[str] = []
    for entry in listeners:
        owners.append(f"{entry.get('command')} pid={entry.get('pid')}")
    return {
        "host": host,
        "port": port,
        "occupied": occupied,
        "owners": owners,
        "listeners": listeners,
    }

def _inferred_chain(config: dict[str, Any], service: dict[str, Any], daemon: dict[str, Any]) -> list[str]:
    lines: list[str] = []
    service_state = service.get("state") or {}
    service_status = service_state.get("status")
    if service_status:
        lines.append(
            f"local bridge service: {service.get('port')} ({service_status})"
        )
    else:
        lines.append(f"local bridge service: {service.get('port')} (not running)")

    if daemon.get("listeners"):
        owners = ", ".join(
            sorted({f"{entry['command']}:{entry['pid']}" for entry in daemon["listeners"]})
        )
        lines.append(
            f"local daemon/tunnel port: {daemon.get('host')}:{daemon.get('port')} (listening via {owners})"
        )
    else:
        lines.append(
            f"local daemon/tunnel port: {daemon.get('host')}:{daemon.get('port')} (not listening)"
        )

    remote_host = config.get("remote_host")
    jump_host = config.get("jump_host")
    if remote_host:
        remote_line = f"remote target: {remote_host}:{daemon.get('port')}"
        if jump_host:
            remote_line += f" via jump host {jump_host}"
        lines.append(remote_line)

    warm = service_state.get("warm_remote_session", {})
    warm_meta = warm.get("metadata", {}) if isinstance(warm, dict) else {}
    if warm_meta.get("persistent_shell_ready"):
        lines.append("persistent SSH shell: ready")

    diagnostics = (
        service_state.get("ensure_ready", {}).get("metadata", {}).get("diagnostics", {})
        if isinstance(service_state, dict)
        else {}
    )
    summary = diagnostics.get("summary")
    if summary:
        lines.append(f"daemon diagnostics: {summary}")
    return lines

def _condense_entries(entries: list[dict[str, Any]]) -> list[dict[str, Any]]:
    condensed: dict[tuple[Any, ...], dict[str, Any]] = {}
    for entry in entries:
        proc = entry.get("process") or {}
        key = (
            entry.get("command"),
            entry.get("pid"),
            entry.get("user"),
            entry.get("state"),
            proc.get("started_at"),
            proc.get("command"),
        )
        existing = condensed.get(key)
        if existing is None:
            condensed[key] = {
                **entry,
                "names": [entry.get("name")],
            }
            continue
        name = entry.get("name")
        if name not in existing["names"]:
            existing["names"].append(name)
    return list(condensed.values())

def _display_name(name: str) -> str:
    return name.replace("_", " ")

def _render_value(value: Any) -> str:
    rendered = "-" if value in (None, "", []) else str(value)
    return f"[{rendered}]"

def _format_single(key: str, value: Any) -> str:
    label = f"{_display_name(key)}:"
    return f"{label} {_render_value(value)}"

def _format_pair(left: tuple[str, Any], right: tuple[str, Any]) -> str:
    return f"{_format_single(left[0], left[1])}{_COLUMN_GAP}{_format_single(right[0], right[1])}"

def _is_short_pair(pair: tuple[str, Any]) -> bool:
    return len(_render_value(pair[1])) <= _SHORT_VALUE_WIDTH

def _format_pairs(*pairs: tuple[str, Any]) -> list[str]:
    lines: list[str] = []
    pending: tuple[str, Any] | None = None
    for pair in pairs:
        if pending is None:
            pending = pair
            continue
        if _is_short_pair(pending) and _is_short_pair(pair):
            lines.append(_format_pair(pending, pair))
            pending = None
            continue
        lines.append(_format_single(pending[0], pending[1]))
        pending = pair
    if pending is not None:
        lines.append(_format_single(pending[0], pending[1]))
    return lines

def _summarize_last_result(last_result: Any) -> str:
    if not isinstance(last_result, dict) or not last_result:
        return "-"

    if "test_connection" in last_result:
        return "test_connection: alive" if last_result.get("test_connection") else "test_connection: failed"

    status = last_result.get("status")
    output = str(last_result.get("output") or "").strip()
    errors = last_result.get("errors") or []

    parts: list[str] = []
    if status:
        parts.append(str(status))
    if output:
        compact = " ".join(output.split())
        parts.append(f"output={compact[:80]}")
    elif errors:
        first_error = " ".join(str(errors[0]).split())
        parts.append(f"error={first_error[:80]}")

    if not parts:
        compact = " ".join(json.dumps(last_result, ensure_ascii=False).split())
        return compact[:120]
    return " | ".join(parts)

def _separator(name: str) -> str:
    return "-" * _RULE_WIDTH

def _section_header(name: str, *, leading_blank: bool = True) -> list[str]:
    lines: list[str] = []
    if leading_blank:
        lines.append("")
    lines.append(_separator(name))
    lines.append(_render_value(_display_name(name)))
    return lines

def _build_tunnel_cmd(
    remote_host: str | None,
    remote_user: str | None,
    jump_host: str | None,
    jump_user: str | None,
    port: int,
) -> str | None:
    """Return the SSH tunnel command that would be run, as a string."""
    if not remote_host:
        return None
    cmd: list[str] = ["ssh", "-N", f"-L {port}:localhost:{port}"]
    if jump_host:
        effective_jump_user = jump_user or remote_user
        jump_target = f"{effective_jump_user}@{jump_host}" if effective_jump_user else jump_host
        cmd.append(f"-J {jump_target}")
    remote_target = f"{remote_user}@{remote_host}" if remote_user else remote_host
    cmd.append(remote_target)
    return " ".join(cmd)

def collect_runtime_status(*, load_env: bool = False) -> dict[str, Any]:
    """Collect a one-shot snapshot of local bridge-related runtime state."""
    if load_env:
        load_dotenv()
    service = BridgeService()
    ssh_env = remote_ssh_env_from_os()
    daemon_port = _rb_port()

    snapshot = {
        "captured_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "config": {
            "remote_host": ssh_env.remote_host,
            "remote_user": ssh_env.remote_user,
            "jump_host": ssh_env.jump_host,
            "jump_user": ssh_env.jump_user,
            "service_host": "127.0.0.1",
            "service_port": service.port,
            "daemon_host": _rb_host(),
            "daemon_port": daemon_port,
            "tunnel_cmd": _build_tunnel_cmd(
                ssh_env.remote_host,
                ssh_env.remote_user,
                ssh_env.jump_host,
                ssh_env.jump_user,
                daemon_port,
            ),
        },
        "service": _service_summary(service),
        "jump_host_ssh": _jump_host_summary(ssh_env.jump_host, ssh_env.jump_user, ssh_env.remote_user),
        "daemon_port": _daemon_summary(daemon_port),
        "port_usage": {
            "service_port": _port_usage_summary("127.0.0.1", service.port),
            "daemon_port": _port_usage_summary(_rb_host(), daemon_port),
        },
    }
    snapshot["connection_chain"] = _inferred_chain(
        snapshot["config"],
        snapshot["service"],
        snapshot["daemon_port"],
    )
    return snapshot

def format_runtime_status(snapshot: dict[str, Any]) -> str:
    """Render the runtime snapshot into a readable text report."""
    config = snapshot.get("config", {})
    service = snapshot.get("service", {})
    daemon = snapshot.get("daemon_port", {})
    jump_host_ssh = snapshot.get("jump_host_ssh", {})
    service_state = service.get("state") or {}
    service_process = service.get("process") or {}
    last_command_result = _summarize_last_result(service_state.get("last_result"))
    started_at = _format_epoch(service_state.get("started_at")) or service_process.get("started_at")
    state_path = service.get("state_path")
    log_path = Path(state_path).with_name("service.log") if state_path else "-"

    service_listeners = _condense_entries(service.get("listeners", []))
    service_owner = "-"
    service_listen = f"{config.get('service_host')}:{config.get('service_port')}"
    if service_listeners:
        first = service_listeners[0]
        service_owner = f"{first.get('command')} pid={first.get('pid')}"
        service_listen = " | ".join(first.get("names", [])) or first.get("name") or service_listen

    daemon_listeners = _condense_entries(daemon.get("listeners", []))
    daemon_owner = "-"
    daemon_started_at = "-"
    daemon_listen = f"{config.get('daemon_host')}:{config.get('daemon_port')}"
    if daemon_listeners:
        first = daemon_listeners[0]
        proc = first.get("process") or {}
        daemon_owner = f"{first.get('command')} pid={first.get('pid')}"
        daemon_started_at = proc.get("started_at") or "-"
        daemon_listen = " | ".join(first.get("names", [])) or first.get("name") or daemon_listen

    ensure_ready = (service_state.get("ensure_ready") or {}).get("metadata", {})
    diagnostics = ensure_ready.get("diagnostics", {}) if isinstance(ensure_ready, dict) else {}
    daemon_summary = diagnostics.get("summary") or "-"
    daemon_tcp = "reachable" if diagnostics.get("tcp_reachable") else "unreachable"
    daemon_ping = "ok" if diagnostics.get("daemon_responsive") else "no response"

    lines = [
        "=" * _RULE_WIDTH,
        *_format_pairs(("captured_at", snapshot.get("captured_at"))),
        *_section_header("ssh_path"),
    ]

    tunnel_cmd = config.get("tunnel_cmd")
    if tunnel_cmd:
        lines.append(f"[cmd] {tunnel_cmd}")

    if not jump_host_ssh.get("configured"):
        lines.extend(_format_pairs(("jump_host_ssh", "not configured")))
    else:
        ssh_cmd = jump_host_ssh.get("ssh_cmd")
        if ssh_cmd:
            lines.append(f"[cmd] {ssh_cmd}")
        elapsed = jump_host_ssh.get("elapsed")
        lines.extend(
            _format_pairs(
                ("jump_host_ssh", "reachable" if jump_host_ssh.get("reachable") else "failed"),
                ("jump_host_elapsed", f"{elapsed:.3f}s" if elapsed is not None else "-"),
            )
        )

    lines.extend(_section_header("local_bridge_service"))
    lines.extend(
        _format_pairs(
            ("status", service_state.get("status") or "not running"),
            ("pid", service_state.get("pid")),
            ("started_at", started_at),
            ("listen", service_listen),
            ("owner", service_owner),
            ("last_command_result", last_command_result),
            ("state_path", state_path),
            ("log_path", log_path),
        )
    )

    lines.extend(_section_header("local_ramic_tunnel"))
    lines.extend(
        _format_pairs(
            ("status", "listening" if daemon_listeners else "not listening"),
            ("owner", daemon_owner),
            ("started_at", daemon_started_at),
            ("listen", daemon_listen),
        )
    )

    lines.extend(_section_header("remote_ramic_daemon"))
    lines.extend(
        _format_pairs(
            ("remote_host", config.get("remote_host")),
            ("remote_user", config.get("remote_user")),
            ("local_tunnel_port", f"{config.get('daemon_host')}:{config.get('daemon_port')}"),
            ("tcp", daemon_tcp),
            ("daemon_ping", daemon_ping),
            ("summary", daemon_summary),
        )
    )
    lines.append("=" * _RULE_WIDTH)
    return "\n".join(lines)

