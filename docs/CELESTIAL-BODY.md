# CelestialBody

The **CelestialBody** class represents a celestial body (such as a planet or moon) in Kerbal Space Program. These objects can be accessed through the `bodies` dictionary in the SpaceCenter service.

## Quick usage
```python
import krpc
conn = krpc.connect()
kerbin = conn.space_center.bodies['Kerbin']
print(kerbin.name)
print(kerbin.mass)
```

## Core Attributes

### Basic Information
- `name` (str, read-only) - Name of the body
- `satellites` (list[CelestialBody], read-only) - List of bodies orbiting this body
- `orbit` (Orbit, read-only) - Orbital parameters
- `mass` (float, read-only) - Mass in kilograms
- `gravitational_parameter` (float, read-only) - Standard gravitational parameter (m³/s²)
- `surface_gravity` (float, read-only) - Surface gravity at sea level (m/s²)

### Physical Properties
- `rotational_period` (float, read-only) - Sidereal rotational period in seconds
- `rotational_speed` (float, read-only) - Rotational speed in radians/second
- `rotation_angle` (float, read-only) - Current rotation angle in radians
- `initial_rotation` (float, read-only) - Initial rotation angle at UT 0
- `equatorial_radius` (float, read-only) - Equatorial radius in meters
- `sphere_of_influence` (float, read-only) - Sphere of influence radius in meters

### Surface Properties
- `has_solid_surface` (bool, read-only) - Whether body has solid surface
- `is_star` (bool, read-only) - Whether body is a star
- `biomes` (set[str], read-only) - Set of biomes present on body
- `flying_high_altitude_threshold` (float, read-only) - Altitude for "high" flying science
- `space_high_altitude_threshold` (float, read-only) - Altitude for "high" space science

### Atmosphere Properties
- `has_atmosphere` (bool, read-only) - Whether body has atmosphere
- `atmosphere_depth` (float, read-only) - Depth of atmosphere in meters
- `has_atmospheric_oxygen` (bool, read-only) - Whether atmosphere contains oxygen

## Position and Height Methods

### Surface Height
- `surface_height(latitude, longitude)` - Height relative to mean sea level in meters
- `bedrock_height(latitude, longitude)` - Height of bedrock relative to mean sea level

### Position Methods
- `msl_position(latitude, longitude, reference_frame)` - Position at mean sea level
- `surface_position(latitude, longitude, reference_frame)` - Position at surface
- `bedrock_position(latitude, longitude, reference_frame)` - Position at bedrock
- `position_at_altitude(latitude, longitude, altitude, reference_frame)` - Position at altitude

### Position Queries
- `altitude_at_position(position, reference_frame)` - Altitude at given position
- `latitude_at_position(position, reference_frame)` - Latitude at given position
- `longitude_at_position(position, reference_frame)` - Longitude at given position
- `biome_at(latitude, longitude)` - Biome at given coordinates

## Atmosphere Methods

### Atmospheric Properties
- `atmospheric_density_at_position(position, reference_frame)` - Density at position (kg/m³)
- `temperature_at(position, reference_frame)` - Temperature at position
- `density_at(altitude)` - Air density at altitude (kg/m³)
- `pressure_at(altitude)` - Air pressure at altitude (Pa)

## Reference Frames

### Body Frames
- `reference_frame` (ReferenceFrame, read-only) - Body-fixed reference frame
- `non_rotating_reference_frame` (ReferenceFrame, read-only) - Non-rotating body frame
- `orbital_reference_frame` (ReferenceFrame, read-only) - Orbital reference frame

### Motion Methods
- `position(reference_frame)` - Position vector in given frame
- `velocity(reference_frame)` - Velocity vector in given frame
- `rotation(reference_frame)` - Rotation quaternion in given frame
- `direction(reference_frame)` - North pole direction vector
- `angular_velocity(reference_frame)` - Angular velocity vector

## Reference Frame Details

### Body-Fixed Frame
- Origin: Center of body
- Axes: Rotate with body
- X-axis: Points to 0° longitude, 0° latitude
- Y-axis: Points to north pole
- Z-axis: Points to 90°E longitude

### Non-Rotating Frame
- Origin: Center of body
- Axes: Fixed in space
- X-axis: Arbitrary direction through equator
- Y-axis: Points to north pole
- Z-axis: Arbitrary direction through equator

### Orbital Frame
- Origin: Center of body
- Axes: Rotate with orbital motion
- X-axis: Points in anti-radial direction
- Y-axis: Points in prograde direction
- Z-axis: Points in normal direction
