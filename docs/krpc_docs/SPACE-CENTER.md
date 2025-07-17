# SpaceCenter

Source docs: <https://krpc.github.io/krpc/python/api/space-center/space-center.html>

The **SpaceCenter** service is the main gateway to Kerbal Space Program game state. It lets you query global information (science, funds, reputation), switch scenes, access lists of vessels and celestial bodies, and perform high‑level actions such as launching or recovering vessels.

## Quick usage
```python
import krpc
conn = krpc.connect()
sc = conn.space_center
print(sc.active_vessel.name)
```

## Core Attributes

### Game Resources
- `science` (float, read-only) - Current amount of science
- `funds` (float, read-only) - Current amount of funds
- `reputation` (float, read-only) - Current amount of reputation

### Vessel Management
- `active_vessel` (Vessel, read/write) - Currently active vessel
- `vessels` (list[Vessel], read-only) - List of all vessels in the game
- `launch_sites` (list[LaunchSite], read-only) - Available launch sites

### Celestial Bodies
- `bodies` (dict[str, CelestialBody], read-only) - Dictionary of all celestial bodies keyed by name
- `target_body` (CelestialBody, read/write) - Currently targeted celestial body (Flight scene only)

### Targeting
- `target_vessel` (Vessel, read/write) - Currently targeted vessel (Flight scene only)
- `target_docking_port` (DockingPort, read/write) - Currently targeted docking port (Flight scene only)

### Game State
- `ut` (float, read-only) - Universal time in seconds
- `g` (float, read-only) - Gravitational constant G
- `game_mode` (GameMode, read-only) - Current game mode
- `warp_mode` (WarpMode, read-only) - Current time warp mode

### UI Controls
- `ui_visible` (bool, read/write) - Whether the UI is visible (Flight scene only)
- `navball` (bool, read/write) - Whether the navball is visible (Flight scene only)
- `map_filter` (MapFilterType, read/write) - Visible objects in map mode

## Time Warp Controls

### Warp Properties
- `warp_rate` (float, read-only) - Current warp rate (1 if not active)
- `warp_factor` (int, read-only) - Current warp factor index (0 if not active)
- `rails_warp_factor` (int, read/write) - On-rails warp factor (0-7)
- `physics_warp_factor` (int, read/write) - Physical warp factor (0-3)
- `maximum_rails_warp_factor` (int, read-only) - Maximum available rails warp factor

### Warp Methods
- `warp_to(ut, max_rails_rate=100000.0, max_physics_rate=2.0)` - Warp to specified universal time
- `can_rails_warp_at(factor=1)` - Check if rails warp is possible at given factor

## Vessel Operations

### Launch Methods
- `launch_vessel(craft_directory, name, launch_site, recover=True, crew=None, flag_url='')` - Launch a vessel
- `launch_vessel_from_vab(name, recover=True)` - Launch from VAB to launchpad
- `launch_vessel_from_sph(name, recover=True)` - Launch from SPH to runway
- `launchable_vessels(craft_directory)` - Get list of launchable vessels

### Save/Load Operations
- `save(name)` - Save game with given name
- `load(name)` - Load game with given name
- `quicksave()` - Create quicksave
- `quickload()` - Load quicksave
- `can_revert_to_launch()` - Check if flight can be reverted
- `revert_to_launch()` - Revert current flight to launch

## Coordinate Transformations

- `transform_position(position, from, to)` - Convert position between reference frames
- `transform_direction(direction, from, to)` - Convert direction between reference frames
- `transform_rotation(rotation, from, to)` - Convert rotation between reference frames
- `transform_velocity(position, velocity, from, to)` - Convert velocity between reference frames

## Raycasting

- `raycast_distance(position, direction, reference_frame)` - Get distance to hit point
- `raycast_part(position, direction, reference_frame)` - Get hit part (Flight scene only)

## Additional Features

### Crew Management
- `transfer_crew(crew_member, target_part)` - Move crew member to different part
- `create_kerbal(name, job, male)` - Create new Kerbal
- `get_kerbal(name)` - Find Kerbal by name

### Scene Management
- `load_space_center()` - Switch to space center view
- `screenshot(file_path, scale=1)` - Save screenshot (Flight scene only)

### Managers
- `camera` (Camera, read-only) - Camera control
- `waypoint_manager` (WaypointManager, read-only) - Waypoint management
- `contract_manager` (ContractManager, read-only) - Contract management
- `alarm_manager` (AlarmManager, read-only) - Alarm management

## Enums

### GameMode
- `sandbox` - Sandbox mode
- `career` - Career mode
- `science` - Science career mode
- `science_sandbox` - Science sandbox mode
- `mission` - Mission mode
- `mission_builder` - Mission builder mode
- `scenario` - Scenario mode
- `scenario_non_resumable` - Non-resumable scenario mode

### WarpMode
- `rails` - On-rails time warp
- `physics` - Physical time warp
- `none` - No time warp

### MapFilterType
- `all` - Everything
- `none` - Nothing
- `debris` - Debris
- `unknown` - Unknown objects
- `space_objects` - Space objects
- `probes` - Probes
- `rovers` - Rovers
- `landers` - Landers
- `ships` - Ships
- `stations` - Stations
- `bases` - Bases
- `ev_as` - EVAs
- `flags` - Flags
- `plane` - Planes
- `relay` - Relays
- `site` - Launch sites
- `deployed_science_controller` - Deployed science controllers

### EditorFacility
- `vab` - Vehicle Assembly Building
- `sph` - Space Plane Hangar
- `none` - None