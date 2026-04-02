# CDAC Reference

## When To Use

Use this reference when building a CDAC from either:
- a custom capacitor unit cell such as `PLAYGROUND_LLM/LB_CUNIT`
- a PDK capacitor PCell such as `tsmcN28/cfmom_2t`

Typical cases:
- unary CDAC arrays
- binary-weighted cap arrays
- dense unit-cap tiling with overlap
- custom top/bottom plate routing from a proprietary MOM or metal fringe cell
- PDK CFMOM arrays that need explicit parameter probing and plate-aware routing

## First Principle

Do not infer the usable connection point from the symbol name, pin label location, or schematic connectivity alone.

For any unit capacitor, always inspect:
- layout bbox
- shape layers
- pin labels
- via bboxes
- any internal landing metals intended for routing

## Common Inspection Flow

1. Open the master layout and schematic.
- Confirm what the schematic says is `TOP` and `BOT`.
- Confirm what the layout actually exposes for routing.

2. Read the master geometry.
- Use `client.layout.read_geometry(lib, cell)` for a quick dump.
- If needed, use raw SKILL on `cv~>shapes`, `cv~>vias`, and `cv~>instances`.

3. Identify the real routing landing geometry.
- A pin label in the middle of the cell does not guarantee that the visible routing landing is there.
- Many custom caps expose routing through internal vias or local strap heads.

4. Derive pitch from geometry, not assumption.
- If the unit cell is meant to overlap, measure the actual overlap-compatible pitch from the real side metals.

## Unary CDAC Construction Pattern

For a 4-bit unary CDAC with 16 unit caps:

1. Place 16 instances in one row or one column, depending on the requested breakout style.
- Prefer one row when the user wants horizontal `CODE` breakout.
- Prefer one column when the user wants vertical `CODE` trunks.

2. Short the top plates with one simple common route.
- Keep the top connection visually obvious.
- Avoid decorative trunks or unnecessary corners.

3. Route each bottom plate independently.
- For same-layer routing, use one vertical segment and one horizontal segment to form an L-shape.
- Keep each route tied to the real bottom access centerline.

4. Keep labels on the real bus metal.
- Do not leave the label floating outside the routed shape.

## Binary CDAC Construction Pattern

For a binary CDAC built from unit capacitors:

1. Decide the layout intent first.
- weighted blocks are simpler to route and debug
- common-centroid placement gives better matching but needs a separate breakout plan

2. Keep placement and breakout as separate phases.
- first prove the placement is correct
- then design isolated breakout channels
- do not mix an unproven common-centroid placement with ad hoc bottom routing

3. For weighted-block binary layouts, avoid reusing the same routing column for different bits.
- if different bits share the same vertical path corridor, they can short immediately
- assign disjoint routing corridors or disjoint routing layers before drawing the first bus

4. For common-centroid binary layouts, start with placement-only.
- use an `8 x 8` matrix for `6 bit = 63 + 1 dummy`
- distribute `32/16/8/4/2` in symmetric pairs
- put `1 bit` and `dummy` at the most central pair
- only add breakout after reserving explicit isolated channels

## Custom Unit Notes: `LB_CUNIT`

For `PLAYGROUND_LLM/LB_CUNIT`:
- the cell can be placed shoulder-to-shoulder with horizontal overlap
- the top plate is naturally collected on the upper metal head
- the bottom routing should align to the internal `M3` via center used as the real access point
- routing to the `M6` pin label center or to a guessed lower edge point was wrong
- bottom breakout must be taken from `M3`, not from `M5/M6/M7`
- reason: inside this custom MOM cell, `M5/M6/M7` contain interleaved top/bottom plate structures, so treating those upper metals as an exposed bottom-plate escape layer can create shorts or false-looking connections

Measured facts that mattered:
- master bbox: `((-0.225, 0.02), (0.225, 1.19))`
- dense horizontal pitch used successfully: `0.400`
- bottom access via center was around `y = 0.605`

Practical unary pattern:
- a 4-bit unary CDAC is naturally `16` unit caps
- if the user wants "one row, 16 lines horizontal", place the units in one row and draw independent L-shaped bottom routes
- if the user asks for a vertical unary column, keep the `16` unit interpretation; do not silently collapse it to `4` physical caps
- if the unit exposes a real internal via landing, align the route centerline to that via center instead of the pin text
- if the unit is `LB_CUNIT`, do not promote the bottom breakout to `M5/M6/M7`; keep the breakout on `M3` until it is safely outside the capacitor body

## PDK CFMOM Notes: `cfmom_2t`

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

Field-availability notes from direct probing:
- the CDF parameters that were confirmed to change layout geometry are:
  - `Wfinger`
  - `Sfinger`
  - `Ftip`
  - `Lfinger`
  - `Nfinger`
- measured `R0` bbox changes from single-parameter probes:
  - `Wfinger=80n` -> `3.08 x 1.42`
  - `Sfinger=80n` -> `3.05 x 1.42`
  - `Ftip=200n` -> `2.36 x 1.62`
  - `Lfinger=3u` -> `2.36 x 3.42`
  - `Nfinger=8` -> `0.76 x 1.42`
- parameters that were confirmed to be accepted and stored on the instance but did not change bbox in the tested setup:
  - `StartMn`
  - `StopMn`
  - `TFdme`
  - `OdPolyBlk`
  - `HardCons`
- parameters that were confirmed readable from `dbFindProp(inst ...)` after being set:
  - `Wfinger`
  - `Sfinger`
  - `Ftip`
  - `Lfinger`
  - `Nfinger`
  - `StartMn`
  - `StopMn` when changed away from its default
  - `TFdme`
  - `OdPolyBlk`
  - `HardCons`
- `StopMn` is not reliable as an instance property when left at the default value; if you need to confirm it through `dbFindProp`, set it explicitly to a non-default first
- the CDF field `c` maps to the UI label `CapValue@0V_(F)`, but in the tested flow:
  - `cdfGetInstCDF(inst)` returned the default CDF value `6.86047f`
  - `dbFindProp(inst "c")` returned `nil`
  - therefore `c` should not be treated as a proven per-instance live capacitance readback yet
- `dbCreateParamInst(...)` with an inline parameter list was proven to work for `cfmom_2t`
- `dbCreateParamInstByMasterName(...)` with an extra inline parameter list was not accepted in this flow and failed type checking

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
- The common `TOP` rail had to overlap the transformed left plate stripe, not just run nearby.
- The successful `TOP` rail used width `0.11` and was placed directly on the transformed left plate stripe.
- The successful `BOT` breakout started from the transformed right plate stripe, not from a guessed x-coordinate near the edge.

4. Keep labels on metal, especially for dense fanout.
- If labels are placed beside the breakout, they will look disconnected.
- For vertical `CODE` trunks, place the label anchor directly on the vertical metal spine.
- If the bottom label region becomes crowded, remove decorative horizontal stubs before moving the label off-metal.

5. Preserve intended gaps after parameter changes.
- If `Lfinger` / `Nfinger` are changed, re-probe the rotated bbox first and keep the user's requested edge gap explicit.
- In the tested `R90` unary column, keeping a `0.4um` cell-to-cell gap meant recomputing the origin pitch from the new rotated height, not reusing the old pitch.

6. Make the breakout order explicit before routing.
- If the user says the output ports should be `y`-aligned and `x`-spread, route all `BOT` ports to one common bottom `y` and fan them out in `x`.
- If the user says the output ports should be `x`-aligned and `y`-spread, use one common side `x` and stack the ports vertically.
- Do not switch between those two interpretations mid-iteration.

7. Avoid one giant routing payload for dense unary arrays.
- For a `16`-unit rotated CFMOM column with separate `TOP` and `BOT` routing, sending all paths in one edit block can truncate the request and produce misleading errors such as `*Error* eval: unbound variable dbCr`.
- Split the routing into smaller batches, for example one `TOP` pass plus `BOT` chunks of `4` units.

## Path vs Rect For CDAC Routing

Default recommendation:
- use `path` for plate escape wires and buses

Why:
- analog routing is usually defined by centerlines and widths
- path-based edits are easier to retarget when pitch or access coordinates change
- the corner issue can be solved by extending the horizontal segment by half the wire width

Use `rect` only when:
- you need a deliberately oversized landing pad
- you need exact rectangular fill geometry
- a path corner visually or electrically cannot express the intended shape

## What Belongs In Skill vs Playground

Keep these in the skill/reference:
- how to measure custom-unit overlap and access geometry
- how to choose between weighted-block and common-centroid placement
- how to align plate routing to the real landing metal
- how to validate elbows, labels, and shorts from screenshots
- working parameter names for PDK cap PCells that were empirically verified

Keep these in `playground/virtuoso/layout/`:
- one-off layout generators
- temporary CDAC builders under active iteration
- scripts tied to a specific experiment or cell naming convention

## Failure Modes To Avoid

- connecting to a pin label instead of the real landing metal
- using `M5/M6/M7` as the first bottom breakout layer on `LB_CUNIT`
- using default `cfmom_2t` parameters and then wondering why the instances overlap
- guessing `l` / `nf` style names for `cfmom_2t` and assuming the PCell resized
- routing to the visual edge of the instance instead of the transformed plate metal
- mis-mapping the rotated `R90` plates and shorting the right-side `BOT` breakout into the left-side `TOP` collector
- putting `TOP` near the cap instead of overlapping the top-plate metal
- leaving the common `TOP` collector floating beside the plate instead of overlapping it
- leaving `CODE` labels floating outside the routed shape
- building `BOT` fanout with the wrong alignment convention (`x`-aligned vs `y`-aligned) relative to the user's stated port order
- drawing a long multi-segment `BOT` path that leaves an ugly jog at the elbow when a cleaner two-segment route would work
- adding a bottom horizontal label rail that creates clutter without improving connectivity
- using extra vias to compensate for wrong coordinates
- trusting numeric coordinates without screenshot review
- regenerating on top of old shapes or old instances
- claiming success before checking the image

## Required Final Check

Before closing the task:

1. fit the layout window
2. capture a screenshot
3. run an explicit short-check between the newly added routes and the plate metal that must remain isolated
- for custom unit caps, use the measured master geometry and the routed-shape geometry
- for PDK cap PCells, use the measured transformed plate metal and the routed-shape geometry
- do not rely only on the screenshot for short detection
- if only a geometric short-check was possible, say so explicitly
4. inspect whether:
- the route head fully lands on the intended access point
- the common plate rail really overlaps the intended plate metal
- the elbow is full-width
- the label is on metal
- there are no leftover shapes from old attempts
