# Parts

The **Parts** class provides functionality to interact with the individual parts of a vessel in Kerbal Space Program. It is obtained by calling `Vessel.parts` and allows you to access and manipulate all parts of a vessel.

## Quick usage
```python
import krpc
conn = krpc.connect()
vessel = conn.space_center.active_vessel
parts = vessel.parts
print(f"Total parts: {len(parts.all)}")
print(f"Root part: {parts.root.title}")
```

## Core Properties

### Part Lists
- `all` (list[Part], read-only) - List of all vessel parts
- `root` (Part, read-only) - Vessel's root part
- `controlling` (Part, read/write) - Part from which vessel is controlled

### Part Queries
- `with_name(name)` - List of parts with given name
- `with_title(title)` - List of parts with given title
- `with_tag(tag)` - List of parts with given tag
- `with_module(module_name)` - List of parts containing given module
- `in_stage(stage)` - List of parts activated in given stage
- `in_decouple_stage(stage)` - List of parts decoupled in given stage
- `modules_with_name(module_name)` - List of modules with given name

### Part Type Lists
- `antennas` (list[Antenna], read-only) - All antennas
- `cargo_bays` (list[CargoBay], read-only) - All cargo bays
- `control_surfaces` (list[ControlSurface], read-only) - All control surfaces
- `decouplers` (list[Decoupler], read-only) - All decouplers
- `docking_ports` (list[DockingPort], read-only) - All docking ports
- `engines` (list[Engine], read-only) - All engines
- `experiments` (list[Experiment], read-only) - All science experiments
- `fairings` (list[Fairing], read-only) - All fairings
- `intakes` (list[Intake], read-only) - All intakes
- `legs` (list[Leg], read-only) - All landing legs
- `launch_clamps` (list[LaunchClamp], read-only) - All launch clamps
- `lights` (list[Light], read-only) - All lights
- `parachutes` (list[Parachute], read-only) - All parachutes
- `radiators` (list[Radiator], read-only) - All radiators
- `resource_drains` (list[ResourceDrain], read-only) - All resource drains
- `rcs` (list[RCS], read-only) - All RCS blocks/thrusters
- `reaction_wheels` (list[ReactionWheel], read-only) - All reaction wheels
- `resource_converters` (list[ResourceConverter], read-only) - All resource converters
- `resource_harvesters` (list[ResourceHarvester], read-only) - All resource harvesters
- `robotic_hinges` (list[RoboticHinge], read-only) - All robotic hinges
- `robotic_pistons` (list[RoboticPiston], read-only) - All robotic pistons
- `robotic_rotations` (list[RoboticRotation], read-only) - All robotic rotations
- `robotic_rotors` (list[RoboticRotor], read-only) - All robotic rotors
- `sensors` (list[Sensor], read-only) - All sensors
- `solar_panels` (list[SolarPanel], read-only) - All solar panels
- `wheels` (list[Wheel], read-only) - All wheels

## Part Class

The **Part** class represents an individual part of a vessel.

### Basic Properties
- `name` (str, read-only) - Internal part name
- `title` (str, read-only) - Part title
- `tag` (str, read/write) - Part name tag
- `flag_url` (str, read/write) - Part flag URL
- `highlighted` (bool, read/write) - Part highlight state
- `highlight_color` (tuple[float, float, float], read/write) - Highlight color
- `cost` (float, read-only) - Part cost in funds
- `vessel` (Vessel, read-only) - Parent vessel

### Tree Properties
- `parent` (Part, read-only) - Parent part
- `children` (list[Part], read-only) - Child parts
- `axially_attached` (bool, read-only) - Whether axially attached
- `radially_attached` (bool, read-only) - Whether radially attached

### Staging Properties
- `stage` (int, read-only) - Activation stage
- `decouple_stage` (int, read-only) - Decoupling stage

### Physical Properties
- `massless` (bool, read-only) - Whether part is massless
- `mass` (float, read-only) - Current mass including resources
- `dry_mass` (float, read-only) - Mass without resources
- `shielded` (bool, read-only) - Whether part is shielded
- `dynamic_pressure` (float, read-only) - Dynamic pressure in Pascals
- `impact_tolerance` (float, read-only) - Impact tolerance in m/s

### Thermal Properties
- `temperature` (float, read-only) - Part temperature in Kelvin
- `skin_temperature` (float, read-only) - Skin temperature in Kelvin
- `max_temperature` (float, read-only) - Maximum temperature in Kelvin
- `max_skin_temperature` (float, read-only) - Maximum skin temperature in Kelvin
- `thermal_mass` (float, read-only) - Thermal mass in J/K
- `thermal_skin_mass` (float, read-only) - Skin thermal mass in J/K
- `thermal_resource_mass` (float, read-only) - Resource thermal mass in J/K
- `thermal_conduction_flux` (float, read-only) - Conduction heat flux in Watts
- `thermal_convection_flux` (float, read-only) - Convection heat flux in Watts
- `thermal_radiation_flux` (float, read-only) - Radiation heat flux in Watts
- `thermal_internal_flux` (float, read-only) - Internal heat flux in Watts
- `thermal_skin_to_internal_flux` (float, read-only) - Skin-to-internal heat flux in Watts

### Crew Properties
- `available_seats` (int, read-only) - Number of open seats
- `resources` (Resources, read-only) - Part resources

### Fuel Properties
- `crossfeed` (bool, read-only) - Whether part is crossfeed capable
- `is_fuel_line` (bool, read-only) - Whether part is a fuel line
- `fuel_lines_from` (list[Part], read-only) - Parts connected via fuel lines
- `fuel_lines_to` (list[Part], read-only) - Parts receiving fuel

### Module Properties
- `modules` (list[Module], read-only) - Part modules

### Part Type Properties
- `antenna` (Antenna, read-only) - Antenna if applicable
- `cargo_bay` (CargoBay, read-only) - Cargo bay if applicable
- `control_surface` (ControlSurface, read-only) - Control surface if applicable
- `decoupler` (Decoupler, read-only) - Decoupler if applicable
- `docking_port` (DockingPort, read-only) - Docking port if applicable
- `engine` (Engine, read-only) - Engine if applicable
- `experiment` (Experiment, read-only) - Experiment if applicable
- `experiments` (list[Experiment], read-only) - All experiments
- `fairing` (Fairing, read-only) - Fairing if applicable
- `intake` (Intake, read-only) - Intake if applicable
- `leg` (Leg, read-only) - Landing leg if applicable
- `launch_clamp` (LaunchClamp, read-only) - Launch clamp if applicable
- `light` (Light, read-only) - Light if applicable
- `parachute` (Parachute, read-only) - Parachute if applicable
- `radiator` (Radiator, read-only) - Radiator if applicable
- `resource_drain` (ResourceDrain, read-only) - Resource drain if applicable
- `rcs` (RCS, read-only) - RCS if applicable
- `reaction_wheel` (ReactionWheel, read-only) - Reaction wheel if applicable
- `resource_converter` (ResourceConverter, read-only) - Resource converter if applicable
- `resource_harvester` (ResourceHarvester, read-only) - Resource harvester if applicable
- `robotic_controller` (RoboticController, read-only) - Robotic controller if applicable
- `robotic_hinge` (RoboticHinge, read-only) - Robotic hinge if applicable
- `robotic_piston` (RoboticPiston, read-only) - Robotic piston if applicable
- `robotic_rotation` (RoboticRotation, read-only) - Robotic rotation if applicable
- `robotic_rotor` (RoboticRotor, read-only) - Robotic rotor if applicable
- `sensor` (Sensor, read-only) - Sensor if applicable
- `solar_panel` (SolarPanel, read-only) - Solar panel if applicable
- `wheel` (Wheel, read-only) - Wheel if applicable

### Position Methods
- `position(reference_frame)` - Position in given frame
- `center_of_mass(reference_frame)` - Center of mass in given frame
- `bounding_box(reference_frame)` - Bounding box in given frame
- `direction(reference_frame)` - Direction in given frame
- `velocity(reference_frame)` - Velocity in given frame
- `rotation(reference_frame)` - Rotation in given frame

### Force Methods
- `add_force(force, position, reference_frame)` - Add constant force
- `instantaneous_force(force, position, reference_frame)` - Add instantaneous force

### Other Properties
- `glow` (bool, write-only) - Part glow state
- `auto_strut_mode` (AutoStrutMode, read-only) - Auto-strut mode
- `moment_of_inertia` (tuple[float, float, float], read-only) - Moment of inertia
- `inertia_tensor` (list[float], read-only) - Inertia tensor
- `reference_frame` (ReferenceFrame, read-only) - Part reference frame
- `center_of_mass_reference_frame` (ReferenceFrame, read-only) - Center of mass reference frame

## Module Class

The **Module** class represents a specific part module.

### Properties
- `name` (str, read-only) - Module name
- `part` (Part, read-only) - Parent part
- `fields` (dict[str, str], read-only) - Module fields
- `fields_by_id` (dict[str, str], read-only) - Module fields by ID
- `events` (list[str], read-only) - Module events
- `events_by_id` (list[str], read-only) - Module events by ID
- `actions` (list[str], read-only) - Module actions
- `actions_by_id` (list[str], read-only) - Module actions by ID

### Field Methods
- `has_field(name)` - Check if field exists
- `has_field_with_id(id)` - Check if field exists by ID
- `get_field(name)` - Get field value
- `get_field_by_id(id)` - Get field value by ID
- `set_field_int(name, value)` - Set integer field
- `set_field_int_by_id(id, value)` - Set integer field by ID
- `set_field_float(name, value)` - Set float field
- `set_field_float_by_id(id, value)` - Set float field by ID
- `set_field_string(name, value)` - Set string field
- `set_field_string_by_id(id, value)` - Set string field by ID
- `set_field_bool(name, value)` - Set boolean field
- `set_field_bool_by_id(id, value)` - Set boolean field by ID
- `reset_field(name)` - Reset field
- `reset_field_by_id(id)` - Reset field by ID

### Event Methods
- `has_event(name)` - Check if event exists
- `has_event_with_id(id)` - Check if event exists by ID
- `trigger_event(name)` - Trigger event
- `trigger_event_by_id(id)` - Trigger event by ID

### Action Methods
- `has_action(name)` - Check if action exists
- `has_action_with_id(id)` - Check if action exists by ID
- `set_action(name, value=True)` - Set action
- `set_action_by_id(id, value=True)` - Set action by ID

## Enums

### AutoStrutMode
- `off` - Off
- `root` - Root
- `heaviest` - Heaviest
- `grandparent` - Grandparent
- `force_root` - ForceRoot
- `force_heaviest` - ForceHeaviest
- `force_grandparent` - ForceGrandparent 