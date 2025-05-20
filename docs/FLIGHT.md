# Flight

The **Flight** class provides flight telemetry data for a vessel. It is obtained by calling `Vessel.flight()` and all information is returned in the reference frame passed to that method.

## Quick usage
```python
import krpc
conn = krpc.connect()
vessel = conn.space_center.active_vessel
flight = vessel.flight()
print(flight.mean_altitude)
print(flight.speed)
```

## Altitude and Position

### Altitude Properties
- `mean_altitude` (float, read-only) - Altitude above sea level in meters
- `surface_altitude` (float, read-only) - Altitude above surface/sea level in meters
- `bedrock_altitude` (float, read-only) - Altitude above bedrock in meters
- `elevation` (float, read-only) - Terrain height above sea level in meters

### Position Properties
- `latitude` (float, read-only) - Latitude in degrees
- `longitude` (float, read-only) - Longitude in degrees
- `center_of_mass` (tuple[float, float, float], read-only) - Center of mass position vector

## Motion and Orientation

### Velocity Properties
- `velocity` (tuple[float, float, float], read-only) - Velocity vector in m/s
- `speed` (float, read-only) - Speed in m/s
- `horizontal_speed` (float, read-only) - Horizontal speed in m/s
- `vertical_speed` (float, read-only) - Vertical speed in m/s

### Orientation Properties
- `rotation` (tuple[float, float, float, float], read-only) - Rotation quaternion
- `direction` (tuple[float, float, float], read-only) - Pointing direction unit vector
- `pitch` (float, read-only) - Pitch relative to horizon (-90° to +90°)
- `heading` (float, read-only) - Heading relative to north (0° to 360°)
- `roll` (float, read-only) - Roll relative to horizon (-180° to +180°)

### Orbital Directions
- `prograde` (tuple[float, float, float], read-only) - Prograde direction unit vector
- `retrograde` (tuple[float, float, float], read-only) - Retrograde direction unit vector
- `normal` (tuple[float, float, float], read-only) - Normal direction unit vector
- `anti_normal` (tuple[float, float, float], read-only) - Anti-normal direction unit vector
- `radial` (tuple[float, float, float], read-only) - Radial direction unit vector
- `anti_radial` (tuple[float, float, float], read-only) - Anti-radial direction unit vector

## Aerodynamics

### Pressure and Forces
- `g_force` (float, read-only) - Current G force in g
- `atmosphere_density` (float, read-only) - Atmospheric density in kg/m³
- `dynamic_pressure` (float, read-only) - Dynamic pressure in Pa
- `static_pressure` (float, read-only) - Static pressure in Pa
- `static_pressure_at_msl` (float, read-only) - Static pressure at mean sea level in Pa
- `aerodynamic_force` (tuple[float, float, float], read-only) - Total aerodynamic force vector
- `lift` (tuple[float, float, float], read-only) - Lift force vector
- `drag` (tuple[float, float, float], read-only) - Drag force vector

### Air Properties
- `speed_of_sound` (float, read-only) - Speed of sound in m/s
- `mach` (float, read-only) - Speed in multiples of speed of sound
- `true_air_speed` (float, read-only) - True air speed in m/s
- `equivalent_air_speed` (float, read-only) - Equivalent air speed in m/s
- `terminal_velocity` (float, read-only) - Estimated terminal velocity in m/s

### Flight Dynamics
- `angle_of_attack` (float, read-only) - Pitch angle between orientation and velocity vector
- `sideslip_angle` (float, read-only) - Yaw angle between orientation and velocity vector
- `total_air_temperature` (float, read-only) - Total air temperature in Kelvin
- `static_air_temperature` (float, read-only) - Static air temperature in Kelvin

## Advanced Aerodynamics (Requires Ferram Aerospace Research)

### Stall and Coefficients
- `stall_fraction` (float, read-only) - Current amount of stall (0 to 1)
- `drag_coefficient` (float, read-only) - Coefficient of drag
- `lift_coefficient` (float, read-only) - Coefficient of lift
- `ballistic_coefficient` (float, read-only) - Ballistic coefficient
- `thrust_specific_fuel_consumption` (float, read-only) - TSFC for jet engines (N/h/N)

## Methods

### Aerodynamic Simulation
- `simulate_aerodynamic_force_at(body, position, velocity)` - Simulate aerodynamic forces at given position and velocity
