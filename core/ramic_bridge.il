; RAMIC Bridge — SKILL-side IPC via callback socket
; Load this in Virtuoso CIW: load("/path/to/ramic_bridge.il")

; Load paths from environment variables, with fallbacks
RBDPath = if(getShellEnvVar("RB_DAEMON_PATH") then
                getShellEnvVar("RB_DAEMON_PATH")
            else
                "./ramic_daemon.py"
            )
RBPython = if(getShellEnvVar("RB_PYTHON_PATH") then
                getShellEnvVar("RB_PYTHON_PATH")
            else
                "python"
            )
RBPort = if(getShellEnvVar("RB_PORT") then
                atoi(getShellEnvVar("RB_PORT"))
            else
                65432
            )
RBCallbackPort = RBPort + 1

procedure(RBSendCallback(msg)
  "Sends result back to daemon via TCP callback socket.
   Uses a temp file + background Python one-liner to avoid blocking CIW."
  let((tmpFile port cmd)
    tmpFile = sprintf(nil "/tmp/.ramic_cb_%d" ipcGetPid())
    port = outfile(tmpFile "w")
    when(port
      fprintf(port "%s" msg)
      close(port)
    )
    cmd = sprintf(nil "%s -c \"import socket,sys;f=open('%s');d=f.read();f.close();import os;os.remove('%s');s=socket.socket();s.connect(('127.0.0.1',%d));s.sendall(d.encode());s.close()\" &"
      RBPython tmpFile tmpFile RBCallbackPort)
    system(cmd)
  )
)

procedure(RBIpcDataHandler(ipcId data)
  "Evaluates SKILL from daemon stdout, sends result via callback socket.
   Using a callback socket instead of ipcWriteProcess avoids issues where
   the ipcBeginProcess data handler stops firing after the first invocation
   on certain Virtuoso/platform combinations (see issue #37)."
  let((result resultStr)
    if(errset(result = evalstring(data)) then
      resultStr = sprintf(nil "OK %L" result)
    else
      resultStr = sprintf(nil "ERR %L" errset.errset)
    )
    RBSendCallback(resultStr)
  )
)

procedure(RBIpcErrHandler(ipcId data)
  printf("[RAMIC-ERR] %s\n" data)
)

procedure(RBIpcFinishHandler(ipcId data)
  printf("[RAMIC] daemon exited\n")
)

unless(boundp('RBIpc) RBIpc = 'unbound)

procedure(RBStart()
  if(boundp('RBIpc) && ipcIsAliveProcess(RBIpc) then
    printf("[RAMIC] already running\n")
  else
    ; Use "env -u" to strip Virtuoso's LD_LIBRARY_PATH / LD_PRELOAD
    ; so the system Python links against its own libs.
    ; Use "stdbuf -oL" to force line-buffered stdout so ipcBeginProcess
    ; receives complete lines without waiting for Python's buffer to fill.
    RBIpc = ipcBeginProcess(
      sprintf(nil "/usr/bin/env -u LD_LIBRARY_PATH -u LD_PRELOAD stdbuf -oL %s -u %L %s %d"
        RBPython RBDPath "127.0.0.1" RBPort)
      "" 'RBIpcDataHandler 'RBIpcErrHandler 'RBIpcFinishHandler "")
    printf("[RAMIC] started on port %d (callback on %d)\n" RBPort RBCallbackPort)
  )
)

RBStart()
