# Node

The **Node** class represents a maneuver node in Kerbal Space Program. It can be created using `Control.add_node()` and provides functionality to manipulate and execute orbital maneuvers.

## Quick usage
```python
import krpc
conn = krpc.connect()
vessel = conn.space_center.active_vessel
node = vessel.control.add_node(conn.space_center.ut + 60, prograde=100)
print(f"Delta-v: {node.delta_v} m/s")
print(f"Time to burn: {node.time_to} seconds")
```

## Core Properties

### Delta-V Components
- `prograde` (float, read/write) - Delta-v in prograde direction (m/s)
- `normal` (float, read/write) - Delta-v in normal direction (m/s)
- `radial` (float, read/write) - Delta-v in radial direction (m/s)
- `delta_v` (float, read/write) - Total delta-v of maneuver (m/s)
- `remaining_delta_v` (float, read-only) - Remaining delta-v during execution (m/s)

### Time Properties
- `ut` (float, read/write) - Universal time of maneuver (s)
- `time_to` (float, read-only) - Time until maneuver (s)

### Orbital Properties
- `orbit` (Orbit, read-only) - Resulting orbit after maneuver
- `reference_frame` (ReferenceFrame, read-only) - Frame fixed relative to burn
- `orbital_reference_frame` (ReferenceFrame, read-only) - Frame aligned with orbital directions

## Methods

### Burn Vectors
- `burn_vector([reference_frame])` - Get burn vector in specified frame
- `remaining_burn_vector([reference_frame])` - Get remaining burn vector during execution

### Position and Direction
- `position(reference_frame)` - Get position vector in specified frame
- `direction(reference_frame)` - Get burn direction as unit vector

### Node Management
- `remove()` - Remove the maneuver node

## Reference Frames

### Node Reference Frame
The reference frame fixed relative to the maneuver node's burn:
- Origin: Position of maneuver node
- Y-axis: Direction of burn
- X-axis and Z-axis: Arbitrary but fixed directions

### Orbital Reference Frame
The reference frame fixed relative to the maneuver node, oriented with orbital directions:
- Origin: Position of maneuver node
- X-axis: Orbital anti-radial direction
- Y-axis: Orbital prograde direction
- Z-axis: Orbital normal direction 