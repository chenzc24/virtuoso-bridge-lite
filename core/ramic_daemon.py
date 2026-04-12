#!/usr/bin/env python
"""RAMIC Bridge Daemon — TCP-to-Virtuoso IPC relay with callback socket.

Launched by Virtuoso's ipcBeginProcess(). Receives SKILL commands over TCP
(port N), writes them to stdout (→ Virtuoso). Results are received via a
callback socket (port N+1) instead of stdin, which avoids issues where the
ipcBeginProcess data handler stops firing after the first invocation on
certain Virtuoso/platform combinations (see issue #37).

Usage (called by ramic_bridge.il, not manually):
    python ramic_daemon.py 127.0.0.1 65432
"""

import sys
import socket
import os
import fcntl
import json
import errno
import time
import re

HOST = sys.argv[1]
PORT = int(sys.argv[2])

# Non-blocking stdin (Virtuoso's IPC pipe) — kept for compatibility
fcntl.fcntl(sys.stdin.fileno(), fcntl.F_SETFL,
            fcntl.fcntl(sys.stdin.fileno(), fcntl.F_GETFL) | os.O_NONBLOCK)

STX = b'\x02'  # start-of-result (success)
NAK = b'\x15'  # start-of-result (error)
RS  = b'\x1e'  # end-of-result


# Callback socket: Virtuoso sends results here instead of via stdin pipe
CALLBACK_PORT = PORT + 1
_cb_server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
_cb_server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
_cb_server.bind((HOST, CALLBACK_PORT))
_cb_server.listen(1)
_cb_server.settimeout(60)


def read_result():
    """Read result from Virtuoso via callback socket.

    The SKILL-side RBIpcDataHandler evaluates the expression and sends
    the result back as 'OK <value>' or 'ERR <msg>' over a TCP connection
    to the callback port.
    """
    try:
        conn, _ = _cb_server.accept()
        data = b""
        while True:
            chunk = conn.recv(65536)
            if not chunk:
                break
            data += chunk
        conn.close()
        text = data.decode('utf-8', errors='replace').strip()
        if text.startswith("OK "):
            return STX + text[3:].encode('utf-8')
        elif text.startswith("ERR "):
            return NAK + text[4:].encode('utf-8')
        else:
            return STX + text.encode('utf-8')
    except socket.timeout:
        return NAK + b"timeout waiting for Virtuoso callback"


_BLOCKED_FNS = re.compile(
    r'(?<!["\w])(shell|system|ipcBeginProcess|getShellEnvVar|sstGetUserName)\s*\(',
)


_SKIP_CHECK = os.environ.get("RB_UNSAFE", "").lower() in ("1", "true", "yes")


def _check_skill(skill: str) -> None:
    """Reject SKILL code that calls dangerous shell-access functions.
    Disable with environment variable RB_UNSAFE=1."""
    if _SKIP_CHECK:
        return
    # Strip string literals so we don't false-positive on quoted names.
    stripped = re.sub(r'"[^"]*"', '""', skill)
    m = _BLOCKED_FNS.search(stripped)
    if m:
        raise ValueError(f"Blocked SKILL function: {m.group(1)!r}")


def handle(conn):
    """Handle one client request."""
    chunks = []
    while True:
        chunk = conn.recv(65536)
        if not chunk:
            break
        chunks.append(chunk)
    req = json.loads(b"".join(chunks))

    # Flatten multi-line SKILL into a single line so that Virtuoso's
    # ipcBeginProcess (which fires the data handler per line) receives
    # the entire expression in one callback.  Strip ; comments first
    # because they would swallow everything after them on the joined line.
    # The regex skips semicolons inside "quoted strings".
    skill = re.sub(r'"[^"]*"|;[^\n]*', lambda m: m.group() if m.group().startswith('"') else ' ', req["skill"])
    skill = ' '.join(skill.split())                  # collapse whitespace

    _check_skill(skill)

    # Send SKILL to Virtuoso (newline required — ipcBeginProcess is line-based)
    sys.stdout.write(skill + '\n')
    sys.stdout.flush()

    # Read result via callback socket
    result = read_result()
    conn.sendall(result)


def main():
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    s.bind((HOST, PORT))
    s.listen(1)
    while True:
        conn, _ = s.accept()
        try:
            handle(conn)
        except Exception as e:
            try:
                conn.sendall(('\x15' + str(e)).encode('utf-8'))
            except:
                pass
        finally:
            try:
                conn.shutdown(socket.SHUT_RDWR)
            except:
                pass
            conn.close()


if __name__ == "__main__":
    main()
