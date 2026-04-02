"""High-level client for the background bridge service."""

from __future__ import annotations

import json
import os
import socket
import time
from pathlib import Path
from typing import Any

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
from virtuoso_bridge.virtuoso.layout import LayoutOps, parse_layout_geometry_output as _parse_layout_geometry_output
from virtuoso_bridge.virtuoso.schematic import SchematicOps

_DEFAULT_STATE_PATH = Path.home() / ".cache" / "virtuoso_bridge" / "state.json"

class BridgeClient:
    """High-level client for the background bridge service."""

    def __init__(
        self,
        port: int | None = None,
        state_path: Path | None = None,
    ) -> None:
        self._state_path = state_path or _DEFAULT_STATE_PATH
        self.port = port or self._read_state_port()
        self.layout = LayoutOps(self)
        self.schematic = SchematicOps(self)

    def _read_state_port(self) -> int:
        if self._state_path.is_file():
            try:
                state = json.loads(self._state_path.read_text(encoding="utf-8"))
                p = state.get("port")
                if isinstance(p, int):
                    return p
            except (OSError, json.JSONDecodeError):
                pass
        return _DEFAULT_PORT

    def _send(self, request: dict[str, Any], *, timeout: float = 10.0) -> dict[str, Any]:
        try:
            with socket.create_connection((_SERVICE_HOST, self.port), timeout=timeout) as sock:
                sock.sendall(json.dumps(request).encode("utf-8"))
                sock.shutdown(socket.SHUT_WR)
                chunks: list[bytes] = []
                while True:
                    data = sock.recv(65536)
                    if not data:
                        break
                    chunks.append(data)
        except OSError as exc:
            raise RuntimeError(
                f"Cannot reach bridge service at {_SERVICE_HOST}:{self.port}. "
                "Start it with BridgeService().start() first."
            ) from exc
        return json.loads(b"".join(chunks).decode("utf-8"))

    def _request(self, op: str, *, timeout: int = 10, **payload: Any) -> dict[str, Any]:
        request = {"op": op, "timeout": timeout, **payload}
        start = time.monotonic()
        response = self._send(request, timeout=max(10.0, timeout + 2))
        response["_elapsed"] = time.monotonic() - start
        return response

    def status(self) -> dict[str, Any]:
        """Check whether the service is alive."""
        return self._request("status", timeout=2)

    def ensure_ready(self, timeout: int = 10) -> dict[str, Any]:
        """Ask the service to ensure the bridge is ready."""
        return self._request("ensure_ready", timeout=timeout)

    def warm_remote_session(self, timeout: int = 15) -> dict[str, Any]:
        """Ask the service to warm up remote SSH transports."""
        return self._request("warm_remote_session", timeout=timeout)

    def test_connection(self, timeout: int = 10) -> dict[str, Any]:
        """Ask the service to test daemon connectivity."""
        return self._request("test_connection", timeout=timeout)

    def execute_skill(self, skill_code: str, timeout: int = 30) -> dict[str, Any]:
        """Execute SKILL code via the service."""
        return self._request("execute_skill", skill=skill_code, timeout=timeout)

    def open_cell_view(
        self,
        lib: str,
        cell: str,
        *,
        view: str = "layout",
        view_type: str | None = None,
        mode: str = "w",
        timeout: int = 30,
    ) -> dict[str, Any]:
        """Open a target cellview and bind it to ``cv`` in the service session."""
        return self._request(
            "open_cell_view",
            lib=lib,
            cell=cell,
            view=view,
            view_type=view_type,
            mode=mode,
            timeout=timeout,
        )

    def open_window(
        self,
        lib: str,
        cell: str,
        *,
        view: str = "layout",
        view_type: str | None = None,
        mode: str = "a",
        timeout: int = 30,
    ) -> dict[str, Any]:
        """Open a Virtuoso window for a target cellview."""
        return self._request(
            "open_window",
            lib=lib,
            cell=cell,
            view=view,
            view_type=view_type,
            mode=mode,
            timeout=timeout,
        )

    def load_il(self, path: str | Path, timeout: int = 20) -> dict[str, Any]:
        """Load an IL file in Virtuoso via the service."""
        return self._request("load_il", path=str(Path(path).resolve()), timeout=timeout)

    def save_current_cellview(self, timeout: int = 30) -> dict[str, Any]:
        """Save the current edit cellview held by the service session."""
        return self._request("save_current_cellview", timeout=timeout)

    def close_current_cellview(self, timeout: int = 30) -> dict[str, Any]:
        """Close the current edit cellview held by the service session."""
        return self._request("close_current_cellview", timeout=timeout)

    def get_current_design(
        self, timeout: int = 10
    ) -> tuple[str | None, str | None, str | None]:
        """Return ``(lib, cell, view)`` for the active edit cellview."""
        response = self._request("get_current_design", timeout=timeout)
        if not response.get("ok"):
            return None, None, None
        return response.get("lib"), response.get("cell"), response.get("view")

    def run_il_file(
        self,
        path: str | Path,
        lib: str,
        cell: str,
        *,
        view: str = "layout",
        view_type: str | None = None,
        mode: str = "w",
        open_window: bool = True,
        save: bool = False,
        timeout: int = 60,
    ) -> dict[str, Any]:
        """Open a target cellview, load an IL file, and optionally save it."""
        return self._request(
            "run_il_file",
            path=str(Path(path).resolve()),
            lib=lib,
            cell=cell,
            view=view,
            view_type=view_type,
            mode=mode,
            open_window=open_window,
            save=save,
            timeout=timeout,
        )

    def execute_operations(
        self,
        commands: list[str],
        *,
        timeout: int = 60,
        wrap_in_progn: bool = True,
    ) -> dict[str, Any]:
        """Compose and execute a batch of atomic SKILL operations."""
        return self._request(
            "execute_operations",
            commands=commands,
            wrap_in_progn=wrap_in_progn,
            timeout=timeout,
        )

    def run_shell_command(self, cmd: str, timeout: int = 30) -> dict[str, Any]:
        """Run a shell command on the Virtuoso host via the service."""
        return self._request("run_shell_command", cmd=cmd, timeout=timeout)

    def download_file(
        self,
        remote_path: str | Path,
        local_path: str | Path,
        timeout: int = 30,
    ) -> dict[str, Any]:
        """Download a file from the Virtuoso host to a local path via the service."""
        return self._request(
            "download_file",
            remote_path=str(remote_path),
            local_path=str(Path(local_path)),
            timeout=timeout,
        )

    def upload_file(
        self,
        local_path: str | Path,
        remote_path: str | Path,
        timeout: int = 30,
    ) -> dict[str, Any]:
        """Upload a local file to the Virtuoso host via the service."""
        return self._request(
            "upload_file",
            local_path=str(Path(local_path)),
            remote_path=str(remote_path),
            timeout=timeout,
        )

    def ciw_print(self, message: str, timeout: int = 10) -> dict[str, Any]:
        """Print a message to Virtuoso CIW via the service."""
        return self._request("ciw_print", message=message, timeout=timeout)

    def ciw_log(self, skill_code: str, timeout: int = 10) -> dict[str, Any]:
        """Execute SKILL and log both command and result to CIW via the service."""
        return self._request("ciw_log", skill=skill_code, timeout=timeout)

    def stop(self) -> dict[str, Any]:
        """Request the service to stop."""
        return self._request("stop", timeout=2)
