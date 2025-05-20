# Control

The **Control** class provides functionality to manipulate vessel controls in Kerbal Space Program. This includes adjusting the throttle, enabling/disabling systems like SAS and RCS, and controlling vessel orientation. It is obtained by calling `Vessel.control`.

## Quick usage
```python
import krpc
conn = krpc.connect()
vessel = conn.space_center.active_vessel
control = vessel.control
control.throttle = 1.0
control.sas = True
```

## Core Properties

### Control State
- `source` (ControlSource, read-only) - Source of vessel control
- `state` (ControlState, read-only) - Current control state
- `input_mode` (ControlInputMode, read/write) - Behavior of control inputs

### Flight Control Systems
- `sas` (bool, read/write) - SAS state
- `sas_mode` (SASMode, read/write) - Current SAS mode
- `speed_mode` (SpeedMode, read/write) - Navball speed mode
- `rcs` (bool, read/write) - RCS state
- `reaction_wheels` (bool, read/write) - Reaction wheels state

### Landing Systems
- `gear` (bool, read/write) - Landing gear state
- `legs` (bool, read/write) - Landing legs state
- `wheels` (bool, read/write) - Wheels state
- `brakes` (bool, read/write) - Wheel brakes state

### Vessel Systems
- `lights` (bool, read/write) - Lights state
- `antennas` (bool, read/write) - Antennas state
- `cargo_bays` (bool, read/write) - Cargo bays state
- `intakes` (bool, read/write) - Air intakes state
- `parachutes` (bool, read/write) - Parachutes state
- `radiators` (bool, read/write) - Radiators state

### Resource Systems
- `resource_harvesters` (bool, read/write) - Resource harvester deployment
- `resource_harvesters_active` (bool, read/write) - Resource harvester activity
- `solar_panels` (bool, read/write) - Solar panels state

## Control Inputs

### Main Controls
- `throttle` (float, read/write) - Throttle level (0 to 1)
- `abort` (bool, read/write) - Abort action group state

### Attitude Control
- `pitch` (float, read/write) - Pitch control (-1 to 1)
- `yaw` (float, read/write) - Yaw control (-1 to 1)
- `roll` (float, read/write) - Roll control (-1 to 1)

### Translation Control
- `forward` (float, read/write) - Forward translation (-1 to 1)
- `up` (float, read/write) - Up translation (-1 to 1)
- `right` (float, read/write) - Right translation (-1 to 1)

### Wheel Control
- `wheel_throttle` (float, read/write) - Wheel throttle (-1 to 1)
- `wheel_steering` (float, read/write) - Wheel steering (-1 to 1)

### Custom Controls
- `custom_axis01` (float, read/write) - Custom axis 1 (-1 to 1)
- `custom_axis02` (float, read/write) - Custom axis 2 (-1 to 1)
- `custom_axis03` (float, read/write) - Custom axis 3 (-1 to 1)
- `custom_axis04` (float, read/write) - Custom axis 4 (-1 to 1)

## Staging

### Stage Properties
- `current_stage` (int, read-only) - Current stage number
- `stage_lock` (bool, read/write) - Stage lock state

### Stage Methods
- `activate_next_stage()` - Activate next stage
- `get_action_group(group)` - Get action group state
- `set_action_group(group, state)` - Set action group state
- `toggle_action_group(group)` - Toggle action group state

## Maneuver Nodes

### Node Properties
- `nodes` (list[Node], read-only) - List of maneuver nodes

### Node Methods
- `add_node(ut, prograde=0.0, normal=0.0, radial=0.0)` - Create maneuver node
- `remove_nodes()` - Remove all maneuver nodes

## Enums

### ControlState
- `full` - Full controllable
- `partial` - Partially controllable
- `none` - Not controllable

### ControlSource
- `kerbal` - Controlled by Kerbal
- `probe` - Controlled by probe core
- `none` - Not controlled

### SASMode
- `stability_assist` - Stability assist mode
- `maneuver` - Point to maneuver direction
- `prograde` - Point prograde
- `retrograde` - Point retrograde
- `normal` - Point normal
- `anti_normal` - Point anti-normal
- `radial` - Point radial
- `anti_radial` - Point anti-radial
- `target` - Point to target
- `anti_target` - Point away from target

### SpeedMode
- `orbit` - Speed relative to orbit
- `surface` - Speed relative to surface
- `target` - Speed relative to target

### ControlInputMode
- `additive` - Add to current inputs
- `override` - Override current inputs 