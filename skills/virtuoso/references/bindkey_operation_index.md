# Bindkey Operation Index

This file is not a shortcut guide. It is an operation/API lookup derived from
the archived bindkeys in [`raw_bindkeys.il`](/Users/tokenzhang/Documents/virtuoso-bridge/skills/virtuoso/references/raw_bindkeys.il).

Use it when you want to answer:

- "What Virtuoso function corresponds to this manual action?"
- "Should this action become a bridge API?"
- "Is this operation safe for request/response automation, or does it depend on live UI interaction?"

## Status Legend

- `implemented`: already exposed through `client.layout.*`, `client.schematic.*`, or editors
- `candidate`: good future bridge API candidate
- `interactive`: likely too UI-driven for stable bridge automation
- `avoid`: low-value UI chrome or poor fit for bridge APIs

## Layout Operations

### View Control

- `hiZoomAbsoluteScale`
  - status: `implemented`
  - current API: `client.layout.fit_view()`
- `hiZoomIn`, `hiZoomOut`, `hiZoomInAtMouse`, `hiZoomOutAtMouse`
  - status: `candidate`
  - note: fixed zoom helpers are bridgeable; mouse-relative variants are weaker fits
- `geScroll`
  - status: `candidate`
  - note: directional pan API could be added cleanly
- `leIncrementStopLevelByOne`, `leDecrementStopLevelByOne`, `leSetStopLevelToEditLevel`
  - status: `candidate`
  - note: useful for hierarchy browsing and screenshots
- `hiPrevWinView`, `hiNextWinView`
  - status: `candidate`
  - note: useful if viewport-history semantics matter

### Layer / Visibility

- `pteSetActiveLpp`
  - status: `implemented`
  - current API: `client.layout.set_active_lpp(...)`
- `pteSetVisible`
  - status: `implemented`
  - current API: `client.layout.show_layers(...)`, `client.layout.hide_layers(...)`
- `pteSetNoneVisible`
  - status: `implemented`
  - current API: `client.layout.show_only_layers(...)`
- `pteSetAllVisible`
  - status: `candidate`
  - note: useful as a reset helper
- `pteSetNoneSelectable`, `pteSetAllSelectable`, `pteSetSelectable`
  - status: `candidate`
  - note: useful for safer scripted selection workflows
- `pteSetLSActive`, `pteToggleLSActive`
  - status: `candidate`
  - note: layer-set support is useful if teams rely on palette presets

### Selection / Deletion

- `geSingleSelectBox`, `geAddSelectBox`, `geSubSelectBox`
  - status: `implemented`
  - current API: `client.layout.select_box(..., mode_name="replace|add|sub")`
- `geDeselectAllFig`
  - status: `implemented`
  - current API: used inside selection flow
- `leHiDelete`
  - status: `implemented`
  - current API: `client.layout.delete_selected()`, `client.layout.clear_current()`
- `geSubSelectPoint`, `mouseSubSelectPt`, `mouseAddSelectPt`
  - status: `interactive`
  - note: mouse-point semantics are not a good primary bridge surface
- `geSelObjectsPartiallySelected`, `geTogglePartialSelect`, `geToggleAreaSelectOption`
  - status: `candidate`
  - note: useful if partial-select workflows matter for edits

### Create / Edit Geometry

- `leHiCreateRect`
  - status: `implemented`
  - current editor API: `layout.add_rect(...)`
- `leHiCreatePolygon`
  - status: `implemented`
  - current editor API: `layout.add_polygon(...)`
- `leHiCreateLabel`
  - status: `implemented`
  - current editor API: `layout.add_label(...)`
- `leHiCreateVia`
  - status: `implemented`
  - current editor API: `layout.add_via(...)`, `layout.add_via_by_name(...)`
- `leHiCreateInst`
  - status: `implemented`
  - current editor API: `layout.add_instance(...)`
- `leHiMove`, `leHiCopy`, `leHiStretch`, `leHiRotate`, `leHiFlip`, `leHiPaste`, `leHiYank`
  - status: `candidate`
  - note: these are strong next-step edit APIs
- `leHiChop`, `leHiMerge`, `leHiReShape`, `leHiAttach`, `leHiQuickAlign`
  - status: `candidate`
  - note: valuable but need careful parameter design
- `leHiEditProp`
  - status: `candidate`
  - note: likely needs object-targeted property APIs instead of form-style editing

### Routing

- `leHiAddWireVia`
  - status: `candidate`
  - note: good basis for via-stack and assisted-routing helpers
- `weHiInteractiveRouting`
  - status: `interactive`
  - note: too UI-driven as-is; better replaced by explicit route helpers
- `leFinishWire`
  - status: `interactive`
  - note: depends on live interactive routing state
- `leHiCreateBus`
  - status: `candidate`
  - note: very relevant for bus helper APIs
- `weGatherBusWires`
  - status: `candidate`
  - note: useful if bus post-processing is common
- `leHiCreateStrandedWire`
  - status: `candidate`
  - note: likely niche but bridgeable
- `leWECycleControlWire`, `weScaleMagnifierOrIncreaseWidth`, `weScrollOrCycleUpWireViaAlignment`
  - status: `interactive`
  - note: tied to editor state rather than deterministic API calls

### Nets / Marking / Checking

- `leHiMarkNet`, `leHiUnmarkNet`, `leHiUnmarkNetAll`
  - status: `implemented`
  - current API: `client.layout.highlight_net(...)`
- `leToggleMaintainConnections`
  - status: `candidate`
  - note: relevant for edit semantics and safer scripted modifications
- `leHiEditDRDRuleOptions`, `leToggleDrdMode`, `drdAddTarget`, `drdRemoveTarget`
  - status: `candidate`
  - note: useful only if DRD state manipulation becomes a real workflow
- `leHiIncrementalViolation`
  - status: `candidate`
  - note: good for future check/review workflows

### Measurement / Coordinates

- `leHiCreateMeasurement`, `leHiClearMeasurement`, `leHiClearMeasurementInHier`
  - status: `candidate`
  - note: good for review and screenshot annotation flows
- `leHiSetRefPoint`, `leSetRefPointInactive`, `leMoveCursorToRefPoint`
  - status: `candidate`
  - note: reference-point workflow can be translated into explicit coordinate APIs
- `leMoveCursor(...)`, `legRpDelta = ...`
  - status: `avoid`
  - note: cursor nudge is too UI-specific; expose direct coordinate arguments instead

## Schematic Operations

### Core Editing

- `schHiCreateInst`
  - status: `implemented`
  - current editor API: `schematic.add_instance(...)`
- `schHiCreateWire`
  - status: `implemented`
  - current editor API: `schematic.add_wire(...)`
- `schHiCreatePin`
  - status: `implemented`
  - current editor API: `schematic.add_pin(...)`
- `schHiCreateWireLabel`
  - status: `implemented`
  - current editor API: `schematic.add_label(...)`
- `schHiCheck`, `schHiCheckAndSave`
  - status: `implemented`
  - current behavior: editor exits with check+save; namespace also exposes `client.schematic.check()` and `save()`

### Navigation / Selection

- `schZoomFit`
  - status: `candidate`
  - note: schematic fit-view helper is a good next addition
- `schSelectAllFig`, `schDeselectAllFig`, `schSingleSelectBox`, `schSubSelectBox`
  - status: `candidate`
  - note: schematic namespace lacks explicit selection helpers today
- `schHiZoomToSelSet`
  - status: `candidate`
  - note: useful for schematic review screenshots

### Connectivity Helpers

- `schHiCreateWireStubs`
  - status: `candidate`
  - note: aligns with terminal-aware wire-stub helpers
- `schSnapToConn`
  - status: `interactive`
  - note: snap mode is editor-state driven
- `geEnterAddNetProbe`
  - status: `candidate`
  - note: probing/highlighting could be made explicit if needed

### Object Editing

- `schHiMove`, `schHiStretch`, `schHiRotate`, `schHiObjectProperty`
  - status: `candidate`
  - note: these are reasonable future object-targeted APIs
- `schHiDescendRead`, `schHiDescendEdit`, `schHiReturn`
  - status: `candidate`
  - note: useful if hierarchical schematic browsing becomes important

## Operations To Keep As Archive Only

These should stay in the raw archive for lookup, but should not drive bridge API design directly:

- `hiToggleEnterForm`
- `deToggleAssistants`
- `deToggleToolbars`
- `hiFocusToCIW`
- `mousePopUp`
- `cmdOption`, `cmdShiftOption`, `cmdCtrlOption`
- magnifier sizing / cursor movement commands
- most `PcellIDE`-specific overrides
- most `viva*` graph/browser shortcuts unless waveform tooling becomes a direct bridge target

## Recommended Next API Candidates

If continuing bridge feature work, the strongest next layout/schematic candidates from this archive are:

- layout hierarchy view control:
  - stop-level set/inc/dec
- layout edit transforms:
  - move / copy / rotate / stretch
- layout review helpers:
  - measure / clear measurements
- layout bus/routing helpers:
  - create bus
  - explicit add-wire-via helpers
- schematic viewport and selection helpers:
  - fit view
  - select/deselect box
- schematic object transforms:
  - move / rotate / property update
