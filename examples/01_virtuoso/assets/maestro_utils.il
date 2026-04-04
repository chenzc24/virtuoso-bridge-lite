; maestro_utils.il
;
; Utility procedures for managing Maestro sessions via bridge.
;
; Procedures:
;   MaestroOpen(libName cellName) - open maestro, ensure editable, return session
;   MaestroClose(libName cellName) - save and close maestro cleanly
;   MaestroCloseAll() - close all maestro windows and sessions
;   MaestroClearLocks(libName cellName) - remove stale .cdslck files
;   MaestroDismissDialog() - dismiss any blocking dialog

; --- Dismiss any current dialog (Overwrite, Save, etc.) ---
procedure(MaestroDismissDialog()
  let((form)
    form = hiGetCurrentForm()
    when(form
      hiFormDone(form)
      printf("[MaestroDismissDialog] Dismissed dialog\n")
      t
    )
  )
)

; --- Clear stale lock files for a maestro cellview ---
procedure(MaestroClearLocks(libName cellName)
  let((libPath lockPath)
    libPath = ddGetObj(libName)~>writePath
    when(libPath
      lockPath = sprintf(nil "%s/%s/maestro/maestro.sdb.cdslck" libPath cellName)
      when(isFile(lockPath)
        deleteFile(lockPath)
        printf("[MaestroClearLocks] Removed %s\n" lockPath)
      )
    )
    t
  )
)

; --- Open maestro: check existing, make editable, return session ---
procedure(MaestroOpen(libName cellName)
  let((existingWin session result)

    ; 1. Check if maestro window already open for this cell
    existingWin = nil
    foreach(win hiGetWindowList()
      let((name)
        name = hiGetWindowName(win)
        when(and(name
                 rexMatchp(cellName name)
                 rexMatchp("maestro" name))
          existingWin = win
        )
      )
    )

    ; 2. If not open, clear stale locks then open
    unless(existingWin
      MaestroClearLocks(libName cellName)
      existingWin = deOpenCellView(libName cellName "maestro" "maestro" nil "r")
      printf("[MaestroOpen] Opened %s/%s/maestro\n" libName cellName)
    )

    ; 3. Try make editable; dismiss dialog if it pops up
    result = maeMakeEditable()
    MaestroDismissDialog()  ; handle "Change Mode Confirmation" / "Overwrite" dialog
    unless(result
      ; Retry after dismissing dialog
      result = maeMakeEditable()
      MaestroDismissDialog()
    )

    ; 4. Get first available session
    session = nil
    foreach(s maeGetSessions()
      unless(session session = s)
    )

    printf("[MaestroOpen] Session: %s  Editable: %L\n" session result)
    session
  )
)

; --- Close maestro for a specific cell: save then close ---
procedure(MaestroClose(libName cellName)
  let((found)
    ; Save first (prevents "save changes?" dialog on close)
    foreach(s maeGetSessions()
      maeSaveSetup(?lib libName ?cell cellName ?view "maestro" ?session s)
    )

    ; Find and close only this cell's maestro windows
    found = nil
    foreach(win hiGetWindowList()
      let((name)
        name = hiGetWindowName(win)
        when(and(name
                 rexMatchp(cellName name)
                 rexMatchp("maestro" name))
          hiCloseWindow(win)
          MaestroDismissDialog()  ; handle any save dialog
          found = t
        )
      )
    )

    printf("[MaestroClose] %s/%s/maestro closed\n" libName cellName)
    found
  )
)

; --- Close all maestro windows and sessions ---
procedure(MaestroCloseAll()
  let((count)
    count = 0

    ; Save all then close
    foreach(win hiGetWindowList()
      let((name)
        name = hiGetWindowName(win)
        when(and(name rexMatchp("maestro" name))
          hiCloseWindow(win)
          MaestroDismissDialog()
          count = count + 1
        )
      )
    )

    ; Close all sessions
    foreach(s maeGetSessions()
      maeCloseSession(?session s ?forceClose t)
    )

    printf("[MaestroCloseAll] Closed %d maestro windows\n" count)
    count
  )
)
