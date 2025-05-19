# KOS Resources Documentation

This document provides references and examples for the kRPC API endpoints used in the KOS (Kerbal Orbital System) project.

## Core API References

### Vessel Control
[Vessel API Documentation](https://krpc.github.io/krpc/python/api/space-center/vessel.html)

Key features used:
- `vessel.control` - Control vessel systems (throttle, SAS, RCS, etc.)
- `vessel.auto_pilot` - Control vessel orientation and navigation
- `vessel.available_thrust` - Get current available thrust
- `vessel.specific_impulse` - Get engine ISP
- `vessel.mass` - Get current vessel mass

Example:
```python
# Control vessel systems
vessel.control.throttle = 1.0
vessel.control.sas = True
vessel.control.rcs = True

# Set up autopilot
vessel.auto_pilot.engage()
vessel.auto_pilot.target_pitch_and_heading(90, 90)
```

### Orbital Mechanics
[Orbit API Documentation](https://krpc.github.io/krpc/python/api/space-center/orbit.html)

Key features used:
- `vessel.orbit.apoapsis` - Get apoapsis altitude
- `vessel.orbit.periapsis` - Get periapsis altitude
- `vessel.orbit.semi_major_axis` - Get orbital semi-major axis
- `vessel.orbit.time_to_apoapsis` - Get time until apoapsis
- `vessel.orbit.body.gravitational_parameter` - Get body's gravitational parameter

Example:
```python
# Calculate orbital parameters
mu = vessel.orbit.body.gravitational_parameter
r = vessel.orbit.apoapsis
a = vessel.orbit.semi_major_axis

# Calculate orbital velocity using vis-viva equation
v = math.sqrt(mu * ((2.0 / r) - (1.0 / a)))
```

### Flight Data
[Flight API Documentation](https://krpc.github.io/krpc/python/api/space-center/flight.html)

Key features used:
- `vessel.flight().mean_altitude` - Get current altitude
- `vessel.flight().velocity` - Get current velocity vector
- `vessel.flight().pitch` - Get current pitch angle
- `vessel.flight().heading` - Get current heading angle

Example:
```python
# Monitor flight parameters
altitude = vessel.flight().mean_altitude
velocity = vessel.flight().velocity
pitch = vessel.flight().pitch
heading = vessel.flight().heading
```

### Resource Management
[Resources API Documentation](https://krpc.github.io/krpc/python/api/space-center/resources.html)

Key features used:
- `vessel.resources.amount()` - Get resource amount
- `vessel.resources.max()` - Get maximum resource capacity
- `vessel.resources_in_decouple_stage()` - Get resources in specific stage

Example:
```python
# Check fuel levels
fuel = vessel.resources.amount("LiquidFuel")
oxidizer = vessel.resources.amount("Oxidizer")
electric_charge = vessel.resources.amount("ElectricCharge")

# Get stage resources
stage_resources = vessel.resources_in_decouple_stage(stage=2, cumulative=False)
srb_fuel = stage_resources.amount("SolidFuel")
```

## Common Calculations

### Delta-V Calculation
```python
def calculate_delta_v(vessel):
    isp = vessel.specific_impulse * 9.82
    m0 = vessel.mass
    m1 = m0 - vessel.resources.amount("LiquidFuel") - vessel.resources.amount("Oxidizer")
    return isp * math.log(m0 / m1)
```

### Orbital Period
```python
def calculate_orbital_period(vessel):
    mu = vessel.orbit.body.gravitational_parameter
    a = vessel.orbit.semi_major_axis
    return 2 * math.pi * math.sqrt((a ** 3) / mu)
```

### Circularization Burn
```python
def calculate_circularization_burn(vessel):
    mu = vessel.orbit.body.gravitational_parameter
    r = vessel.orbit.apoapsis
    a1 = vessel.orbit.semi_major_axis
    a2 = r
    v1 = math.sqrt(mu * ((2.0 / r) - (1.0 / a1)))
    v2 = math.sqrt(mu * ((2.0 / r) - (1.0 / a2)))
    return v2 - v1
```

## Best Practices

1. **Stream Usage**
   - Use streams for frequently accessed values to improve performance
   - Example:
   ```python
   altitude = conn.add_stream(getattr, vessel.flight(), "mean_altitude")
   apoapsis = conn.add_stream(getattr, vessel.orbit, "apoapsis_altitude")
   ```

2. **Error Handling**
   - Always wrap kRPC calls in try-except blocks
   - Handle connection errors gracefully
   ```python
   try:
       conn = krpc.connect(name='KOS')
   except Exception as e:
       logger.error(f"Failed to connect to KSP: {e}")
       raise
   ```

3. **Resource Management**
   - Monitor resource levels continuously
   - Implement safety checks for critical resources
   ```python
   def check_resources(vessel):
       fuel = vessel.resources.amount("LiquidFuel")
       if fuel < 0.1:
           return False
       return True
   ```

4. **Performance Optimization**
   - Use streams for frequently accessed values
   - Batch operations when possible
   - Minimize the number of RPC calls

## Additional Resources

- [kRPC Python Client Documentation](https://krpc.github.io/krpc/python/)
- [Kerbal Space Program Forums](https://forum.kerbalspaceprogram.com/)
- [kRPC GitHub Repository](https://github.com/krpc/krpc)

