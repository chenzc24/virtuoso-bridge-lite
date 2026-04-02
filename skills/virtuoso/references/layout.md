# Layout Reference

## Primary Surfaces

- namespace API: `client.layout`
- declarative editor: `LayoutEditor` from `client.layout.edit(...)`

Prefer pattern:

```python
with client.layout.edit(lib, cell, mode="a") as layout:
    layout.add_instance(...)
    layout.add_mosaic(...)
    layout.add_rect(...)
    layout.add_path(...)
    layout.add_via_by_name(...)
```

## Namespace API

Read / query:
- `client.layout.read_summary(...)`
- `client.layout.read_geometry(...)`
- `client.layout.list_shapes(...)`

Control / visibility:
- `client.layout.clear_current(...)`
- `client.layout.fit_view(...)`
- `client.layout.set_active_lpp(...)`
- `client.layout.show_only_layers(...)`
- `client.layout.show_layers(...)`
- `client.layout.hide_layers(...)`
- `client.layout.highlight_net(...)`
- `client.layout.select_box(...)`
- `client.layout.delete_selected(...)`

Cleanup:
- `client.layout.delete_shapes_on_layer(...)`
- `client.layout.clear_routing(...)`
- `client.layout.delete_cell(...)`

## Editor Methods

- `add_instance(...)`
- `add_mosaic(...)`
- `add_rect(...)`
- `add_path(...)`
- `add_label(...)`
- `add_polygon(...)`
- `add_via(...)`
- `add_via_by_name(...)`
- `add_raw_via_by_name(...)`
- `fit_view()`
- `set_active_lpp(...)`
- `show_only_layers(...)`
- `show_layers(...)`
- `hide_layers(...)`
- `highlight_net(...)`
- `select_box(...)`
- `delete_selected()`

## Guidance

- prefer `client.layout.read_geometry(...)` over summary text when downstream processing matters
- use `add_via_by_name(...)` for normal usage
- use `add_raw_via_by_name(...)` only when the raw-via path itself needs to be demonstrated
- for arrays, prefer `layout.add_mosaic(...)` over hand-written raw SKILL
- screenshots should use `client.download_file(...)`, not ad hoc SSH code
- after every nontrivial routing change, take a screenshot and inspect the image before claiming success
- when creating a new local script, scratch file, or generated artifact for layout work, include a timestamp in the filename by default to avoid accidental overwrite and to keep attempts traceable

## Path Routing Method

For custom routing around analog unit cells, do not start from guessed pin-label centers.

Recommended workflow:

1. Read the master geometry first.
- Use `client.layout.read_geometry(lib, cell)` or raw SKILL on `cv~>shapes` / `cv~>vias`.
- Identify the actual routing landing shape or via bbox.
- Route to the real metal or via centerline, not to a nearby text label.

2. Use `path` when the route is fundamentally a centerline-driven wire.
- `add_path(...)` is the right default for vertical drops, horizontal buses, and narrow analog escape lines.
- Keep the path centerline aligned to the target contact center.

3. Correct L-corners geometrically instead of changing layers unless needed.
- If a vertical path meets a horizontal path of the same width, extend the horizontal segment endpoint by half the wire width toward the corner.
- This avoids the visual and electrical "half-corner" gap that appears when both paths stop exactly at the same centerline intersection.

4. Only add vias when a real layer transition is required.
- Do not add vias just to hide a coordinate mistake.
- For same-layer L-shapes, fix the path endpoints instead of inserting unnecessary vias.

Practical note from the unary CDAC routing work:
- the `LB_CUNIT` bottom routing had to align to the internal `M3` via center, not to the visible pin label
- changing only the y-coordinate without checking the screenshot led to repeated false positives
- the successful same-layer L-shape used `path` plus a half-width horizontal extension at the elbow

## Coordinate Calculation

When deriving routing coordinates from a custom unit cell, prefer explicit measured constants over visual guessing.

Recommended pattern:

1. Measure the master bbox.
- Read `x_min`, `y_min`, `x_max`, `y_max` from `read_geometry(...)`.
- Derive origin-to-origin pitch from the real bbox and any intended overlap.

2. Measure the real access geometry.
- If the usable connection is a via, record its bbox and center.
- If the usable connection is a rectangle, record the intended centerline and metal extent.

3. Compute route endpoints from those measured values.
- Example:
  - `contact_x = inst_origin_x + via_center_x`
  - `contact_y = inst_origin_y + via_center_y`
  - `horizontal_end_x = contact_x + wire_width / 2`

4. Recheck the result on the screenshot.
- Numeric alignment alone is not enough.
- A route can be mathematically centered yet still look wrong because the visible landing geometry is asymmetric.

## Screenshot Validation

For layout work, screenshot review is part of the implementation, not an optional follow-up.

Required loop:

1. edit
2. fit view
3. capture screenshot
4. inspect the image
5. only then state whether the geometry is correct

This is mandatory, not advisory.
After every screenshot is returned, perform a visual review before concluding success.

What to check in the image:
- labels are anchored on real metal, not floating beside it
- route heads do not overshoot the intended contact
- route heads do not connect only halfway into the intended contact
- elbows are full-width, not half-connected
- overlap-based arrays still preserve the intended independent routes
- no old shapes remain after regeneration
- no abnormal protrusions or obvious shorts are visible

If the screenshot disagrees with your coordinate arithmetic, trust the screenshot and revise the coordinate model.

## Transistor Geometry And Sizing

When a layout task depends on the real transistor shape, do not assume the schematic width/length parameters directly control the layout PCell.

Recommended workflow:

1. Read the single-device layout geometry first.
- Use `client.layout.read_geometry(lib, cell)` on the transistor layout master.
- Measure the true bbox before deriving array pitch, overlap, or routing clearance.

2. Inspect the layout CDF parameters before changing device size.
- Use `cdfGetBaseCellCDF(ddGetObj(...))` through `execute_skill(...)` when the layout parameter name is unclear.
- Many PDKs expose multiple width-like parameters such as `w`, `Wfg`, `multiwd`, `nf`, or `fingers`.

3. Verify which parameter actually changes the layout geometry.
- Create a temporary param instance with `dbCreateParamInstByMasterName(...)`.
- Compare the transformed bbox and terminal figures after changing one parameter at a time.
- Do not trust the instance property list alone. A parameter can be stored on the instance without affecting the layout shape.

4. Extract terminal landing shapes before routing.
- Probe transformed terminal figures or pin figures for `S`, `D`, and `G`.
- Use those transformed `M1` / `OD` bboxes to decide where vias and higher-metal routes should land.

Practical note from the tested `tsmcN28/nch_ulvt_mac` PCell:
- `w` was accepted as an instance property but did not resize the layout
- `Wfg` changed the actual layout width
- source/drain routing had to start from the local `M1` contact shapes, not from guessed coordinates
- for this PCell in live editing, `dbCreateParamInstByMasterName(...)` with inline param lists did not reliably produce the intended resized layout; creating the instance first and then applying `dbReplaceProp(inst "Wfg" "string" "0.5u")` / `dbReplaceProp(inst "l" "string" "30n")` was the working pattern
- unless the user explicitly asks for another size, default transistor layout sizing for this workflow should be `Wfg=0.5u` and `l=30n`
- unless the user explicitly asks for built-in gate contact experiments, do not set `polyContacts` by default
- reason: the tested `polyContacts` combinations for `nch_ulvt_mac` were not yet reduced to a stable, known-good recipe, and some combinations triggered `pcellEvalFailed`

For array construction:
- derive `row_pitch` from the measured device height plus the requested vertical gap
- derive `col_pitch` from measured left/right edge geometry, including dummy poly if overlap matters
- re-probe the device after changing width, because source/drain contact height may also change

## Source/Drain Routing Guidance

For transistor arrays, do not connect source and drain by sweeping a large `M1` rectangle across the device bodies.

Why this matters:
- device-local `M1` is usually the contact landing layer
- a wide `M1` strap across the array can accidentally short `S` and `D`
- the result can look visually connected while being electrically wrong

Preferred routing pattern:

1. Keep local `M1` short.
- Use `M1` only at the transistor contact landing shapes.
- Treat those shapes as access points, not as the global routing layer.

2. Jump to higher metals near the contacts.
- Route `S` and `D` on different metal layers whenever possible.
- Place vias close to the transformed source/drain `M1` landing shapes.

3. Move shared buses outside the device bodies.
- Put source and drain buses above, below, or outside the array boundary.
- Route out around the devices instead of crossing through the active region.

4. Verify via definitions from the techfile.
- Do not assume generic via names such as `VIA1`.
- Query `techGetTechFile(cv)~>viaDefs` or use `techFindViaDefByName(...)` first.

Practical note from the tested TSMC28 flow:
- `S` on `M2` and `D` on `M3` was a safer pattern than trying to keep both on `M1`
- routing had to start from the measured source/drain contact windows after resizing the device
- if `S` and `D` access points used the same y-coordinate, the `D` stacked-via path could hit the `S` metal and short the nets
- for `D` on `M3`, the route had to use explicit stacked transitions `M1 -> M2 -> M3`; jumping conceptually from `M1` to `M3` was not enough
- when a vertical drop meets a horizontal bus, stopping both paths exactly at the centerline can trigger both visual half-corners and real DRC issues (`M2.W.1`, `M2.S.1`, `G.4:*`). Extend the bus endpoint or the drop endpoint by half the wire width so the corner is geometrically full
- if DRC reports `G.4:*` on short metal edges together with width/spacing errors near a via landing, suspect a tiny jog created by the via enclosure plus a too-short path segment. A robust fix is often to remove the intermediate-layer jog entirely or to replace it with a real rectangle patch that satisfies min-width and min-area
- for the tested 4x NMOS row, the clean pattern was:
  - `S`: `M1 -> M2` via plus `M2` vertical drops and one horizontal `M2` bus with half-width endpoint extension
  - `D`: `M1 -> M2 -> M3` stacked via at the contact, a local `M2` patch for enclosure/area, and all longer routing on `M3`
- for the tested 6x NMOS row with right-side drain fanout:
  - `S` was kept as one shared lower `M2` bus
  - `D<0:5>` had to remain electrically isolated all the way to the right-side pin rail
  - do not merge all `D` routes into one upper horizontal spine unless the user explicitly wants the drains shorted together
  - when routing each `D` to a common right-side x-position, assign the horizontal channel heights in descending order from leftmost device to rightmost device
  - reason: if the left devices use the lowest channels and the right devices use the highest channels, the horizontal segment of one drain can be pierced by the vertical segment of another drain and short the nets
  - explicit geometric verification on the generated `M3` paths is required; do not trust the screenshot alone for drain fanout isolation
  - if the screenshot shows an L-corner with a missing square at the elbow, a half-width endpoint extension may still be visually insufficient; add an explicit corner rectangle patch on the routing layer
  - for this row pattern, the robust elbow recipe was:
    - one vertical `M3` path from the drain via landing to the assigned route y
    - one horizontal `M3` path from the route y to the right pin rail
    - one explicit `M3` corner rectangle centered at the elbow

## Implant Overlap Arrays

When building transistor rows with intentional dummy-poly overlap, do not assume the local implant layers can remain fragmented per-device.

Practical note from the tested `tsmcN28/nch_ulvt_mac` 4-device row:
- overlapping outer dummy PO reduced the effective origin-to-origin pitch, but leaving each device's `NP` isolated produced `NP.S.9` errors between neighbors
- the fix was to add one explicit top-level `NP` rectangle covering the whole device row, merging the per-device implant regions into one continuous region
- if DRC shows only top-level implant-spacing errors while the device instances themselves are otherwise clean, prefer adding the explicit shared implant cover before changing the transistor pitch

## Labels On Routed Nets

When placing labels on routed metal, do not drop them near the wire by eye.

Preferred pattern:
- place the label anchor directly on the intended metal shape
- for narrow buses, anchor the label on the centerline of the actual metal rectangle
- for vertical spines, place the anchor inside the spine so the Virtuoso cross marker overlaps the metal

Practical note from the tested array-routing flow:
- labels placed beside the route looked detached even if the text was nearby
- moving the anchor onto the metal spine fixed the display and made the net ownership visually unambiguous

## CFMOM Array Notes

For `tsmcN28/cfmom_2t`, do not assume transistor-like parameter names such as `l` / `nf`.

Verified CDF parameters that changed the layout geometry:
- `Lfinger`
- `Nfinger`

Practical note from the tested unary CFMOM CDAC flow:
- default `cfmom_2t` geometry was not the intended unit size for the user's array
- changing guessed names such as `l`, `length`, `nf`, or `fingers` did not change the layout bbox
- `dbReplaceProp(inst "Lfinger" "string" "2u")` and `dbReplaceProp(inst "Nfinger" "string" "12")` did change the geometry
- for the tested `R90` unit with `Lfinger=2u` and `Nfinger=12`, a placed instance bbox became `2.42 x 1.16`
- for the tested `R90` unit with `Lfinger=3u` and `Nfinger=8`, a placed instance bbox became `3.42 x 0.76`

Field-probing notes from direct `cfmom_2t` experiments:
- inline parameter creation through `dbCreateParamInst(...)` was confirmed to work for `cfmom_2t`
- inline parameter creation through `dbCreateParamInstByMasterName(...)` with an appended parameter list was not accepted in this flow and failed type checking
- parameters confirmed to change geometry:
  - `Wfinger`
  - `Sfinger`
  - `Ftip`
  - `Lfinger`
  - `Nfinger`
- measured `R0` single-parameter bbox changes:
  - `Wfinger=80n` -> `3.08 x 1.42`
  - `Sfinger=80n` -> `3.05 x 1.42`
  - `Ftip=200n` -> `2.36 x 1.62`
  - `Lfinger=3u` -> `2.36 x 3.42`
  - `Nfinger=8` -> `0.76 x 1.42`
- parameters confirmed writable and readable as instance properties without changing bbox in the tested setup:
  - `StartMn`
  - `StopMn`
  - `TFdme`
  - `OdPolyBlk`
  - `HardCons`
- `StopMn` did not appear as an instance property when left at its default; it did appear once explicitly changed to a non-default value
- the UI field `CapValue@0V_(F)` corresponds to CDF parameter `c`, but this was not proven to be a live per-instance capacitance readback:
  - `cdfGetInstCDF(inst)` returned the default `6.86047f`
  - `dbFindProp(inst "c")` returned `nil`
  - treat `c` as a displayed/default CDF field unless a callback-driven readback path is explicitly verified

Required workflow for `cfmom_2t` arrays:

1. Probe the CDF first.
- Use `cdfGetBaseCellCDF(ddGetObj("tsmcN28" "cfmom_2t"))`.
- Confirm the active geometry-driving parameter names before drawing the array.

2. Verify geometry with a temporary layout cell.
- Create one trial instance.
- Apply `dbReplaceProp(...)` for `Lfinger` / `Nfinger`.
- Open the trial layout window so the user can watch the probe.
- Read back the bbox with `client.layout.read_geometry(...)`.

3. Route to real plate metal after orientation is applied.
- Do not reuse `R0` coordinates after rotating the cap.
- For the tested vertical `R90` array, the transformed plate mapping was:
  - original `PLUS/TOP` at `y ~= 1.365` became the left plate at `x ~= -1.365`
  - original `MINUS/BOT` at `y ~= 0.055` became the right plate at `x ~= -0.055`
- The common `TOP` rail had to overlap the left metal stripe, not just run nearby.
- The successful `TOP` rail used width `0.11` and was placed directly on the transformed left plate stripe.
- The successful `BOT` breakout started from the transformed right plate stripe, not from a guessed x-coordinate near the edge.

4. Keep labels on metal, especially for dense fanout.
- If labels are placed beside the breakout, they will look disconnected.
- For vertical `CODE` trunks, place the label anchor directly on the vertical metal spine.
- If the bottom label region becomes crowded, remove decorative horizontal stubs before moving the label off-metal.

5. Keep the user's port-order wording literal.
- If they say the ports should be `y`-aligned and spread in `x`, use one common output `y` and fan out horizontally.
- If they say the ports should be `x`-aligned and spread in `y`, use one common output `x` and stack vertically.
- Do not "clean up" into the opposite convention just because it looks symmetric.

6. Prefer simple two-segment fanout over long polyline elbows.
- For the tested unary `BOT` breakout, one short horizontal segment from plate to target `x`, plus one vertical drop to the common output `y`, removed the visible jog that appeared with one long multi-corner path.
- If a corner still looks clipped, extend the horizontal segment by half the wire width into the corner or split the route into separate path objects.

Common failure modes from the tested CFMOM array work:
- using default `cfmom_2t` parameters and then wondering why the instances overlap
- guessing `l` / `nf` style names and assuming the PCell resized
- routing to the visual edge of the instance instead of the transformed plate metal
- misreading the rotated `R90` plate mapping and effectively swapping `TOP` / `BOT`
- putting `TOP` near the cap instead of overlapping the top-plate metal
- leaving the `TOP` collector hanging beside the capacitor plate instead of overlapping it
- leaving `CODE` labels floating outside the trunk metal
- adding a bottom horizontal label rail that creates clutter without improving connectivity
- batching too many path creations into one layout edit and hitting truncated SKILL payloads such as `*Error* eval: unbound variable dbCr`

## Mosaic Guidance

Use the direct mosaic API when you want one array object instead of many instances:

```lisp
dbCreateSimpleMosaic(cv master nil origin orient rows cols rowPitch colPitch)
```

Use the Python wrapper where possible:

```python
with client.layout.edit(lib, cell) as layout:
    layout.add_mosaic(
        lib,
        master_cell,
        origin=(0.0, 0.0),
        orientation="R0",
        rows=2,
        cols=4,
        row_pitch=row_pitch,
        col_pitch=col_pitch,
    )
```

For unit-cap tiling, `row_pitch` and `col_pitch` are origin-to-origin spacing, not edge gap.
If neighboring unit caps should overlap, compute:
- `col_pitch = master_width - side_vertical_metal_width`
- `row_pitch = master_height - top_or_bottom_horizontal_metal_thickness`

Do not guess overlap values. Derive them from the layout geometry of the unit cell.

Practical note from `LB_CUNIT`:
- the unit capacitor can be shoulder-overlapped horizontally
- dense unary placement used `col_pitch = master_width - overlap`
- this must still be verified visually after routing because dense overlap can make unrelated shapes look connected

## Layout Examples

- `examples/01_virtuoso/layout/01_create_layout.py`
- `examples/01_virtuoso/layout/02_add_polygon.py`
- `examples/01_virtuoso/layout/03_add_via.py`
- `examples/01_virtuoso/layout/04_multilayer_routing.py`
- `examples/01_virtuoso/layout/05_bus_routing.py`
- `examples/01_virtuoso/layout/06_read_layout.py`
- `examples/01_virtuoso/layout/07_screenshot.py`
- `examples/01_virtuoso/layout/08_delete_shapes_on_layer.py`
- `examples/01_virtuoso/layout/09_clear_routing.py`
- `examples/01_virtuoso/layout/10_clear_current_layout.py`
- `examples/01_virtuoso/layout/11_delete_cell.py`
- `examples/01_virtuoso/layout/12_add_unit_cap_mosaic.py`
- `examples/01_virtuoso/layout/13_add_overlapped_unit_cap_mosaic.py`

Experimental CDAC construction scripts should not live under `examples/`.
Keep one-off or evolving layout generators under `playground/virtuoso/layout/`, and keep only the reusable method and pitfalls in the skill references.
