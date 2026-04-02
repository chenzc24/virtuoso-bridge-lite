# Schematic Reference

## Primary Surfaces

- namespace API: `client.schematic`
- declarative editor: `SchematicEditor` from `client.schematic.edit(...)`

Prefer pattern:

```python
with client.schematic.edit(lib, cell) as schematic:
    schematic.add_instance(...)
    schematic.add_pin(...)
    schematic.add_net_label_to_instance_term(...)
```

## Namespace API

- `client.schematic.edit(...)`
- `client.schematic.open(...)`
- `client.schematic.save(...)`
- `client.schematic.check(...)`
- `client.schematic.add_instance(...)`
- `client.schematic.add_wire(...)`
- `client.schematic.add_label(...)`
- `client.schematic.add_pin(...)`
- `client.schematic.add_pin_to_instance_term(...)`
- `client.schematic.add_wire_between_instance_terms(...)`
- `client.schematic.add_net_label_to_instance_term(...)`

## Editor Methods

- `add_instance(...)`
- `add_wire(...)`
- `add_label(...)`
- `add_pin(...)`
- `add_pin_to_instance_term(...)`
- `add_wire_between_instance_terms(...)`
- `add_net_label_to_instance_term(...)`

## Guidance

- prefer `schematic` as the local variable name, not `sch`
- use terminal-aware helpers before guessing coordinates
- if a missing schematic primitive is needed, add a formal builder in `src/virtuoso_bridge/virtuoso/schematic/ops.py`
- use namespace helpers for one-off direct actions; use `SchematicEditor` for multi-step edits

## Schematic Examples

- `examples/01_virtuoso/schematic/01_execute_operations.py`
- `examples/01_virtuoso/schematic/02_read_connectivity.py`
- `examples/01_virtuoso/schematic/03_create_rc.py`
- `examples/01_virtuoso/schematic/04_create_inverter.py`
- `examples/01_virtuoso/schematic/05_create_cellview.py`
- `examples/01_virtuoso/schematic/06_read_instance_params.py`
- `examples/01_virtuoso/schematic/07_export_netlist_cdl.py`
- `examples/01_virtuoso/schematic/08_rename_instance.py`
- `examples/01_virtuoso/schematic/09_delete_instance.py`
- `examples/01_virtuoso/schematic/10_delete_cell.py`
- `examples/01_virtuoso/schematic/11_screenshot.py`
