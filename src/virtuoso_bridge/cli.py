"""CLI entry points for common bridge workflows."""

from __future__ import annotations

import argparse
import os
import re
import threading
import time
from datetime import datetime
from pathlib import Path

from dotenv import load_dotenv

from virtuoso_bridge import BridgeClient, BridgeService
from virtuoso_bridge.transport.remote_paths import (
    default_virtuoso_bridge_dir,
    resolve_remote_username,
)
from virtuoso_bridge.transport.ssh import SSHRunner, remote_ssh_env_from_os
from virtuoso_bridge.virtuoso.basic.runtime_status import (
    collect_runtime_status,
    format_runtime_status,
)

def _env_template_path() -> Path:
    return Path(__file__).with_name("resources") / ".env_template"

def _generate_env_template() -> str:
    import getpass
    from virtuoso_bridge.virtuoso.basic.bridge import _default_remote_port
    try:
        username = getpass.getuser()
    except Exception:  # noqa: BLE001
        username = ""
    remote_port = _default_remote_port(username)
    local_port = remote_port + 1
    template = _env_template_path().read_text(encoding="utf-8")
    return template.format(remote_port=remote_port, local_port=local_port)

_SETUP_LOAD_RE = re.compile(r'load\("([^"]+/virtuoso_setup\.il)"\)')

def _is_virtuoso_bridge_project(pyproject: Path) -> bool:
    try:
        head = pyproject.read_text(encoding="utf-8")[:4000]
    except OSError:
        return False
    return 'name = "virtuoso-bridge"' in head

def _repo_root() -> Path:
    """Directory containing ``virtuoso-bridge``'s ``pyproject.toml`` (for ``.env`` and paths)."""
    raw = os.environ.get("VIRTUOSO_BRIDGE_ROOT", "").strip()
    if raw:
        p = Path(raw).expanduser().resolve()
        if _is_virtuoso_bridge_project(p / "pyproject.toml"):
            return p
    here = Path(__file__).resolve()
    for parent in here.parents:
        pm = parent / "pyproject.toml"
        if pm.is_file() and _is_virtuoso_bridge_project(pm):
            return parent
    cwd = Path.cwd()
    nested = cwd / "virtuoso-bridge" / "pyproject.toml"
    if nested.is_file() and _is_virtuoso_bridge_project(nested):
        return nested.parent
    root_pm = cwd / "pyproject.toml"
    if root_pm.is_file() and _is_virtuoso_bridge_project(root_pm):
        return cwd
    raise RuntimeError(
        "Could not locate virtuoso-bridge project root (pyproject.toml). "
        "Run this command from the repo that contains virtuoso-bridge/, or set "
        "VIRTUOSO_BRIDGE_ROOT to that directory."
    )

def _load_repo_env() -> None:
    vb_env = _repo_root() / ".env"
    if vb_env.is_file():
        load_dotenv(vb_env, override=True)

def _format_elapsed(seconds: float) -> str:
    return f"{seconds:.3f}s"

def _timed_call(func):
    started = time.monotonic()
    result = func()
    return time.monotonic() - started, result

def _print_elapsed(label: str, elapsed: float) -> None:
    print(f"{label} = {_format_elapsed(elapsed)}")

def _print_init_next_steps(env_path: Path, created: bool) -> None:
    status = "created" if created else "kept existing"
    print(f".env: {status} at {env_path}")
    print()
    print("Next steps:")
    print("1. Make sure plain SSH already works with your existing keys and ~/.ssh/config.")
    print("2. Edit .env and set VB_REMOTE_HOST to the SSH host alias you already use in the shell.")
    print("3. Set VB_JUMP_HOST only if your SSH path uses a jump / bastion host.")
    print("4. Run: virtuoso-bridge start")
    print("5. If start reports degraded, load the generated remote virtuoso_setup.il in Virtuoso CIW.")
    print("6. Run: virtuoso-bridge status")
    print("7. Then try: python examples/bridge_client.py")

def cli_init() -> int:
    env_path = _repo_root() / ".env"
    if env_path.exists():
        _print_init_next_steps(env_path, created=False)
        return 0
    env_path.write_text(_generate_env_template(), encoding="utf-8")
    _print_init_next_steps(env_path, created=True)
    return 0

def _require_remote_host() -> bool:
    _load_repo_env()
    if os.getenv("VB_REMOTE_HOST"):
        return True
    print("VB_REMOTE_HOST is not set.")
    print("Run: virtuoso-bridge init")
    print("Then edit .env and rerun the command.")
    return False

def _tail_cmd_lines(
    log_path: Path,
    stop_event: threading.Event,
    start_offset: int,
) -> None:
    """Background thread: tail log_path and print [cmd] lines in real time."""
    offset = start_offset
    while not stop_event.is_set():
        try:
            with open(log_path, "r", encoding="utf-8", errors="replace") as f:
                f.seek(offset)
                while True:
                    line = f.readline()
                    if not line:
                        break
                    stripped = line.rstrip()
                    if stripped.startswith("[cmd]"):
                        print(stripped, flush=True)
                    offset = f.tell()
        except OSError:
            pass
        stop_event.wait(timeout=0.1)

def _find_setup_load_hint(log_path: Path) -> str | None:
    if not log_path.is_file():
        return None
    try:
        text = log_path.read_text(encoding="utf-8", errors="replace")
    except OSError:
        return None
    matches = _SETUP_LOAD_RE.findall(text)
    return matches[-1] if matches else None

def _default_setup_load_path() -> str:
    u = resolve_remote_username(configured_user=os.getenv("VB_REMOTE_USER"), runner=None)
    base = default_virtuoso_bridge_dir(u, "virtuoso_bridge")
    return f"{base}/virtuoso_setup.il"

def _print_recovery_hint(service: BridgeService) -> None:
    setup_path = _find_setup_load_hint(service._log_path)
    print("[next step]")
    if setup_path:
        print(f'[ciw] load("{setup_path}")')
    else:
        print(f'[ciw] load("{_default_setup_load_path()}")')
    print("[then] virtuoso-bridge status")

def _jump_host_precheck() -> tuple[int | None, dict[str, str] | None]:
    _load_repo_env()
    ssh_env = remote_ssh_env_from_os()
    if not ssh_env.jump_host:
        return None, None

    effective_user = ssh_env.jump_user or ssh_env.remote_user
    started = time.monotonic()
    runner = SSHRunner(
        host=ssh_env.jump_host,
        user=effective_user,
        connect_timeout=2,
        persistent_shell=False,
    )
    ssh_cmd = " ".join(runner._build_ssh_base() + ["-T", "exit", "0"])
    reachable = runner.test_connection(timeout=2)
    elapsed = time.monotonic() - started
    details = {
        "target": f"{effective_user}@{ssh_env.jump_host}" if effective_user else ssh_env.jump_host,
        "status": "reachable" if reachable else "failed",
        "elapsed": _format_elapsed(elapsed),
        "ssh_cmd": ssh_cmd,
    }
    if not reachable:
        print("------------------------------------------------------------------------")
        print("ssh check")
        print(f"[cmd] {ssh_cmd}")
        print(f"jump host ssh: [{details['status']}]")
        print(f"jump host elapsed: [{details['elapsed']}]")
        print()
        print("SSH to the jump host failed.")
        print("Fix the SSH path first, then rerun: virtuoso-bridge status")
        return 1, details
    return None, details

def _remote_host_precheck() -> tuple[int | None, dict[str, str] | None]:
    _load_repo_env()
    ssh_env = remote_ssh_env_from_os()
    if not ssh_env.remote_host:
        return None, None

    target = ssh_env.remote_host
    if ssh_env.remote_user:
        target = f"{ssh_env.remote_user}@{target}"

    effective_jump_user = ssh_env.jump_user or ssh_env.remote_user
    started = time.monotonic()
    runner = SSHRunner(
        host=ssh_env.remote_host,
        user=ssh_env.remote_user,
        jump_host=ssh_env.jump_host,
        jump_user=effective_jump_user,
        connect_timeout=2,
        persistent_shell=False,
    )
    ssh_cmd = " ".join(runner._build_ssh_base() + ["-T", "exit", "0"])
    reachable = runner.test_connection(timeout=2)
    elapsed = time.monotonic() - started
    details = {
        "target": target,
        "status": "reachable" if reachable else "failed",
        "elapsed": _format_elapsed(elapsed),
        "ssh_cmd": ssh_cmd,
    }
    if not reachable:
        print("------------------------------------------------------------------------")
        print("ssh check")
        print(f"[cmd] {ssh_cmd}")
        print(f"remote host ssh: [{details['status']}]")
        print(f"remote host elapsed: [{details['elapsed']}]")
        print()
        print("SSH to the remote host failed.")
        print("Check VB_REMOTE_HOST, VB_REMOTE_USER, VB_JUMP_HOST, and VB_JUMP_USER.")
        print("Fix the SSH path first, then rerun: virtuoso-bridge start")
        return 1, details
    return None, details

def _ssh_path_precheck() -> int | None:
    precheck, _details = _jump_host_precheck()
    if precheck is not None:
        return precheck
    precheck, _details = _remote_host_precheck()
    if precheck is not None:
        return precheck
    return None

def _terminate_pid(pid: int) -> None:
    import signal

    try:
        os.kill(pid, signal.SIGTERM)
    except OSError:
        return

def _cleanup_stale_local_processes() -> None:
    snapshot = collect_runtime_status(load_env=True)
    service_state = ((snapshot.get("service") or {}).get("state") or {}).get("status")
    if service_state == "running":
        return

    stale_pids: list[int] = []
    for entry in (snapshot.get("service") or {}).get("listeners", []):
        pid = entry.get("pid")
        if isinstance(pid, int):
            stale_pids.append(pid)
    for entry in (snapshot.get("daemon_port") or {}).get("listeners", []):
        pid = entry.get("pid")
        if isinstance(pid, int):
            stale_pids.append(pid)

    seen: set[int] = set()
    for pid in stale_pids:
        if pid in seen:
            continue
        seen.add(pid)
        _terminate_pid(pid)

def _safe_service_test() -> tuple[bool, str | None, float]:
    deadline = time.monotonic() + 2.5
    last_error: str | None = None
    started = time.monotonic()
    while True:
        try:
            response = BridgeClient().test_connection(timeout=2)
        except Exception as exc:  # noqa: BLE001
            last_error = str(exc)
        else:
            if not response.get("ok"):
                last_error = str(response.get("error") or "request failed")
            else:
                alive = bool(response.get("alive"))
                elapsed = time.monotonic() - started
                if alive:
                    return True, None, elapsed
                last_error = "service reported test_connection = False"
        if time.monotonic() >= deadline:
            return False, last_error, time.monotonic() - started
        time.sleep(0.1)

def _print_service_state(service: BridgeService, state: dict | None) -> int:
    state = state or {}
    status = state.get("status") or "unknown"

    if status == "running":
        print("[virtuoso bridge] service status: running")
        ok, error, elapsed = _safe_service_test()
        _print_elapsed("client.test_connection", elapsed)
        if ok:
            print("[virtuoso bridge] service process is running and the Virtuoso/RAMIC path is usable")
            return 0
        print(f"[virtuoso bridge] service process is running, but the Virtuoso/RAMIC path is not usable: {error}")
        return 1

    reasons = state.get("degraded_reason") or state.get("errors") or []
    if status == "degraded":
        ok, error, elapsed = _safe_service_test()
        _print_elapsed("client.test_connection", elapsed)
        if ok:
            print("[virtuoso bridge] service status: running")
            print("[virtuoso bridge] service process is running and the Virtuoso/RAMIC path is usable")
            return 0
        print("[virtuoso bridge] service status: degraded")
        print("[virtuoso bridge] service process is running, but the Virtuoso/RAMIC path is not usable")
        if reasons:
            print(f"[virtuoso bridge] reason: {reasons[0]}")
        elif error:
            print(f"[virtuoso bridge] reason: {error}")
        _print_recovery_hint(service)
        return 1

    if status == "error":
        print("[virtuoso bridge] service status: error")
        error = state.get("error")
        if error:
            print(f"[virtuoso bridge] error: {error}")
        print(f"Log: {service._log_path}")
        return 1

    if status == "stopped":
        print("[virtuoso bridge] service status: stopped")
        print("[virtuoso bridge] service process exited before the Virtuoso/RAMIC path became usable")
        print(f"Log: {service._log_path}")
        _print_recovery_hint(service)
        return 1

    print(f"[virtuoso bridge] service status: {status}")
    print(f"Log: {service._log_path}")
    return 1

def cli_start() -> int:
    if not _require_remote_host():
        return 1
    precheck = _ssh_path_precheck()
    if precheck is not None:
        return precheck

    service = BridgeService()
    _alive_elapsed, alive = _timed_call(service.is_alive)

    if alive:
        print("Service already running.")
        state = service.read_state()
        return _print_service_state(service, state)

    _cleanup_stale_local_processes()
    _cleanup_stale_local_processes()
    return _start_service(service)

def _start_service(service: BridgeService) -> int:
    """Start service with log tailing. Shared by cli_start and cli_restart."""
    print("Starting bridge service...")
    _log_offset = service._log_path.stat().st_size if service._log_path.is_file() else 0
    _stop_tail = threading.Event()
    _tail = threading.Thread(target=_tail_cmd_lines, args=(service._log_path, _stop_tail, _log_offset), daemon=True)
    _tail.start()
    start_elapsed, state = _timed_call(lambda: service.start(wait=15.0))
    _stop_tail.set()
    _tail.join(timeout=1.0)
    _print_elapsed("service.start", start_elapsed)
    if not state:
        print("Service did not become ready in time.")
        print(f"Log: {service._log_path}")
        return 1
    return _print_service_state(service, state)

def cli_restart() -> int:
    if not _require_remote_host():
        return 1
    precheck = _ssh_path_precheck()
    if precheck is not None:
        return precheck
    service = BridgeService()
    if service.is_alive():
        print("Stopping bridge service...")
        stop_elapsed, _ = _timed_call(service.stop)
        _print_elapsed("service.stop", stop_elapsed)
        deadline = time.monotonic() + 10.0
        while time.monotonic() < deadline:
            if not service.is_alive():
                break
            time.sleep(0.2)
        if service.is_alive():
            print("Service did not stop in time.")
            return 1
    else:
        print("Service is not running. Starting a fresh instance.")
    return _start_service(service)

def _service_running(snapshot: dict) -> bool:
    state = ((snapshot.get("service") or {}).get("state") or {})
    return state.get("status") in {"running", "degraded", "starting"}

def cli_status() -> int:
    snapshot = collect_runtime_status(load_env=True)
    service_state = ((snapshot.get("service") or {}).get("state") or {})
    service_status = service_state.get("status")
    if service_status in {"starting", "degraded"}:
        _safe_service_test()
        snapshot = collect_runtime_status(load_env=True)
        service_state = ((snapshot.get("service") or {}).get("state") or {})
        service_status = service_state.get("status")
    print(format_runtime_status(snapshot))

    if service_status in {"degraded", "error", "stopped", None}:
        if service_status in {"degraded", "error"}:
            print()
            _print_recovery_hint(BridgeService())
        return 1

    if _service_running(snapshot):
        message = f"[check_status] CIW ping at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
        elapsed, response = _timed_call(lambda: BridgeClient().ciw_print(message, timeout=5))
        print()
        print(f"[ciw_print] elapsed: {_format_elapsed(elapsed)}")
        if not response.get("ok"):
            print(f"[ciw_print] warning: request failed: {response.get('error')}")
            return 0
        result = response.get("result", {})
        status = result.get("status")
        if status != "success":
            print(f"[ciw_print] warning: {result.get('errors')}")
            return 0
        print("[ciw_print] success")
    return 0

def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="virtuoso-bridge")
    subparsers = parser.add_subparsers(dest="command", required=True)
    subparsers.add_parser("init", help="Create a starter .env and print next steps")
    subparsers.add_parser("start", help="Start the shared bridge service if needed")
    subparsers.add_parser("restart", help="Force-restart the shared bridge service")
    subparsers.add_parser("status", help="Print bridge runtime status and CIW ping")
    return parser

def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    if args.command == "init":
        return cli_init()
    if args.command == "start":
        return cli_start()
    if args.command == "restart":
        return cli_restart()
    if args.command == "status":
        return cli_status()
    parser.error(f"Unknown command: {args.command}")
    return 2
