;;-----------------------------------------------------------------------------
;; Archived raw Virtuoso bindkeys used as an operation-discovery reference.
;; This file is preserved for API lookup and future bridge feature design.
;; It is not intended to be loaded into context by default.
;;-----------------------------------------------------------------------------

;;-----------------------------------------------------------------------------
;; Bindkeys for 'Annotation Browser'
;;-----------------------------------------------------------------------------
hiSetBindKeys( "Annotation Browser" list(
    list("<Key>Delete" "_vbAssistantDeleteSelectedInTree(abGetAssistant(hiGetCurrentWindow()))")
)) ;; hiSetBindKeys
;;-----------------------------------------------------------------------------

;;-----------------------------------------------------------------------------
;; Bindkeys for 'Command Interpreter'
;;-----------------------------------------------------------------------------
hiSetBindKeys( "Command Interpreter" list(
    list("<Key>F3" "hiToggleEnterForm()")
    list("<Key>Help" "hiHelp('window 'ciw window(1))")

    ;; Empty bindkeys (typically inserted when a bindkey is redefined or deleted)
    list("<Key>F1" "")
)) ;; hiSetBindKeys
;;-----------------------------------------------------------------------------

;;-----------------------------------------------------------------------------
;; Bindkeys for 'EAD'
;;-----------------------------------------------------------------------------
hiSetBindKeys( "EAD" list(
    list("Ctrl<Key>U" "_eadToolbarUpdateAllNetsCB()")
)) ;; hiSetBindKeys
;;-----------------------------------------------------------------------------

;;-----------------------------------------------------------------------------
;; Bindkeys for 'EAD VSE-XL'
;;-----------------------------------------------------------------------------
hiSetBindKeys( "EAD VSE-XL" list(
    list("Ctrl<Key>U" "_eadToolbarUpdateAllNetsCB()")
)) ;; hiSetBindKeys
;;-----------------------------------------------------------------------------

;;-----------------------------------------------------------------------------
;; Bindkeys for 'Graphics Browser'
;;-----------------------------------------------------------------------------
hiSetBindKeys( "Graphics Browser" list(
    list("<DrawThru1>" "geSingleSelectBox()" "geSingleSelectBox()")
    list("<DrawThru3>" "hiZoomIn()" "hiZoomIn()")
    list("<Key>BackSpace" "" "deletePoint()")
    list("<Key>Escape" "" "cancelEnterFun()")
    list("<Key>F3" "" "hiToggleEnterForm()")
    list("<Key>F4" "geTogglePartialSelect()")
    list("Ctrl<Btn1Down>" "mouseSubSelectPt()" "mouseSubSelectPt()")
    list("Ctrl<Btn4Down>" "hiZoomInAtMouse()")
    list("Ctrl<Btn5Down>" "hiZoomOutAtMouse()")
    list("Ctrl<DrawThru1>" "geSubSelectBox()" "geSubSelectBox()")
    list("Ctrl<Key>Tab" "hiLowerWindow(hiGetCurrentWindow())")
    list("None<Btn1Down>" "mouseSingleSelectPt()" "mouseAddPt(t)")
    list("None<Btn1Down>(2)" "" "mouseFinishPt()")
    list("None<Btn2Down>" "hiRepeat()")
    list("None<Btn3Down>" "mousePopUp()" "mousePopUp()")
    list("None<Btn3Down>(2)" "" "hiToggleEnterForm()")
    list("None<Btn4Down>" "geScroll(nil \"n\" nil)")
    list("None<Btn5Down>" "geScroll(nil \"s\" nil)")
    list("Shift<Btn1Down>" "mouseAddSelectPt()" "mouseAddSelectPt()")
    list("Shift<Btn4Down>" "geScroll(nil \"w\" nil)")
    list("Shift<Btn5Down>" "geScroll(nil \"e\" nil)")
    list("Shift<DrawThru1>" "geAddSelectBox()" "geAddSelectBox()")
    list("Shift<DrawThru3>" "hiZoomOut()" "hiZoomOut()")
    list("Shift<Key>F4" "geToggleAreaSelectOption()")

    ;; Empty bindkeys (typically inserted when a bindkey is redefined or deleted)
    list("<Key>F1" "")
    list("Shift<Btn2Down>" "")
)) ;; hiSetBindKeys
;;-----------------------------------------------------------------------------

;;-----------------------------------------------------------------------------
;; Bindkeys for 'Layout'
;;-----------------------------------------------------------------------------
hiSetBindKeys( "Layout" list(
    list("<DrawThru1>" "leSelBoxOrStretch()" "geSingleSelectBox()")
    list("<DrawThru2>" "hiDynamicPanGrabbing()" "_cmdOptionDrawThru2()")
    list("<DrawThru3>" "hiZoomIn()" "hiZoomIn()")
    list("<Key>!" "pteSetActiveLpp(\"M1 drawing\") pteSetNoneVisible(?mode \"All\" ?panel \"Layers\") pteSetVisible(\"CO drawing\" t \"Layers\") pteSetVisible(\"M1 pin\" t \"Layers\")")
    list("<Key>#" "pteSetActiveLpp(\"M3 drawing\") pteSetNoneVisible(?mode \"All\" ?panel \"Layers\") pteSetVisible(\"VIA2 drawing\" t \"Layers\") pteSetVisible(\"M3 pin\" t \"Layers\")")
    list("<Key>$" "pteSetActiveLpp(\"M4 drawing\") pteSetNoneVisible(?mode \"All\" ?panel \"Layers\") pteSetVisible(\"VIA3 drawing\" t \"Layers\") pteSetVisible(\"M4 pin\" t \"Layers\")")
    list("<Key>%" "pteSetActiveLpp(\"M5 drawing\") pteSetNoneVisible(?mode \"All\" ?panel \"Layers\") pteSetVisible(\"VIA4 drawing\" t \"Layers\") pteSetVisible(\"M5 pin\" t \"Layers\")")
    list("<Key>&" "pteSetActiveLpp(\"M7 drawing\") pteSetNoneVisible(?mode \"All\" ?panel \"Layers\") pteSetVisible(\"VIA6 drawing\" t \"Layers\") pteSetVisible(\"M7 pin\" t \"Layers\")")
    list("<Key>'" "hiUpdateMagOptions()")
    list("<Key>(" "pteSetActiveLpp(\"M9 drawing\") pteSetNoneVisible(?mode \"All\" ?panel \"Layers\") pteSetVisible(\"VIA8 drawing\" t \"Layers\") pteSetVisible(\"M9 pin\" t \"Layers\")")
    list("<Key>*" "pteSetActiveLpp(\"M8 drawing\") pteSetNoneVisible(?mode \"All\" ?panel \"Layers\") pteSetVisible(\"VIA7 drawing\" t \"Layers\") pteSetVisible(\"M8 pin\" t \"Layers\")")
    list("<Key>+" "leIncrementStopLevelByOne(hiGetCurrentWindow())")
    list("<Key>-" "leDecrementStopLevelByOne(hiGetCurrentWindow())")
    list("<Key>." "leToggleMagnifier()")
    list("<Key>1" "pteSetActiveLpp(\"M1 drawing\") pteSetVisible(\"CO drawing\" t \"Layers\") pteSetVisible(\"M1 pin\" t \"Layers\")")
    list("<Key>2" "pteSetActiveLpp(\"M2 drawing\") pteSetVisible(\"VIA1 drawing\" t \"Layers\") pteSetVisible(\"M2 pin\" t \"Layers\")")
    list("<Key>3" "pteSetActiveLpp(\"M3 drawing\") pteSetVisible(\"VIA2 drawing\" t \"Layers\") pteSetVisible(\"M3 pin\" t \"Layers\")")
    list("<Key>4" "pteSetActiveLpp(\"M4 drawing\") pteSetVisible(\"VIA3 drawing\" t \"Layers\") pteSetVisible(\"M4 pin\" t \"Layers\")")
    list("<Key>5" "pteSetActiveLpp(\"M5 drawing\") pteSetVisible(\"VIA4 drawing\" t \"Layers\") pteSetVisible(\"M5 pin\" t \"Layers\")")
    list("<Key>6" "pteSetActiveLpp(\"M6 drawing\") pteSetVisible(\"VIA5 drawing\" t \"Layers\") pteSetVisible(\"M6 pin\" t \"Layers\")")
    list("<Key>7" "pteSetActiveLpp(\"M7 drawing\") pteSetVisible(\"VIA6 drawing\" t \"Layers\") pteSetVisible(\"M7 pin\" t \"Layers\")")
    list("<Key>8" "pteSetActiveLpp(\"M8 drawing\") pteSetVisible(\"VIA7 drawing\" t \"Layers\") pteSetVisible(\"M8 pin\" t \"Layers\")")
    list("<Key>9" "pteSetActiveLpp(\"M9 drawing\") pteSetVisible(\"VIA8 drawing\" t \"Layers\") pteSetVisible(\"M9 pin\" t \"Layers\")")
    list("<Key>@" "pteSetActiveLpp(\"M2 drawing\") pteSetNoneVisible(?mode \"All\" ?panel \"Layers\") pteSetVisible(\"VIA1 drawing\" t \"Layers\") pteSetVisible(\"M2 pin\" t \"Layers\")")
    list("<Key>A" "leHiQuickAlign()")
    list("<Key>B" "leReturnToLevel()")
    list("<Key>BackSpace" "deletePoint()" "deletePoint()")
    list("<Key>C" "leHiCopy()")
    list("<Key>D" "geSubSelectPoint()")
    list("<Key>Delete" "leHiDelete()" "leHiDelete()")
    list("<Key>Down" "geScroll(nil \"s\"    nil)")
    list("<Key>E" "leHiEditDisplayOptions()")
    list("<Key>Escape" "" "cancelEnterFun()")
    list("<Key>F" "hiZoomAbsoluteScale(hiGetCurrentWindow() 0.9)")
    list("<Key>F11" "deToggleAssistants()")
    list("<Key>F2" "geSave()")
    list("<Key>F3" "leHiSaveACopy(hiGetCurrentWindow())" "hiToggleEnterForm()")
    list("<Key>F4" "geTogglePartialSelect()")
    list("<Key>F5" "deFileOpen()")
    list("<Key>F6" "leToggleMaintainConnections()")
    list("<Key>F7" "leHiEditDRDRuleOptions()")
    list("<Key>F9" "geToggleDisplayResolution()")
    list("<Key>G" "leToggleGravity()")
    list("<Key>H" "leHiRepeatCopy()")
    list("<Key>I" "leHiCreateInst()")
    list("<Key>J" "geSelObjectsPartiallySelected()")
    list("<Key>K" "leHiCreateMeasurement()")
    list("<Key>KP_1" "pteSetActiveLpp(\"PO drawing\")")
    list("<Key>KP_2" "pteSetActiveLpp(\"OD drawing\")")
    list("<Key>KP_3" "pteSetActiveLpp(\"PP drawing\")")
    list("<Key>KP_4" "pteSetActiveLpp(\"NP drawing\")")
    list("<Key>KP_5" "pteSetActiveLpp(\"NW drawing\")")
    list("<Key>KP_6" "pteSetActiveLpp(\"PM drawing\")")
    list("<Key>KP_7" "pteSetActiveLpp(\"ref drawing\")")
    list("<Key>KP_Add" "leHiSetRefPoint()")
    list("<Key>KP_Divide" "drdAddTarget()" "drdAddTarget()")
    list("<Key>KP_Enter" "mouseAddPt()")
    list("<Key>KP_Equal" "legRpDelta = 0.5")
    list("<Key>KP_Multiply" "drdRemoveTarget()" "drdRemoveTarget()")
    list("<Key>KP_Subtract" "leSetRefPointInactive(geGetEditCellView())")
    list("<Key>L" "leHiCreateLabel(hiGetCurrentWindow() leGetEnv(\"labelMode\"))")
    list("<Key>Left" "geScroll(nil \"w\"    nil)")
    list("<Key>M" "leHiMove()")
    list("<Key>N" "leCycleSnapModes()")
    list("<Key>O" "leHiCreateVia()")
    list("<Key>P" "weHiInteractiveRouting()")
    list("<Key>Q" "leHiEditProp()")
    list("<Key>R" "leHiCreateRect()")
    list("<Key>S" "leHiStretch()")
    list("<Key>U" "hiUndo()")
    list("<Key>V" "leHiAttach()")
    list("<Key>W" "hiPrevWinView(hiGetCurrentWindow())")
    list("<Key>X" "leHiEditInPlace()")
    list("<Key>Y" "leHiYank()")
    list("<Key>Z" "hiZoomIn()")
    list("<Key>`" "leHiMarkNet()" "drdToggleSmartSnapMode()")
    list("<Key>space" "leHiAddWireVia(hiGetCurrentWindow())" "leSpaceBarFunc(hiGetCurrentWindow() t)")
    list("<Key>~" "leHiUnmarkNetAll()")
    list("Ctrl Shift<Key>D" "leHiP2P()")
    list("Ctrl Shift<Key>E" "leHiAddWireVia(hiGetCurrentWindow() \"targetLayers\")")
    list("Ctrl Shift<Key>G" "weGatherBusWires(hiGetCurrentWindow())")
    list("Ctrl Shift<Key>K" "leHiClearMeasurementInHier()")
    list("Ctrl Shift<Key>M" "leHiIncrementalViolation()")
    list("Ctrl Shift<Key>Q" "leHiAddWireVia(hiGetCurrentWindow() \"up\")")
    list("Ctrl Shift<Key>S" "leHiCreateStrandedWire()")
    list("Ctrl Shift<Key>W" "weHiInteractiveRouting()")
    list("Ctrl Shift<Key>X" "leHiCreateBus()")
    list("Ctrl Shift<Key>Z" "leWECycleControlWire()")
    list("Ctrl<Key>1" "if(leIsLayerVisible( list(\"M1\" \"drawing\")) then pteSetVisible(\"M1 drawing\" nil \"Layers\") pteSetVisible(\"CO drawing\" nil \"Layers\") pteSetVisible(\"M1 pin\" nil \"Layers\") else pteSetVisible(\"M1 drawing\" t \"Layers\") pteSetVisible(\"CO drawing\" t \"Layers\") pteSetVisible(\"M1 pin\" t \"Layers\"))")
    list("Ctrl<Key>2" "if(leIsLayerVisible( list(\"M2\" \"drawing\")) then pteSetVisible(\"M2 drawing\" nil \"Layers\") pteSetVisible(\"VIA1 drawing\" nil \"Layers\") pteSetVisible(\"M2 pin\" nil \"Layers\") else pteSetVisible(\"M2 drawing\" t \"Layers\") pteSetVisible(\"VIA1 drawing\" t \"Layers\") pteSetVisible(\"M2 pin\" t \"Layers\"))")
    list("Ctrl<Key>3" "if(leIsLayerVisible( list(\"M3\" \"drawing\")) then pteSetVisible(\"M3 drawing\" nil \"Layers\") pteSetVisible(\"VIA2 drawing\" nil \"Layers\") pteSetVisible(\"M3 pin\" nil \"Layers\") else pteSetVisible(\"M3 drawing\" t \"Layers\") pteSetVisible(\"VIA2 drawing\" t \"Layers\") pteSetVisible(\"M3 pin\" t \"Layers\"))")
    list("Ctrl<Key>4" "if(leIsLayerVisible( list(\"M4\" \"drawing\")) then pteSetVisible(\"M4 drawing\" nil \"Layers\") pteSetVisible(\"VIA3 drawing\" nil \"Layers\") pteSetVisible(\"M4 pin\" nil \"Layers\") else pteSetVisible(\"M4 drawing\" t \"Layers\") pteSetVisible(\"VIA3 drawing\" t \"Layers\") pteSetVisible(\"M4 pin\" t \"Layers\"))")
    list("Ctrl<Key>5" "if(leIsLayerVisible( list(\"M5\" \"drawing\")) then pteSetVisible(\"M5 drawing\" nil \"Layers\") pteSetVisible(\"VIA4 drawing\" nil \"Layers\") pteSetVisible(\"M5 pin\" nil \"Layers\") else pteSetVisible(\"M5 drawing\" t \"Layers\") pteSetVisible(\"VIA4 drawing\" t \"Layers\") pteSetVisible(\"M5 pin\" t \"Layers\"))")
    list("Ctrl<Key>6" "if(leIsLayerVisible( list(\"M6\" \"drawing\")) then pteSetVisible(\"M6 drawing\" nil \"Layers\") pteSetVisible(\"VIA5 drawing\" nil \"Layers\") pteSetVisible(\"M6 pin\" nil \"Layers\") else pteSetVisible(\"M6 drawing\" t \"Layers\") pteSetVisible(\"VIA5 drawing\" t \"Layers\") pteSetVisible(\"M6 pin\" t \"Layers\"))")
    list("Ctrl<Key>7" "if(leIsLayerVisible( list(\"M7\" \"drawing\")) then pteSetVisible(\"M7 drawing\" nil \"Layers\") pteSetVisible(\"VIA6 drawing\" nil \"Layers\") pteSetVisible(\"M7 pin\" nil \"Layers\") else pteSetVisible(\"M7 drawing\" t \"Layers\") pteSetVisible(\"VIA6 drawing\" t \"Layers\") pteSetVisible(\"M7 pin\" t \"Layers\"))")
    list("Ctrl<Key>8" "if(leIsLayerVisible( list(\"M8\" \"drawing\")) then pteSetVisible(\"M8 drawing\" nil \"Layers\") pteSetVisible(\"VIA7 drawing\" nil \"Layers\") pteSetVisible(\"M8 pin\" nil \"Layers\") else pteSetVisible(\"M8 drawing\" t \"Layers\") pteSetVisible(\"VIA7 drawing\" t \"Layers\") pteSetVisible(\"M8 pin\" t \"Layers\"))")
    list("Ctrl<Key>9" "if(leIsLayerVisible( list(\"M9\" \"drawing\")) then pteSetVisible(\"M9 drawing\" nil \"Layers\") pteSetVisible(\"VIA8 drawing\" nil \"Layers\") pteSetVisible(\"M9 pin\" nil \"Layers\") else pteSetVisible(\"M9 drawing\" t \"Layers\") pteSetVisible(\"VIA8 drawing\" t \"Layers\") pteSetVisible(\"M9 pin\" t \"Layers\"))")
    list("Ctrl<Key>A" "pteSetNoneVisible(?mode \"All\" ?panel \"Layers\")")
    list("Ctrl<Key>D" "geDeselectAllFig()")
    list("Ctrl<Key>E" "leToggleDrdMode()")
    list("Ctrl<Key>F" "leSetStopLevelToEditLevel(hiGetCurrentWindow())")
    list("Ctrl<Key>G" "geZoomToGrid(hiGetCurrentWindow())")
    list("Ctrl<Key>O" "geSelectViaPile()")
    list("Ctrl<Key>P" "leHiCreatePin()")
    list("Ctrl<Key>R" "hiRedraw()")
    list("Ctrl<Key>S" "leHiSave()")
    list("Ctrl<Key>W" "pteSetNoneSelectable(?mode \"All\" ?panel \"Layers\")")
    list("Ctrl<Key>Z" "pteSetSelectable(\"Instances\" nil \"Objects\")")
    list("Shift<Key>A" "pteSetAllVisible(?mode \"All\" ?panel \"Layers\")")
    list("Shift<Key>C" "leHiChop()")
    list("Shift<Key>G" "leHiCreateGuardRing()")
    list("Shift<Key>K" "leHiClearMeasurement()")
    list("Shift<Key>M" "leHiMerge()")
    list("Shift<Key>O" "leHiRotate()")
    list("Shift<Key>P" "leHiCreatePolygon()")
    list("Shift<Key>R" "leHiReShape()")
    list("Shift<Key>W" "pteSetAllSelectable(?mode \"All\" ?panel \"Layers\")")
    list("Shift<Key>X" "leHiDescend()")
    list("Shift<Key>Y" "leHiPaste()")
    list("Shift<Key>Z" "pteSetSelectable(\"Instances\" t \"Objects\")")
)) ;; hiSetBindKeys
;;-----------------------------------------------------------------------------

;;-----------------------------------------------------------------------------
;; Bindkeys for 'Palette'
;;-----------------------------------------------------------------------------
hiSetBindKeys( "Palette" list(
    list("<Key>1" "pteSetLSActive(?layerSets pteGetLSAtPosition(0) ?turnOnVis t ?turnOnSel t ?turnOffAllVis t ?turnOffAllSel t ?deactivateOthers t)")
    list("<Key>2" "pteSetLSActive(?layerSets pteGetLSAtPosition(1) ?turnOnVis t ?turnOnSel t ?turnOffAllVis t ?turnOffAllSel t ?deactivateOthers t)")
    list("<Key>3" "pteSetLSActive(?layerSets pteGetLSAtPosition(2) ?turnOnVis t ?turnOnSel t ?turnOffAllVis t ?turnOffAllSel t ?deactivateOthers t)")
    list("<Key>4" "pteSetLSActive(?layerSets pteGetLSAtPosition(3) ?turnOnVis t ?turnOnSel t ?turnOffAllVis t ?turnOffAllSel t ?deactivateOthers t)")
    list("<Key>5" "pteSetLSActive(?layerSets pteGetLSAtPosition(4) ?turnOnVis t ?turnOnSel t ?turnOffAllVis t ?turnOffAllSel t ?deactivateOthers t)")
    list("<Key>6" "pteSetLSActive(?layerSets pteGetLSAtPosition(5) ?turnOnVis t ?turnOnSel t ?turnOffAllVis t ?turnOffAllSel t ?deactivateOthers t)")
    list("<Key>7" "pteSetLSActive(?layerSets pteGetLSAtPosition(6) ?turnOnVis t ?turnOnSel t ?turnOffAllVis t ?turnOffAllSel t ?deactivateOthers t)")
    list("<Key>8" "pteSetLSActive(?layerSets pteGetLSAtPosition(7) ?turnOnVis t ?turnOnSel t ?turnOffAllVis t ?turnOffAllSel t ?deactivateOthers t)")
    list("<Key>9" "pteSetLSActive(?layerSets pteGetLSAtPosition(8) ?turnOnVis t ?turnOnSel t ?turnOffAllVis t ?turnOffAllSel t ?deactivateOthers t)")
    list("Ctrl<Key>1" "pteToggleLSActive(?layerSet pteGetLSAtPosition(0) ?toggleVis t ?toggleSel t)")
    list("Ctrl<Key>2" "pteToggleLSActive(?layerSet pteGetLSAtPosition(1) ?toggleVis t ?toggleSel t)")
    list("Ctrl<Key>3" "pteToggleLSActive(?layerSet pteGetLSAtPosition(2) ?toggleVis t ?toggleSel t)")
    list("Ctrl<Key>4" "pteToggleLSActive(?layerSet pteGetLSAtPosition(3) ?toggleVis t ?toggleSel t)")
    list("Ctrl<Key>5" "pteToggleLSActive(?layerSet pteGetLSAtPosition(4) ?toggleVis t ?toggleSel t)")
    list("Ctrl<Key>6" "pteToggleLSActive(?layerSet pteGetLSAtPosition(5) ?toggleVis t ?toggleSel t)")
    list("Ctrl<Key>7" "pteToggleLSActive(?layerSet pteGetLSAtPosition(6) ?toggleVis t ?toggleSel t)")
    list("Ctrl<Key>8" "pteToggleLSActive(?layerSet pteGetLSAtPosition(7) ?toggleVis t ?toggleSel t)")
    list("Ctrl<Key>9" "pteToggleLSActive(?layerSet pteGetLSAtPosition(8) ?toggleVis t ?toggleSel t)")
)) ;; hiSetBindKeys
;;-----------------------------------------------------------------------------

;;-----------------------------------------------------------------------------
;; Bindkeys for 'Schematics'
;;-----------------------------------------------------------------------------
hiSetBindKeys( "Schematics" list(
    list("<DrawThru1>" "schDirectEdit(1)" "geSingleSelectBox()")
    list("<DrawThru2>" "hiDynamicPanGrabbing()" "hiDynamicPanGrabbing()")
    list("<DrawThru3>" "hiZoomIn()" "hiZoomIn()")
    list("<Key>F" "schZoomFit(1.0 0.9)")
    list("<Key>I" "schHiCreateInst()")
    list("<Key>L" "schHiCreateWireLabel()")
    list("<Key>P" "schHiCreatePin()")
    list("<Key>Q" "schHiObjectProperty()" "schHiObjectProperty()")
    list("<Key>R" "schHiRotate(t)" "schSetEnv(\"rotate\" t)")
    list("<Key>W" "schHiCreateWire(0.0)")
    list("<Key>X" "schHiCheck(\"run\")")
    list("<Key>space" "schHiCreateWireStubs()")
    list("Ctrl<Key>A" "schSelectAllFig()")
    list("Ctrl<Key>D" "schDeselectAllFig()")
    list("Ctrl<Key>E" "schHiReturn()")
    list("Ctrl<Key>F" "schSetSelectOptions()")
    list("Ctrl<Key>T" "schHiZoomToSelSet()")
    list("Shift<Key>E" "schHiDescendEdit()")
    list("Shift<Key>M" "schHiMove()")
    list("Shift<Key>S" "_schHiSave()")
    list("Shift<Key>W" "schHiCreateWire(schGetEnv(\"defWideWireWidth\"))")
    list("Shift<Key>X" "schHiCheckAndSave()")
)) ;; hiSetBindKeys
;;-----------------------------------------------------------------------------

;;-----------------------------------------------------------------------------
;; Bindkeys for 'Symbol'
;;-----------------------------------------------------------------------------
hiSetBindKeys( "Symbol" list(
    list("<Key>L" "schHiCreateSymbolLabel()")
    list("<Key>P" "schHiCreateSymbolPin()")
    list("<Key>X" "schHiVIC()")
    list("Shift<Key>X" "schHiVICAndSave()")
)) ;; hiSetBindKeys
;;-----------------------------------------------------------------------------
