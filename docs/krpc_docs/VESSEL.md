# Vessel

The **Vessel** class provides functionality to interact with vessels in Kerbal Space Program. This includes getting orbital and flight data, manipulating control inputs, and managing resources. Vessel objects are created using `active_vessel` or `vessels` from the SpaceCenter service.

## Quick usage
```python
import krpc
conn = krpc.connect()
vessel = conn.space_center.active_vessel
print(vessel.name)
print(vessel.orbit.body.name)
```

## Core Attributes

### Basic Information
- `name` (str, read/write) - Name of the vessel
- `type` (VesselType, read/write) - Type of the vessel
- `situation` (VesselSituation, read-only) - Current situation of the vessel
- `recoverable` (bool, read-only) - Whether the vessel can be recovered
- `met` (float, read-only) - Mission elapsed time in seconds
- `biome` (str, read-only) - Name of current biome

### Mass and Resources
- `mass` (float, read-only) - Total mass including resources (kg)
- `dry_mass` (float, read-only) - Total mass excluding resources (kg)
- `resources` (Resources, read-only) - Access to vessel's resources
- `resources_in_decouple_stage(stage, cumulative=True)` - Get resources for specific stage

### Crew Management
- `crew_capacity` (int, read-only) - Maximum crew capacity
- `crew_count` (int, read-only) - Current number of crew
- `crew` (list[CrewMember], read-only) - List of crew members

### Control Systems
- `control` (Control, read-only) - Vessel control inputs
- `auto_pilot` (AutoPilot, read-only) - Auto-pilot functionality
- `comms` (Comms, read-only) - Communication systems

### Flight Data
- `flight(reference_frame=None)` - Get flight telemetry
- `orbit` (Orbit, read-only) - Current orbital parameters
- `parts` (Parts, read-only) - Access to vessel's parts

## Propulsion

### Thrust Properties
- `thrust` (float, read-only) - Current thrust (N)
- `available_thrust` (float, read-only) - Available thrust from active engines (N)
- `available_thrust_at(pressure)` - Available thrust at given pressure (N)
- `max_thrust` (float, read-only) - Maximum thrust from active engines (N)
- `max_thrust_at(pressure)` - Maximum thrust at given pressure (N)
- `max_vacuum_thrust` (float, read-only) - Maximum vacuum thrust (N)

### Engine Performance
- `specific_impulse` (float, read-only) - Combined specific impulse (s)
- `specific_impulse_at(pressure)` - Specific impulse at given pressure (s)
- `vacuum_specific_impulse` (float, read-only) - Vacuum specific impulse (s)
- `kerbin_sea_level_specific_impulse` (float, read-only) - Sea level specific impulse on Kerbin (s)

## Dynamics

### Inertia and Torque
- `moment_of_inertia` (tuple[float, float, float], read-only) - Moment of inertia around COM
- `inertia_tensor` (list[float], read-only) - 3x3 inertia tensor
- `available_torque` (tuple[tuple[float, float, float], tuple[float, float, float]], read-only) - Maximum available torque
- `available_reaction_wheel_torque` - Maximum reaction wheel torque
- `available_rcs_torque` - Maximum RCS torque
- `available_rcs_force` - Maximum RCS force
- `available_engine_torque` - Maximum engine gimbal torque
- `available_control_surface_torque` - Maximum control surface torque
- `available_other_torque` - Maximum torque from other sources

## Reference Frames

### Vessel Frames
- `reference_frame` (ReferenceFrame, read-only) - Vessel-fixed reference frame
- `orbital_reference_frame` (ReferenceFrame, read-only) - Orbital reference frame
- `surface_reference_frame` (ReferenceFrame, read-only) - Surface reference frame
- `surface_velocity_reference_frame` (ReferenceFrame, read-only) - Surface velocity reference frame

### Position and Motion
- `position(reference_frame)` - Position vector in given frame
- `velocity(reference_frame)` - Velocity vector in given frame
- `rotation(reference_frame)` - Rotation quaternion in given frame
- `direction(reference_frame)` - Direction vector in given frame
- `angular_velocity(reference_frame)` - Angular velocity vector in given frame
- `bounding_box(reference_frame)` - Axis-aligned bounding box in given frame

## Methods
- `recover()` - Recover the vessel

## Enums

### VesselType
- `base` - Base
- `debris` - Debris
- `lander` - Lander
- `plane` - Plane
- `probe` - Probe
- `relay` - Relay
- `rover` - Rover
- `ship` - Ship
- `station` - Station
- `space_object` - SpaceObject
- `unknown` - Unknown
- `eva` - EVA
- `flag` - Flag
- `deployed_science_controller` - DeployedScienceController
- `deployed_science_part` - DeployedSciencePart
- `dropped_part` - DroppedPart
- `deployed_ground_part` - DeployedGroundPart

### VesselSituation
- `docked` - Docked to another vessel
- `escaping` - Escaping
- `flying` - Flying through atmosphere
- `landed` - Landed on surface
- `orbiting` - Orbiting a body
- `pre_launch` - Awaiting launch
- `splashed` - Splashed down
- `sub_orbital` - Sub-orbital trajectory

## CrewMember Class

### Attributes
- `name` (str, read/write) - Crew member's name
- `type` (CrewMemberType, read-only) - Type of crew member
- `on_mission` (bool, read-only) - Whether on mission
- `courage` (float, read/write) - Courage value
- `stupidity` (float, read/write) - Stupidity value
- `experience` (float, read/write) - Experience value
- `badass` (bool, read/write) - Badass status
- `veteran` (bool, read/write) - Veteran status
- `trait` (str, read-only) - Job/trait
- `gender` (CrewMemberGender, read-only) - Gender
- `roster_status` (RosterStatus, read-only) - Current status
- `suit_type` (SuitType, read/write) - Suit type

### Career Log
- `career_log_flights` (list[int], read-only) - Flight IDs
- `career_log_types` (list[str], read-only) - Log entry types
- `career_log_targets` (list[str], read-only) - Target body names

### Enums

#### CrewMemberType
- `applicant` - Applicant
- `crew` - Rocket crew
- `tourist` - Tourist
- `unowned` - Unowned

#### CrewMemberGender
- `male` - Male
- `female` - Female

#### RosterStatus
- `available` - Available
- `assigned` - Assigned
- `dead` - Dead
- `missing` - Missing

#### SuitType
- `default` - Default suit
- `vintage` - Vintage suit
- `future` - Future suit
- `slim` - Slim suit
