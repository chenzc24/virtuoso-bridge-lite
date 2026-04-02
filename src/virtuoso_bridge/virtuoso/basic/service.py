"""Background bridge service for persistent RAMIC sessions."""

from __future__ import annotations

import json
import logging
import os
import socket
import subprocess
import sys
import time
from pathlib import Path
from typing import Any

from virtuoso_bridge.virtuoso.basic.bridge import RAMICBridge
from virtuoso_bridge.models import VirtuosoResult

logger = logging.getLogger(__name__)

_SERVICE_HOST = "127.0.0.1"
def _default_local_port() -> int:
    from virtuoso_bridge.virtuoso.basic.bridge import _default_remote_port
    raw = os.environ.get("VB_LOCAL_PORT", "").strip()
    if raw:
        try:
            return int(raw)
        except ValueError:
            pass
    return _default_remote_port() + 1

_DEFAULT_PORT = _default_local_port()
_DEFAULT_STATE_DIR = Path.home() / ".cache" / "virtuoso_bridge"
_SERVICE_NAME = "virtuoso_bridge"
_PROTOCOL_VERSION = 1
_CAPABILITIES = (
    "status",
    "warm_remote_session",
    "ensure_ready",
    "test_connection",
    "open_cell_view",
    "open_window",
    "save_current_cellview",
    "close_current_cellview",
    "run_il_file",
    "clear_current_layout",
    "execute_operations",
    "execute_skill",
    "load_il",
    "upload_file",
    "download_file",
    "ciw_print",
    "ciw_log",
    "stop",
)

def _write_state_file(path: Path, state: dict[str, Any]) -> None:
    """Write state JSON atomically to avoid readers seeing partial content."""
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp_path = path.with_suffix(path.suffix + ".tmp")
    tmp_path.write_text(json.dumps(state, indent=2), encoding="utf-8")
    tmp_path.replace(path)

def _result_to_dict(result: VirtuosoResult) -> dict[str, Any]:
    return result.model_dump(mode="json")

def _status_payload(state: dict[str, Any]) -> dict[str, Any]:
    """Build the public status response for this service."""
    return {
        "ok": True,
        "service": _SERVICE_NAME,
        "protocol_version": _PROTOCOL_VERSION,
        "capabilities": list(_CAPABILITIES),
        "service_state": state,
    }

def _is_compatible_status_response(response: dict[str, Any] | None) -> bool:
    """Whether a status response belongs to this service implementation."""
    if not response or not response.get("ok"):
        return False
    return (
        response.get("service") == _SERVICE_NAME
        and response.get("protocol_version") == _PROTOCOL_VERSION
    )

def _update_health_from_result(
    state: dict[str, Any],
    result: VirtuosoResult,
    *,
    healthy_status: str = "running",
    degraded_status: str = "degraded",
) -> None:
    """Reflect the latest bridge result in the persisted service state."""
    state["last_result"] = _result_to_dict(result)
    if result.ok:
        state["status"] = healthy_status
        state.pop("degraded_reason", None)
        state.pop("error", None)
        return

    state["status"] = degraded_status
    state["degraded_reason"] = list(result.errors) or ["bridge result indicated failure"]

def _dispatch(
    request: dict[str, Any],
    bridge: RAMICBridge,
    state: dict[str, Any],
) -> tuple[dict[str, Any], bool]:
    """Route an incoming request to the appropriate bridge method."""
    op = request.get("op", "").strip()
    timeout = int(request.get("timeout", 10))

    if op == "status":
        state["last_seen"] = time.time()
        return _status_payload(state), False

    if op == "warm_remote_session":
        result = bridge.warm_remote_session(timeout=timeout)
        state["last_result"] = _result_to_dict(result)
        return {"ok": True, "result": _result_to_dict(result)}, False

    if op == "ensure_ready":
        result = bridge.ensure_ready(timeout=timeout)
        _update_health_from_result(state, result)
        return {"ok": True, "result": _result_to_dict(result)}, False

    if op == "test_connection":
        alive = bridge.test_connection(timeout=timeout)
        state["last_result"] = {"test_connection": alive}
        if alive:
            state["status"] = "running"
            state.pop("degraded_reason", None)
            state.pop("error", None)
        else:
            state["status"] = "degraded"
            state["degraded_reason"] = ["Daemon ping failed"]
        return {"ok": True, "alive": alive}, False

    if op == "execute_skill":
        skill = request.get("skill", "")
        result = bridge.execute_skill(skill, timeout=timeout)
        _update_health_from_result(state, result)
        return {"ok": True, "result": _result_to_dict(result)}, False

    if op == "open_cell_view":
        result = bridge.open_cell_view(
            request.get("lib", ""),
            request.get("cell", ""),
            view=request.get("view", "layout"),
            view_type=request.get("view_type"),
            mode=request.get("mode", "w"),
            timeout=timeout,
        )
        _update_health_from_result(state, result)
        return {"ok": True, "result": _result_to_dict(result)}, False

    if op == "open_window":
        result = bridge.open_window(
            request.get("lib", ""),
            request.get("cell", ""),
            view=request.get("view", "layout"),
            view_type=request.get("view_type"),
            mode=request.get("mode", "a"),
            timeout=timeout,
        )
        _update_health_from_result(state, result)
        return {"ok": True, "result": _result_to_dict(result)}, False

    if op == "save_current_cellview":
        result = bridge.save_current_cellview(timeout=timeout)
        _update_health_from_result(state, result)
        return {"ok": True, "result": _result_to_dict(result)}, False

    if op == "close_current_cellview":
        result = bridge.close_current_cellview(timeout=timeout)
        _update_health_from_result(state, result)
        return {"ok": True, "result": _result_to_dict(result)}, False

    if op == "get_current_design":
        lib, cell, view = bridge.get_current_design(timeout=timeout)
        state["last_result"] = {
            "get_current_design": {"lib": lib, "cell": cell, "view": view}
        }
        return {"ok": True, "lib": lib, "cell": cell, "view": view}, False

    if op == "run_il_file":
        result = bridge.run_il_file(
            request.get("path", ""),
            request.get("lib", ""),
            request.get("cell", ""),
            view=request.get("view", "layout"),
            view_type=request.get("view_type"),
            mode=request.get("mode", "w"),
            open_window=bool(request.get("open_window", True)),
            save=bool(request.get("save", False)),
            timeout=timeout,
        )
        _update_health_from_result(state, result)
        return {"ok": True, "result": _result_to_dict(result)}, False

    if op == "clear_current_layout":
        result = bridge.layout.clear_current(timeout=timeout)
        _update_health_from_result(state, result)
        return {"ok": True, "result": _result_to_dict(result)}, False

    if op == "execute_operations":
        commands = request.get("commands", [])
        result = bridge.execute_operations(
            list(commands) if isinstance(commands, list) else [],
            timeout=timeout,
            wrap_in_progn=bool(request.get("wrap_in_progn", True)),
        )
        _update_health_from_result(state, result)
        return {"ok": True, "result": _result_to_dict(result)}, False

    if op == "load_il":
        path = request.get("path")
        result = bridge.load_il(path, timeout=timeout)
        _update_health_from_result(state, result)
        return {"ok": True, "result": _result_to_dict(result)}, False

    if op == "run_shell_command":
        cmd = request.get("cmd", "")
        result = bridge.run_shell_command(cmd, timeout=timeout)
        _update_health_from_result(state, result)
        return {"ok": True, "result": _result_to_dict(result)}, False

    if op == "download_file":
        result = bridge.download_file(
            request.get("remote_path", ""),
            request.get("local_path", ""),
            timeout=timeout,
        )
        _update_health_from_result(state, result)
        return {"ok": True, "result": _result_to_dict(result)}, False

    if op == "upload_file":
        result = bridge.upload_file(
            request.get("local_path", ""),
            request.get("remote_path", ""),
            timeout=timeout,
        )
        _update_health_from_result(state, result)
        return {"ok": True, "result": _result_to_dict(result)}, False

    if op == "ciw_print":
        message = request.get("message", "")
        result = bridge.ciw_print(message, timeout=timeout)
        _update_health_from_result(state, result)
        return {"ok": True, "result": _result_to_dict(result)}, False

    if op == "ciw_log":
        skill = request.get("skill", "")
        result = bridge.ciw_log(skill, timeout=timeout)
        _update_health_from_result(state, result)
        return {"ok": True, "result": _result_to_dict(result)}, False

    if op == "stop":
        state["stopping"] = True
        return {"ok": True, "message": "bridge service stopping"}, True

    return {"ok": False, "error": f"Unknown op: {op!r}"}, False

def _serve_forever(port: int, state_path: Path) -> None:
    """Run the service loop (called in the background process)."""
    state_path.parent.mkdir(parents=True, exist_ok=True)
    service_state: dict[str, Any] = {
        "service": _SERVICE_NAME,
        "protocol_version": _PROTOCOL_VERSION,
        "capabilities": list(_CAPABILITIES),
        "status": "starting",
        "pid": os.getpid(),
        "port": port,
        "host": _SERVICE_HOST,
        "state_path": str(state_path),
        "started_at": time.time(),
    }
    _write_state_file(state_path, service_state)

    bridge = RAMICBridge.from_env(keep_remote_files=True)
    try:
        warm = bridge.warm_remote_session(timeout=15)
        service_state["warm_remote_session"] = _result_to_dict(warm)
        if warm.status.value != "success":
            service_state["status"] = "error"
            _write_state_file(state_path, service_state)
            return

        ready = bridge.ensure_ready(timeout=15)
        service_state["ensure_ready"] = _result_to_dict(ready)

        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as server:
            server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            server.bind((_SERVICE_HOST, port))
            server.listen(5)
            server.settimeout(1.0)

            if ready.ok:
                service_state["status"] = "running"
                service_state.pop("degraded_reason", None)
            else:
                service_state["status"] = "degraded"
                service_state["degraded_reason"] = ready.errors
            _write_state_file(state_path, service_state)

            stop_requested = False
            while not stop_requested:
                try:
                    conn, _addr = server.accept()
                except socket.timeout:
                    continue

                with conn:
                    chunks: list[bytes] = []
                    while True:
                        data = conn.recv(65536)
                        if not data:
                            break
                        chunks.append(data)
                    if not chunks:
                        continue
                    try:
                        request = json.loads(b"".join(chunks).decode("utf-8"))
                        response, stop_requested = _dispatch(request, bridge, service_state)
                        _write_state_file(state_path, service_state)
                    except Exception as exc:  # noqa: BLE001
                        response = {"ok": False, "error": str(exc)}
                    conn.sendall(json.dumps(response).encode("utf-8"))
    finally:
        bridge.close()
        service_state["status"] = "stopped"
        service_state["stopped_at"] = time.time()
        _write_state_file(state_path, service_state)

class BridgeService:
    """Manager for a background bridge service process."""

    def __init__(
        self,
        port: int = _DEFAULT_PORT,
        state_dir: Path | None = None,
    ) -> None:
        self.port = port
        self._state_dir = Path(state_dir) if state_dir else _DEFAULT_STATE_DIR
        self._state_path = self._state_dir / "state.json"
        self._log_path = self._state_dir / "service.log"

    @property
    def state_path(self) -> Path:
        """Path to the service state JSON file."""
        return self._state_path

    def is_running(self) -> bool:
        """Check whether the service is alive and the bridge is usable."""
        try:
            resp = self._probe_status()
            if not _is_compatible_status_response(resp):
                return False
            state = resp.get("service_state", {})
            return state.get("status") == "running"
        except OSError:
            return False

    def is_alive(self) -> bool:
        """Check whether the service process is accepting connections (even if degraded)."""
        try:
            return _is_compatible_status_response(self._probe_status())
        except OSError:
            return False

    def read_state(self) -> dict[str, Any] | None:
        """Read the last written state from the state file."""
        if not self._state_path.is_file():
            return None
        try:
            return json.loads(self._state_path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            return None

    def start(self, wait: float = 8.0) -> dict[str, Any] | None:
        """Spawn the service as a background process and wait for it to be ready."""
        probe = self._probe_status()
        if _is_compatible_status_response(probe):
            logger.info("Bridge service already running at %s:%d", _SERVICE_HOST, self.port)
            return self.read_state() or probe.get("service_state")
        if probe is not None:
            error_state = {
                "service": _SERVICE_NAME,
                "protocol_version": _PROTOCOL_VERSION,
                "status": "error",
                "port": self.port,
                "host": _SERVICE_HOST,
                "error": (
                    f"Port {self.port} is occupied by an incompatible service. "
                    "Stop the old service or choose a different VB_LOCAL_PORT."
                ),
            }
            self._state_dir.mkdir(parents=True, exist_ok=True)
            _write_state_file(self._state_path, error_state)
            return error_state

        self._state_dir.mkdir(parents=True, exist_ok=True)
        cmd = [
            sys.executable, "-c",
            f"from virtuoso_bridge.virtuoso.basic.service import _serve_forever; "
            f"from pathlib import Path; "
            f"_serve_forever({self.port}, Path({str(self._state_path)!r}))",
        ]
        log_f = self._log_path.open("ab")
        kwargs: dict[str, Any] = {
            "stdin": subprocess.DEVNULL,
            "stdout": log_f,
            "stderr": log_f,
            "close_fds": True,
        }
        if os.name == "nt":
            kwargs["creationflags"] = (
                subprocess.DETACHED_PROCESS | subprocess.CREATE_NEW_PROCESS_GROUP
            )
        else:
            kwargs["start_new_session"] = True
        proc = subprocess.Popen(cmd, **kwargs)
        logger.info("Spawned bridge service PID %d at %s:%d", proc.pid, _SERVICE_HOST, self.port)
        return self._wait_for_state(timeout=wait, expected_pid=proc.pid)

    def stop(self) -> None:
        """Send a stop request to the running service."""
        try:
            _send_request({"op": "stop"}, host=_SERVICE_HOST, port=self.port, timeout=2.0)
        except OSError:
            pass

    def _wait_for_state(self, timeout: float = 8.0, expected_pid: int | None = None) -> dict[str, Any] | None:
        deadline = time.monotonic() + timeout
        while time.monotonic() < deadline:
            probe = self._probe_status()
            if _is_compatible_status_response(probe):
                state = probe.get("service_state") or {}
                if state.get("status") in {"running", "degraded", "error"}:
                    return state
            state = self.read_state()
            if state and state.get("port") == self.port and state.get("status") in {"error", "stopped"}:
                if expected_pid is None or state.get("pid") == expected_pid:
                    return state
            time.sleep(0.2)
        probe = self._probe_status()
        if _is_compatible_status_response(probe):
            return probe.get("service_state")
        return self.read_state()

    def _probe_status(self) -> dict[str, Any] | None:
        """Probe the configured port for a status response."""
        try:
            return _send_request({"op": "status"}, host=_SERVICE_HOST, port=self.port, timeout=1.0)
        except (OSError, json.JSONDecodeError, RuntimeError):
            return None

def _send_request(
    request: dict[str, Any],
    *,
    host: str,
    port: int,
    timeout: float = 5.0,
) -> dict[str, Any]:
    with socket.create_connection((host, port), timeout=timeout) as sock:
        sock.sendall(json.dumps(request).encode("utf-8"))
        sock.shutdown(socket.SHUT_WR)
        chunks: list[bytes] = []
        while True:
            data = sock.recv(65536)
            if not data:
                break
            chunks.append(data)
    return json.loads(b"".join(chunks).decode("utf-8"))
