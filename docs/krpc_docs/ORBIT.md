# Orbit

The **Orbit** class describes an orbit in Kerbal Space Program. It can represent the orbit of a vessel (obtained via `Vessel.orbit`) or a celestial body (obtained via `CelestialBody.orbit`).

## Quick usage
```python
import krpc
conn = krpc.connect()
vessel = conn.space_center.active_vessel
orbit = vessel.orbit
print(f"Apoapsis: {orbit.apoapsis_altitude/1000:.1f} km")
print(f"Periapsis: {orbit.periapsis_altitude/1000:.1f} km")
```

## Basic Properties

### Orbital Body
- `body` (CelestialBody, read-only) - The body being orbited

### Apsides
- `apoapsis` (float, read-only) - Apoapsis from body's center of mass (m)
- `periapsis` (float, read-only) - Periapsis from body's center of mass (m)
- `apoapsis_altitude` (float, read-only) - Apoapsis above sea level (m)
- `periapsis_altitude` (float, read-only) - Periapsis above sea level (m)

### Orbital Elements
- `semi_major_axis` (float, read-only) - Semi-major axis (m)
- `semi_minor_axis` (float, read-only) - Semi-minor axis (m)
- `eccentricity` (float, read-only) - Orbital eccentricity
- `inclination` (float, read-only) - Orbital inclination (rad)
- `longitude_of_ascending_node` (float, read-only) - Longitude of ascending node (rad)
- `argument_of_periapsis` (float, read-only) - Argument of periapsis (rad)

## Time and Motion

### Current State
- `radius` (float, read-only) - Current orbital radius (m)
- `speed` (float, read-only) - Current orbital speed (m/s)
- `period` (float, read-only) - Orbital period (s)
- `time_to_apoapsis` (float, read-only) - Time until apoapsis (s)
- `time_to_periapsis` (float, read-only) - Time until periapsis (s)

### Anomalies
- `mean_anomaly` (float, read-only) - Current mean anomaly
- `mean_anomaly_at_epoch` (float, read-only) - Mean anomaly at epoch
- `epoch` (float, read-only) - Time since epoch (s)
- `eccentric_anomaly` (float, read-only) - Current eccentric anomaly
- `true_anomaly` (float, read-only) - Current true anomaly

## Position Methods

### Current Position
- `position_at(ut, reference_frame)` - Position at given time in specified frame
- `radius_at(ut)` - Orbital radius at given time (m)

### Anomaly Calculations
- `mean_anomaly_at_ut(ut)` - Mean anomaly at given time
- `eccentric_anomaly_at_ut(ut)` - Eccentric anomaly at given time
- `true_anomaly_at_ut(ut)` - True anomaly at given time
- `true_anomaly_at_radius(radius)` - True anomaly at given radius
- `ut_at_true_anomaly(true_anomaly)` - Time at given true anomaly
- `radius_at_true_anomaly(true_anomaly)` - Radius at given true anomaly

## Orbital Speed
- `orbital_speed` (float, read-only) - Current orbital speed (m/s)
- `orbital_speed_at(time)` - Orbital speed at given time (m/s)

## Reference Plane
- `reference_plane_normal(reference_frame)` - Normal to reference plane
- `reference_plane_direction(reference_frame)` - Direction of ascending node

## Orbital Interactions

### Node Calculations
- `true_anomaly_at_an(target)` - True anomaly at ascending node with target
- `true_anomaly_at_dn(target)` - True anomaly at descending node with target
- `relative_inclination(target)` - Relative inclination with target orbit (rad)

### Sphere of Influence
- `time_to_soi_change` (float, read-only) - Time until SOI change (s)
- `next_orbit` (Orbit, read-only) - Next orbit after SOI change

### Close Approaches
- `time_of_closest_approach(target)` - Time of closest approach to target
- `distance_at_closest_approach(target)` - Distance at closest approach (m)
- `list_closest_approaches(target, orbits)` - List of future close approaches
