#!/usr/bin/env python2
"""X11 dialog finder and dismisser. Runs on the remote Virtuoso host.

Usage:
    python2 x11_dismiss_dialog.py <DISPLAY> [--dismiss] [--screenshot /tmp/out.ppm]

Output (stdout): JSON lines, one per dialog found:
    {"window_id": "0x2e01f16", "title": "Save Changes", "x": 1010, "y": 378, "w": 239, "h": 142}

With --dismiss: sends Enter key to each dialog found.
With --screenshot: saves a fullscreen PPM screenshot to the given path.

Exit codes: 0 = dialogs found/dismissed, 1 = no dialogs found, 2 = error
"""
import ctypes
import ctypes.util
import json
import os
import struct
import subprocess
import sys
import time

DIALOG_TITLES = ["Save Changes", "Warning", "Error", "Confirm", "Question",
                 "Discard", "Overwrite", "Not Found", "Information"]


def find_x11_env(user=None):
    """Auto-detect DISPLAY and XAUTHORITY from running virtuoso process."""
    result = {"DISPLAY": None, "XAUTHORITY": None}
    try:
        pids = subprocess.check_output(
            ["pgrep", "-u", user or os.environ.get("USER", ""), "-x", "virtuoso"],
            stderr=subprocess.PIPE
        ).strip().split("\n")
        for pid in pids:
            pid = pid.strip()
            if not pid:
                continue
            env_file = "/proc/%s/environ" % pid
            try:
                data = open(env_file, "rb").read()
                for chunk in data.split(b"\x00"):
                    if chunk.startswith(b"DISPLAY=") and not result["DISPLAY"]:
                        result["DISPLAY"] = chunk.split(b"=", 1)[1].decode()
                    elif chunk.startswith(b"XAUTHORITY=") and not result["XAUTHORITY"]:
                        result["XAUTHORITY"] = chunk.split(b"=", 1)[1].decode()
                if result["DISPLAY"]:
                    return result
            except (IOError, OSError):
                continue
    except (subprocess.CalledProcessError, OSError):
        pass
    return result


def find_dialogs(display):
    """Use xwininfo to find dialog windows matching known titles."""
    os.environ["DISPLAY"] = display
    try:
        tree = subprocess.check_output(
            ["xwininfo", "-root", "-tree"],
            stderr=subprocess.PIPE
        ).decode("utf-8", "replace")
    except (subprocess.CalledProcessError, OSError) as e:
        print(json.dumps({"error": "xwininfo failed: %s" % str(e)}))
        return []

    dialogs = []
    for line in tree.splitlines():
        for title in DIALOG_TITLES:
            if ('"%s"' % title) in line:
                parts = line.strip().split()
                if len(parts) < 1:
                    break
                win_id = parts[0]
                try:
                    info = subprocess.check_output(
                        ["xwininfo", "-id", win_id],
                        stderr=subprocess.PIPE
                    ).decode("utf-8", "replace")
                    x = y = w = h = 0
                    for il in info.splitlines():
                        il = il.strip()
                        if il.startswith("Absolute upper-left X:"):
                            x = int(il.split(":")[1].strip())
                        elif il.startswith("Absolute upper-left Y:"):
                            y = int(il.split(":")[1].strip())
                        elif il.startswith("Width:"):
                            w = int(il.split(":")[1].strip())
                        elif il.startswith("Height:"):
                            h = int(il.split(":")[1].strip())
                    dialogs.append({
                        "window_id": win_id,
                        "title": title,
                        "x": x, "y": y, "w": w, "h": h,
                    })
                except (subprocess.CalledProcessError, OSError):
                    dialogs.append({"window_id": win_id, "title": title})
                break
    return dialogs


def dismiss_window(display, win_id_str):
    """Send Enter key to a window via XTest."""
    os.environ["DISPLAY"] = display
    xlib_path = ctypes.util.find_library("X11")
    xtst_path = ctypes.util.find_library("Xtst")
    if not xlib_path or not xtst_path:
        return {"error": "libX11 or libXtst not found"}

    xlib = ctypes.cdll.LoadLibrary(xlib_path)
    xtst = ctypes.cdll.LoadLibrary(xtst_path)

    dpy = xlib.XOpenDisplay(None)
    if not dpy:
        return {"error": "cannot open display %s" % display}

    win_id = int(win_id_str, 16) if win_id_str.startswith("0x") else int(win_id_str)

    xlib.XRaiseWindow(dpy, win_id)
    xlib.XSetInputFocus(dpy, win_id, 1, 0)  # RevertToParent
    xlib.XFlush(dpy)

    time.sleep(0.15)

    keysym_return = 0xff0d  # XK_Return
    keycode = xlib.XKeysymToKeycode(dpy, keysym_return)
    xtst.XTestFakeKeyEvent(dpy, keycode, True, 0)
    xtst.XTestFakeKeyEvent(dpy, keycode, False, 0)
    xlib.XFlush(dpy)

    xlib.XCloseDisplay(dpy)
    return {"dismissed": win_id_str, "keycode": int(keycode)}


def screenshot_ppm(display, output_path):
    """Take a fullscreen screenshot, save as PPM."""
    os.environ["DISPLAY"] = display
    xwd_tmp = "/tmp/_vb_screen.xwd"
    try:
        subprocess.check_call(
            ["xwd", "-root", "-silent", "-out", xwd_tmp],
            stderr=subprocess.PIPE
        )
    except (subprocess.CalledProcessError, OSError) as e:
        return {"error": "xwd failed: %s" % str(e)}

    data = open(xwd_tmp, "rb").read()
    hs = struct.unpack(">I", data[0:4])[0]
    w = struct.unpack(">I", data[16:20])[0]
    h = struct.unpack(">I", data[20:24])[0]
    bpp = struct.unpack(">I", data[44:48])[0]
    bpl = struct.unpack(">I", data[48:52])[0]
    pixels = data[hs:]

    # XWD byte_order: 0=LSBFirst (RGB pixels), 1=MSBFirst (BGR pixels)
    byte_order = struct.unpack(">I", data[28:32])[0]

    rgb = bytearray()
    for y_row in range(h):
        row = pixels[y_row * bpl: y_row * bpl + w * (bpp // 8)]
        for x_col in range(w):
            if bpp == 32:
                p0, p1, p2 = ord(row[x_col*4]), ord(row[x_col*4+1]), ord(row[x_col*4+2])
            else:
                p0, p1, p2 = ord(row[x_col*3]), ord(row[x_col*3+1]), ord(row[x_col*3+2])
            if byte_order == 0:  # LSBFirst: stored as R,G,B
                rgb.append(p0)
                rgb.append(p1)
                rgb.append(p2)
            else:  # MSBFirst: stored as B,G,R
                rgb.append(p2)
                rgb.append(p1)
                rgb.append(p0)

    with open(output_path, "wb") as f:
        f.write("P6\n%d %d\n255\n" % (w, h))
        f.write(bytes(rgb))

    try:
        os.remove(xwd_tmp)
    except OSError:
        pass
    return {"screenshot": output_path, "size": [w, h]}


def main():
    args = sys.argv[1:]
    display = None
    do_dismiss = False
    screenshot_path = None

    i = 0
    while i < len(args):
        if args[i] == "--dismiss":
            do_dismiss = True
        elif args[i] == "--screenshot":
            i += 1
            screenshot_path = args[i] if i < len(args) else "/tmp/_vb_screenshot.ppm"
        elif not args[i].startswith("-"):
            display = args[i]
        i += 1

    if not display:
        x11_env = find_x11_env()
        display = x11_env.get("DISPLAY")
        if not display:
            print(json.dumps({"error": "cannot detect DISPLAY"}))
            sys.exit(2)
        if x11_env.get("XAUTHORITY"):
            os.environ["XAUTHORITY"] = x11_env["XAUTHORITY"]

    if screenshot_path:
        result = screenshot_ppm(display, screenshot_path)
        print(json.dumps(result))

    dialogs = find_dialogs(display)
    for d in dialogs:
        print(json.dumps(d))

    if not dialogs:
        sys.exit(1)

    if do_dismiss:
        for d in dialogs:
            if "window_id" in d:
                result = dismiss_window(display, d["window_id"])
                print(json.dumps(result))

    sys.exit(0)


if __name__ == "__main__":
    main()
