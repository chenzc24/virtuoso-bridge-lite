# T28 Metal Rule Notes

Use this reference when a Virtuoso layout task needs a quick, verified subset of T28 metal DRC rules without opening the full Calibre rule deck.

Scope:
- verified from the site Calibre DRC rule deck for TSMC 28nm (path set via `DRC_RULE_FILE` in `.env`)
- currently records only the M2 rules that were checked during the Mona Lisa metal-art flow
- values below are specific rule snippets, not a complete substitute for the full deck

## M2 Core Rules

- `M2.W.1`: minimum width `>= 0.05 um`
- `M2.W.3`: maximum width `<= 4.5 um`
- `M2.A.2`: minimum area `>= 0.014 um^2`
- `M2.A.3`: minimum area `>= 0.044 um^2` when all edge lengths are `< 0.13 um`
- `M2.S.1`: minimum space `>= 0.05 um`

## M2 Conditional Spacing

- `M2.S.2`: space `>= 0.06 um`
  Condition: at least one line width `> 0.09 um` and parallel run length `> 0.22 um`
- `M2.S.3`: space `>= 0.10 um`
  Condition: at least one line width `> 0.16 um` and parallel run length `> 0.22 um`
- `M2.S.4`: space `>= 0.13 um`
  Condition: at least one line width `> 0.47 um` and parallel run length `> 0.47 um`
- `M2.S.5`: space `>= 0.15 um`
  Condition: at least one line width `> 0.63 um` and parallel run length `> 0.63 um`
- `M2.S.6`: space `>= 0.50 um`
  Condition: at least one line width `> 1.5 um` and parallel run length `> 1.5 um`

## M2 Related Special Cases

- `LOWMEDN.W.3:M2`: width of `{M2 OR DM2_O} AND LOWMEDN` `>= 0.14 um`
- `LOWMEDN.S.3:M2`: space of `{M2 OR DM2_O} AND LOWMEDN` `>= 0.14 um`
- `M2.A.4`: enclosed area `>= 0.2 um^2`
  Note: this is not a generic maximum-area rule for ordinary M2 polygons

## Interpretation Notes

- For ordinary artwork-style rectangles, the safe baseline is:
  - width `>= 0.05 um`
  - spacing `>= 0.05 um`
  - area `>= 0.014 um^2`
- Do not assume M2 has one single spacing rule. Wider and longer parallel runs trigger larger spacing requirements.
- Do not claim there is a simple standalone “maximum M2 area” rule unless the full rule context has been checked again. In the verified subset above, the clear hard limit is maximum width, not a generic polygon area cap.
- If a task depends on voltage-dependent spacing, via enclosure, density, or dummy-metal limits, reopen the full deck or extend this reference with those exact clauses first.
