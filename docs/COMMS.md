# Comms

The **Comms** class provides functionality to interact with CommNet for a given vessel in Kerbal Space Program. It is obtained by calling `Vessel.comms` and allows you to check communication status, signal strength, and control paths.

## Quick usage
```python
import krpc
conn = krpc.connect()
vessel = conn.space_center.active_vessel
comms = vessel.comms
print(f"Can communicate: {comms.can_communicate}")
print(f"Signal strength: {comms.signal_strength:.2f}")
```

## Core Properties

### Communication Status
- `can_communicate` (bool, read-only) - Whether vessel can communicate with KSC
- `can_transmit_science` (bool, read-only) - Whether vessel can transmit science data
- `signal_strength` (float, read-only) - Signal strength to KSC
- `signal_delay` (float, read-only) - Signal delay to KSC in seconds
- `power` (float, read-only) - Combined power of all active antennae

### Control Path
- `control_path` (list[CommLink], read-only) - Communication path used to control vessel

## CommLink Class

The **CommLink** class represents a communication node in the network, such as a vessel or the KSC.

### Properties
- `type` (CommLinkType, read-only) - Type of link
- `signal_strength` (float, read-only) - Signal strength of the link
- `start` (CommNode, read-only) - Start point of the link
- `end` (CommNode, read-only) - End point of the link

## CommNode Class

The **CommNode** class represents a communication node in the network, such as a vessel or the KSC.

### Properties
- `name` (str, read-only) - Name of the communication node
- `is_home` (bool, read-only) - Whether node is on Kerbin
- `is_control_point` (bool, read-only) - Whether node is a control point
- `is_vessel` (bool, read-only) - Whether node is a vessel
- `vessel` (Vessel, read-only) - Vessel for this communication node

## Enums

### CommLinkType
- `home` - Link to base station on Kerbin
- `control` - Link to control source (e.g., manned spacecraft)
- `relay` - Link to relay satellite 