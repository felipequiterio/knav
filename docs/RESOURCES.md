# Resources

The **Resources** class represents the collection of resources stored in a vessel, stage, or part in Kerbal Space Program. It is obtained by calling `Vessel.resources`, `Vessel.resources_in_decouple_stage()`, or `Part.resources`.

## Quick usage
```python
import krpc
conn = krpc.connect()
vessel = conn.space_center.active_vessel
resources = vessel.resources
print(f"Available resources: {resources.names}")
print(f"Liquid fuel amount: {resources.amount('LiquidFuel')}")
```

## Core Properties

### Resource Lists
- `all` (list[Resource], read-only) - All individual resources that can be stored
- `names` (list[str], read-only) - List of resource names that can be stored

### Resource Queries
- `with_resource(name)` - List of resources with given name
- `has_resource(name)` - Check if named resource can be stored
- `amount(name)` - Current amount of stored resource
- `max(name)` - Maximum amount that can be stored
- `density(name)` - Resource density in kg/l
- `flow_mode(name)` - Resource flow mode

### Resource Control
- `enabled` (bool, read/write) - Whether use of all resources is enabled

## Resource Class

The **Resource** class represents an individual resource stored within a part.

### Basic Properties
- `name` (str, read-only) - Resource name
- `part` (Part, read-only) - Part containing the resource
- `amount` (float, read-only) - Current amount stored
- `max` (float, read-only) - Maximum amount that can be stored
- `density` (float, read-only) - Resource density in kg/l
- `flow_mode` (ResourceFlowMode, read-only) - Resource flow mode
- `enabled` (bool, read/write) - Whether use of this resource is enabled

## ResourceTransfer Class

The **ResourceTransfer** class handles resource transfers between parts.

### Properties
- `amount` (float, read-only) - Amount of resource transferred
- `complete` (bool, read-only) - Whether transfer has completed

### Methods
- `start(from_part, to_part, resource, max_amount)` - Start resource transfer between parts

## Enums

### ResourceFlowMode
- `vessel` - Resource flows to any part in vessel (e.g., electric charge)
- `stage` - Resource flows from first stage, then second, etc. (e.g., mono-propellant)
- `adjacent` - Resource flows between adjacent parts (e.g., liquid fuel)
- `none` - Resource does not flow (e.g., solid fuel) 