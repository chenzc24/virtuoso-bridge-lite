# core/ — The Entire Bridge in 3 Files

This is the raw mechanism. No package, no pip install, no CLI.

## Files

| File | Lines | What it does |
|---|---|---|
| `ramic_bridge.il` | 33 | SKILL side: receives code → `evalstring()` → returns result |
| `ramic_daemon.py` | 90 | TCP relay: sits between network and Virtuoso's IPC pipe |
| `bridge_client.py` | 40 | Python client: sends SKILL over TCP, prints result |

## How to Use

```bash
# 1. Copy daemon to remote
scp core/ramic_daemon.py remote:/tmp/

# 2. In Virtuoso CIW, load the IL file:
#    load("/tmp/ramic_bridge.il")
#    (it auto-starts the daemon on port 65432)

# 3. SSH tunnel
ssh -N -L 65432:localhost:65432 remote &

# 4. Run SKILL from your machine
python core/bridge_client.py '1+2'
python core/bridge_client.py 'hiGetCurrentWindow()'
python core/bridge_client.py 'geGetEditCellView()~>cellName'
```

## How It Works

```
Your Machine                          Remote Virtuoso Server
────────────                          ──────────────────────

bridge_client.py                      Virtuoso process
    │                                     │
    │ TCP: {"skill":"1+2"}                │
    ├──── SSH tunnel ────────────► ramic_daemon.py
    │                                     │
    │                                     │ stdout: "1+2"
    │                                     ├──► ipcWriteProcess
    │                                     │        │
    │                                     │        ▼
    │                                     │    evalstring("1+2")
    │                                     │        │
    │                                     │        ▼
    │                                     │ stdin: "\x02 3 \x1e"
    │                                     ◄──┘
    │ TCP: "\x02 3"                       │
    ◄──── SSH tunnel ─────────────┘
    │
    ▼
   "3"
```

The daemon runs as a **child process of Virtuoso** (via `ipcBeginProcess`).
Virtuoso talks to it through stdin/stdout pipes. The daemon exposes this
as a TCP socket. The SSH tunnel makes the TCP socket reachable from your machine.

That's the entire bridge. `core/` is for understanding the mechanism — no persistent SSH, no file transfer, no auto-reconnect. For production use, install the full package (`pip install -e .`) which adds all of that.
