# Metal Pixel Art Reference

Use this reference when the user wants an image, portrait, icon, or decorative artwork drawn in Virtuoso layout with metal layers.

This method is for visual metal-art generation, not functional routing.

## Default Workflow

Use this order:

1. Check the metal color card first.
- Verify how `M1` through the target top metal are actually displayed in the current Virtuoso layer palette.
- Do not assume the visible colors match the intended brightness order.
- If no color card asset exists yet, create one fixed library asset cell once, with visible labels on every patch, then capture a screenshot and cache the sampled palette before mapping the artwork.
- Preferred fixed asset coverage for future reuse: `PO`, `OD`, and `M1` through `M9`.
- Do not regenerate the color card for every portrait run unless the display palette changed or the cached screenshot/palette is stale.
- The color card should be a fixed library asset cell, not a timestamped scratch cell.
- If that fixed cell already exists, reopen it with overwrite behavior and regenerate in place instead of creating another cell.
- Put a visible text label next to each swatch so later runs can identify the layer unambiguously.

2. Choose pixel size and pitch.
- If the user specifies a target size, derive the grid from that size.
- If the user specifies a target resolution, derive the physical size from that resolution.
- If the user specifies only a long-side resolution, preserve the source image aspect ratio and derive the short side automatically.
- If the user does not specify a size, use this default:
  - square size: `0.2 um x 0.2 um`
  - x pitch: `0.4 um`
  - y pitch: `0.4 um`

3. Pixelate the source image.
- Crop away decorative frames or margins unless the user explicitly wants them preserved.
- Downsample to a coarse grid first.
- Prefer stable rectangular pixels over freeform polygons.
- Quantize tones to the number of usable metal-display buckets, not necessarily the number of available metals.
- Do not assume two different artworks should use the same aspect ratio or the same palette subset.
- When the user approves a specific visual result, preserve the exact matrix file for replay instead of trying to recreate the look from memory.

4. Map tones to metal layers.
- Choose the layer mapping after looking at the color card screenshot.
- If two metal layers look too similar, do not force both into the palette.
- If the visible palette is weak, use a second control dimension such as fill ratio or sparse-vs-solid patterning.
- Do not assume metal numbers imply a brightness order. Use the color card screenshot, not intuition.
- `OD` is red and should be considered for paintings with red or orange highlights.
- `PO` is a useful strong blue anchor for seascapes, skies, and other blue-dominant paintings.
- Avoid manual semantic rules such as hard-coded face, hand, sky, or background masks unless the user explicitly asks for them.
- Prefer one global mapping rule per artwork unless there is a clear user-approved reason to do otherwise.

5. Generate layout conservatively.
- Default to `drawing` purpose.
- Prefer `add_rect(...)` for each pixel block.
- Avoid vias unless the artwork intentionally needs stacked-color overlap behavior.
- For large artwork, prefer an `.il` helper or a generated `.il` file loaded once rather than issuing per-rect SKILL calls.
- When the artwork is dense, put the heavy shape-generation body in the `.il` file and keep the Python side limited to parameter preparation, file upload, and one short entrypoint call.
- Prefer a matrix text file plus a short IL entrypoint over generating giant inline SKILL or giant `.il` files full of expanded `dbCreateRect(...)` calls.
- Reuse the same helper IL and vary only the uploaded matrix and a short render call.
- Create each artwork in its own cell. Do not stack multiple paintings into one layout unless the user explicitly asks for a collage.
- When regenerating an artwork, open the target cell in overwrite mode so the previous contents are cleared before redraw.
- Do not read back giant pixel-art layouts just to inspect them. Use the saved matrix, screenshot, and local preview artifacts instead.

6. Validate visually, then run DRC.
- Capture a screenshot and compare the major facial / shape landmarks against the reference image.
- Only after screenshot review should the artwork be described as correct.
- Run DRC after the first stable visual pass, then adjust size / spacing if needed.
- Virtuoso screenshots can include overlapping windows. When that happens, also generate a local preview PNG from the matrix file and cached palette so the artwork can be inspected without window clutter.

## Sizing Guidance

- Start coarse, then refine.
- A first-pass portrait or painting should bias toward larger pitch and fewer pixels rather than chasing detail too early.
- If DRC is the primary goal, increase square size and keep generous spacing before increasing resolution.
- If visual fidelity is the primary goal, improve the metal palette mapping before increasing pixel count.
- If the user says the detail is missing, increase resolution only after confirming the palette and mapping are not the real bottleneck.

## DRC Bias

For conservative initial artwork:
- use simple axis-aligned rectangles
- keep one pixel as one rectangle unless pattern fill is needed
- leave visible spacing between neighboring pixels
- if the user wants DRC-safe square mosaics, make the gap equal to the square width in both x and y, which means `pitch = 2 x square_size`
- avoid tiny isolated fragments created by aggressive thresholding
- if the user wants a full black background, represent black as no-draw (`.`) rather than forcing an extra dark layer unless the process explicitly needs a drawn background

If DRC starts failing:
- increase square size
- increase pitch
- merge small islands
- reduce resolution before introducing more complex geometry

## Practical Notes

- The color-card step is mandatory for appearance-driven artwork. Without it, the chosen metal mapping is mostly guesswork.
- For large generated paintings, the heavy loop should run inside Virtuoso through `.il` or through small editor chunks.
- Do not claim the result is visually correct from geometry alone; always inspect the screenshot.
- Keep all one-off artwork scripts, helpers, source images, matrices, and output files together in the dedicated workspace area the user chose, rather than scattering them across generic example folders.
