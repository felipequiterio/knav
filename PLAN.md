# KNAV Flight Software & Mission Control Center - Complete Specification

## Context

KNAV is an external flight software and Mission Control Center for Kerbal Space Program (KSP), built on the KRPC mod. It is a professional-grade autopilot system that uses the Guidance-Navigation-Control (GNC) pattern, state machines, and a web-based Mission Control Center UI with REST + WebSocket.

**What is KSP?** Kerbal Space Program is a space flight simulation game where players build and fly rockets. It has realistic orbital mechanics (patched conics approximation), atmospheric flight, and a full solar system (Kerbol system) with planets, moons, and different gravitational fields.

**What is KRPC?** KRPC is a mod for KSP that runs a server (KRPC.dll) inside the game, exposing a Remote Procedure Call API. External programs connect via TCP (Protocol Buffers) to read telemetry, control vessels, manage maneuver nodes, warp time, and interact with all game systems. It supports real-time data streaming for efficient telemetry.

- KRPC server runs inside KSP on configurable ports (default: RPC port 50000, Stream port 50001)
- Python client library: `krpc` (pip installable)
- Connection: `conn = krpc.connect(name="KNAV", address=KRPC_ADDRESS, rpc_port=50000, stream_port=50001)`
- Key services: `conn.space_center` (main gateway), `conn.space_center.active_vessel` (current vessel)
- Scenes: Flight (full control), Space Center (management), VAB/SPH (editors), Tracking Station
- Streaming: `conn.add_stream(vessel.flight().mean_altitude)` for continuous push data

**KRPC API Overview:**

| Service | Access | Key Properties/Methods |
|---|---|---|
| SpaceCenter | `conn.space_center` | `active_vessel`, `vessels`, `bodies`, `ut`, `warp_to()`, `launch_vessel()`, `target_body/vessel` |
| Vessel | `vessel = conn.space_center.active_vessel` | `name`, `type`, `situation`, `mass`, `dry_mass`, `available_thrust`, `max_thrust`, `specific_impulse`, `met`, `orbit`, `flight()`, `control`, `auto_pilot`, `parts`, `resources`, `comms` |
| Orbit | `vessel.orbit` | `apoapsis/periapsis` (+ `_altitude`), `eccentricity`, `inclination`, `semi_major_axis`, `period`, `time_to_apoapsis/periapsis`, `radius`, `speed`, `true/mean/eccentric_anomaly`, `longitude_of_ascending_node`, `argument_of_periapsis`, `epoch`, `body`, `next_orbit`, `time_to_soi_change`, `position_at(ut, frame)`, `radius_at(ut)` |
| Flight | `vessel.flight(ref_frame)` | `mean_altitude`, `surface_altitude`, `latitude`, `longitude`, `speed`, `horizontal_speed`, `vertical_speed`, `pitch`, `heading`, `roll`, `dynamic_pressure`, `static_pressure`, `mach`, `g_force`, `drag`, `lift` |
| Control | `vessel.control` | `throttle` (0-1), `pitch/yaw/roll` (-1 to 1), `sas` (bool), `sas_mode`, `rcs` (bool), `gear`, `brakes`, `lights`, `parachutes`, `solar_panels`, `antennas`, `current_stage`, `activate_next_stage()`, `nodes` (list), `add_node(ut, prograde, normal, radial)`, `remove_nodes()` |
| AutoPilot | `vessel.auto_pilot` | `engage()`, `disengage()`, `target_pitch_and_heading(p, h)`, `target_roll`, `target_direction`, `error` |
| Node | `vessel.control.nodes[0]` | `prograde/normal/radial` (r/w delta-v components), `delta_v`, `remaining_delta_v`, `ut`, `time_to`, `orbit` (resulting), `burn_vector(frame)`, `remaining_burn_vector(frame)`, `remove()`, `reference_frame` |
| CelestialBody | `conn.space_center.bodies["Kerbin"]` | `name`, `mass`, `gravitational_parameter` (mu), `equatorial_radius`, `surface_gravity`, `sphere_of_influence`, `has_atmosphere`, `atmosphere_depth`, `rotational_period`, `satellites`, `orbit`, `reference_frame`, `non_rotating_reference_frame`, `surface_height(lat, lon)`, `biomes` |
| Parts | `vessel.parts` | `all`, `engines`, `solar_panels`, `antennas`, `fairings`, `experiments`, `in_stage(n)`, `with_module(name)` |
| Resources | `vessel.resources` | `amount(name)`, `max(name)`, `density(name)`, `names`, `has_resource(name)` |
| Comms | `vessel.comms` | `can_communicate`, `can_transmit_science`, `signal_strength`, `signal_delay`, `power`, `control_path` |

**SAS Modes:** `stability_assist`, `maneuver`, `prograde`, `retrograde`, `normal`, `anti_normal`, `radial`, `anti_radial`, `target`, `anti_target`

**Vessel Situations:** `pre_launch`, `flying`, `sub_orbital`, `orbiting`, `escaping`, `landed`, `splashed`, `docked`

**Reference Frames:** Each vessel and celestial body provides multiple frames:
- `vessel.reference_frame` (vessel-fixed)
- `vessel.orbital_reference_frame` (orbit-aligned)
- `vessel.surface_reference_frame` (surface-aligned)
- `body.reference_frame` (body-fixed, rotates with body)
- `body.non_rotating_reference_frame` (inertial, fixed to stars)

**Streaming:** For real-time telemetry, create streams instead of polling:
```python
altitude = conn.add_stream(getattr, vessel.flight(), "mean_altitude")
speed = conn.add_stream(getattr, vessel.orbit, "speed")
# Read latest values with: altitude(), speed()
# Remove with: altitude.remove()
```

**Target:** A clean, modular flight software system with GNC loop, state machines, pure orbital mechanics library, KRPC abstraction layer, FastAPI backend, and a Mission Control Center web frontend (React + shadcn/ui).

---

## 1. Project Structure

```
knav/
├── pyproject.toml
├── .env.example
│
├── knav/                                  # Main Python package
│   ├── __init__.py
│   ├── config.py                          # Pydantic Settings: KRPC host/ports, GNC rates
│   │
│   ├── fsw/                               # Flight Software
│   │   ├── __init__.py
│   │   ├── executive.py                   # Main FSW loop: tick GNC, check state machines
│   │   ├── gnc/
│   │   │   ├── __init__.py
│   │   │   ├── navigation.py              # State estimation ("Where are we?")
│   │   │   ├── guidance.py                # Trajectory commands ("Where should we go?")
│   │   │   └── control.py                 # Actuator commands ("How do we get there?")
│   │   ├── state_machines/
│   │   │   ├── __init__.py
│   │   │   ├── vehicle_sm.py              # Vehicle state machine
│   │   │   ├── mission_sm.py              # Mission phase state machine
│   │   │   └── maneuver_sm.py             # Per-maneuver state machines
│   │   ├── maneuvers/
│   │   │   ├── __init__.py
│   │   │   ├── base.py                    # Abstract Maneuver base class
│   │   │   ├── gravity_turn.py            # Gravity turn (port from core/launch/gt.py)
│   │   │   ├── circularization.py         # Circularization
│   │   │   ├── hohmann_transfer.py        # Hohmann transfer (port from core/orbital/hohmann_transfer.py)
│   │   │   ├── bielliptic_transfer.py     # Bi-elliptic transfer
│   │   │   ├── plane_change.py            # Inclination change
│   │   │   ├── rendezvous.py              # Rendezvous (phasing + approach)
│   │   │   ├── docking.py                 # Docking approach
│   │   │   ├── deorbit.py                 # Deorbit burn
│   │   │   ├── landing.py                 # Powered/unpowered landing
│   │   │   └── node_executor.py           # Generic maneuver node executor (port from helpers.py:execute_node)
│   │   └── systems/
│   │       ├── __init__.py
│   │       ├── staging.py                 # Staging logic
│   │       ├── parts.py                   # Part control (fairings, panels, antennas)
│   │       ├── resources.py               # Resource monitoring
│   │       ├── comms.py                   # Communications monitoring
│   │       └── science.py                 # Science experiment management
│   │
│   ├── astro/                             # Pure orbital mechanics (NO KRPC dependency)
│   │   ├── __init__.py
│   │   ├── kepler.py                      # Keplerian orbit math
│   │   ├── maneuver_math.py               # Delta-v calculations
│   │   ├── lambert.py                     # Lambert solver
│   │   ├── propagator.py                  # Orbit propagation
│   │   ├── frames.py                      # Reference frame transforms (stub — future use for interplanetary)
│   │   └── constants.py                   # KSP body constants (mu, R, SOI, atm)
│   │
│   ├── krpc_interface/                    # KRPC abstraction layer
│   │   ├── __init__.py
│   │   ├── connection.py                  # Singleton connection manager
│   │   ├── streams.py                     # Stream lifecycle manager
│   │   ├── scene.py                       # Scene detection and capability gating
│   │   ├── vessel_proxy.py                # Typed vessel facade
│   │   └── errors.py                      # KRPC error types and recovery
│   │
│   ├── models/                            # Pydantic data models (shared by FSW + API)
│   │   ├── __init__.py
│   │   ├── vessel.py                      # VesselState, VesselSystems
│   │   ├── orbit.py                       # OrbitState, OrbitalElements
│   │   ├── maneuver.py                    # ManeuverPlan, ManeuverStatus, ManeuverResult
│   │   ├── mission.py                     # Mission, MissionPhase, MissionTemplate
│   │   ├── telemetry.py                   # TelemetryFrame, TelemetryChannel
│   │   └── enums.py                       # All enum types
│   │
│   ├── events/                            # Event bus / message system
│   │   ├── __init__.py
│   │   ├── bus.py                         # In-process async pub/sub event bus
│   │   └── events.py                      # Event type definitions
│   │
│   ├── api/                               # FastAPI backend
│   │   ├── __init__.py
│   │   ├── app.py                         # FastAPI application factory
│   │   ├── dependencies.py                # Dependency injection (FSW ref, event bus)
│   │   ├── routers/
│   │   │   ├── __init__.py
│   │   │   ├── vessel.py                  # GET /api/vessel, /api/vessel/systems
│   │   │   ├── orbit.py                   # GET /api/orbit
│   │   │   ├── maneuver.py                # POST /api/maneuver/*
│   │   │   ├── mission.py                 # POST /api/mission, mission CRUD
│   │   │   ├── scene.py                   # GET /api/scene
│   │   │   └── command.py                 # POST /api/command/* (throttle, SAS, staging)
│   │   └── websocket/
│   │       ├── __init__.py
│   │       ├── manager.py                 # WebSocket connection manager
│   │       ├── telemetry_ws.py            # /ws/telemetry (10 Hz)
│   │       ├── events_ws.py               # /ws/events (state changes, maneuver status)
│   │       └── logs_ws.py                 # /ws/logs (structured log entries)
│   │
│   └── frontend/                          # Static frontend (served by FastAPI)
│       ├── index.html
│       ├── src/
│       │   ├── main.ts
│       │   ├── stores/                    # State management
│       │   ├── components/                # UI components
│       │   ├── views/                     # Page views (Flight, Orbit Map, Maneuvers, etc.)
│       │   └── lib/                       # WebSocket client, utilities
│       ├── package.json
│       └── vite.config.ts
│
├── tests/
│   ├── conftest.py                        # Mock KRPC fixtures
│   ├── test_astro/                        # Pure math tests (no KRPC)
│   ├── test_fsw/                          # FSW unit tests (mocked KRPC)
│   ├── test_api/                          # API endpoint tests
│   └── test_integration/                  # End-to-end with real KSP (manual)
│
└── docs/
    ├── krpc_docs/                          # Existing KRPC docs (kept)
    └── *.pdf                               # Orbital mechanics textbooks (kept)
```

### Dependencies

```toml
[project]
name = "knav"
version = "1.0.0"
requires-python = ">=3.12"
dependencies = [
    "krpc>=0.5.0",
    "fastapi>=0.115.0",
    "uvicorn[standard]>=0.32.0",
    "websockets>=14.0",
    "pydantic>=2.10.0",
    "pydantic-settings>=2.6.0",
    "python-dotenv>=1.0.0",
    "numpy>=2.0.0",
    "structlog>=24.4.0",
]

[project.optional-dependencies]
dev = ["pytest>=8.0", "pytest-asyncio>=0.24", "httpx>=0.28", "ruff>=0.8.0"]
```

---

## 2. Flight Software Architecture (GNC)

### 2.1 Navigation - "Where are we?"

`knav/fsw/gnc/navigation.py`

Reads raw KRPC telemetry streams and assembles a coherent `VesselState` snapshot every tick.

**Stream set (established once, read each tick):**

| Category | Stream | KRPC Source |
|---|---|---|
| Position | altitude_mean | `vessel.flight().mean_altitude` |
| Position | altitude_surface | `vessel.flight().surface_altitude` |
| Position | latitude, longitude | `vessel.flight().latitude/longitude` |
| Orbit | apoapsis/periapsis altitude | `vessel.orbit.apoapsis_altitude/periapsis_altitude` |
| Orbit | eccentricity, inclination | `vessel.orbit.eccentricity/inclination` |
| Orbit | semi_major_axis, period | `vessel.orbit.semi_major_axis/period` |
| Orbit | time_to_apoapsis/periapsis | `vessel.orbit.time_to_apoapsis/periapsis` |
| Orbit | radius, speed | `vessel.orbit.radius/speed` |
| Orbit | true_anomaly, mean_anomaly | `vessel.orbit.true_anomaly/mean_anomaly` |
| Orbit | LAN, argument_of_periapsis | `vessel.orbit.longitude_of_ascending_node/argument_of_periapsis` |
| Velocity | speed_orbital, speed_surface | `vessel.flight(nrf).speed` / `vessel.flight().speed` |
| Velocity | vertical_speed, horizontal_speed | `vessel.flight(nrf).vertical_speed/horizontal_speed` |
| Attitude | pitch, heading, roll | `vessel.flight().pitch/heading/roll` |
| Aero | dynamic_pressure, mach, g_force | `vessel.flight().*` |
| Mass | total_mass, dry_mass | `vessel.mass/dry_mass` |
| Propulsion | available_thrust, max_thrust, ISP | `vessel.available_thrust/max_thrust/specific_impulse` |
| State | situation, MET | `vessel.situation/met` |
| Time | ut | `conn.space_center.ut` |

**Derived computations (each tick):**

```
twr = available_thrust / (total_mass * local_gravity)
local_gravity = body_mu / orbital_radius^2
acceleration = available_thrust / total_mass
flight_path_angle = atan2(vertical_speed, horizontal_speed)
delta_v_remaining = Isp * g0 * ln(total_mass / dry_mass)
```

**Output:** A frozen `VesselState` published to event bus, consumed by Guidance and Control.

### 2.2 Guidance - "Where should we go?"

`knav/fsw/gnc/guidance.py`

Consumes `VesselState` from Navigation and the active `Maneuver`, produces `GuidanceCommand`.

**GuidanceCommand fields:**
- `target_pitch: float` (degrees)
- `target_heading: float` (degrees)
- `target_roll: float | None`
- `throttle_command: float` (0.0 - 1.0)
- `sas_mode: str | None`
- `use_autopilot: bool`
- `warp_to_ut: float | None`
- `staging_request: bool`
- `terminate: bool`

**Maneuver interface** (every maneuver implements):

```python
class Maneuver(ABC):
    @abstractmethod
    def plan(self, vessel_state: VesselState, ut: float) -> ManeuverPlan:
        """One-time planning: compute delta-v, create nodes."""

    @abstractmethod
    def compute_guidance(self, vessel_state: VesselState, ut: float) -> GuidanceCommand:
        """Called each GNC tick. Returns guidance for this instant."""

    @abstractmethod
    def is_complete(self, vessel_state: VesselState, ut: float) -> bool:
        """True when maneuver has achieved its goals."""

    @abstractmethod
    def abort(self) -> GuidanceCommand:
        """Emergency: zero throttle, stability assist."""
```

If no active maneuver, Guidance produces a "hold" command (stability assist, throttle zero).

### 2.3 Control - "How do we get there?"

`knav/fsw/gnc/control.py`

Translates `GuidanceCommand` into KRPC API calls.

| GuidanceCommand Field | KRPC Action |
|---|---|
| target_pitch + target_heading | `vessel.auto_pilot.target_pitch_and_heading(p, h)` |
| target_roll | `vessel.auto_pilot.target_roll = roll` |
| throttle_command | `vessel.control.throttle = t` (rate-limited) |
| sas_mode | `vessel.control.sas_mode = SASMode.<mode>` |
| use_autopilot=True | `vessel.auto_pilot.engage()` |
| use_autopilot=False | `vessel.auto_pilot.disengage(); vessel.control.sas = True` |
| staging_request=True | `vessel.control.activate_next_stage()` with debounce |
| warp_to_ut | `conn.space_center.warp_to(ut)` |
| terminate=True | Throttle 0, disengage autopilot, emit maneuver-complete |

### 2.4 GNC Loop Execution Model

```
┌─────────────────────────────────────────────────────────┐
│                  FSW Executive Loop                      │
│                                                         │
│  Target rate: 20 Hz (50 ms per tick)                    │
│  Runs as: background thread or asyncio task             │
│                                                         │
│  Each tick:                                             │
│    1. Navigation.update()     ~5 ms  (read streams)     │
│    2. StateMachines.tick()    ~1 ms  (check transitions)│
│    3. Guidance.update()       ~2 ms  (compute commands) │
│    4. Control.update()        ~5 ms  (write to KRPC)    │
│    5. Telemetry.broadcast()   ~1 ms  (push to bus)      │
│    6. Sleep remainder of 50 ms                          │
└─────────────────────────────────────────────────────────┘
```

**Data flow:**

```
KRPC Server (KSP)
    │ streams (~continuous)
    ▼
┌────────────┐  VesselState   ┌────────────┐
│ NAVIGATION │ ──────────────>│  GUIDANCE   │
│            │                │            │
│ Read       │  GuidanceCmd   │ Active     │
│ streams,   │ <────────────  │ maneuver   │
│ build      │                │ compute    │
│ state      │                │ guidance() │
└────────────┘                └─────┬──────┘
                                    │ GuidanceCommand
                                    ▼
                              ┌────────────┐
                              │  CONTROL   │
                              │            │
                              │ AP/SAS mgmt│
                              │ Throttle   │
                              │ Staging    │
                              │ Warp       │
                              └─────┬──────┘
                                    │ KRPC RPC calls
                                    ▼
                              KRPC Server (KSP)
```

### 2.5 Concurrency Model

The system has two execution contexts that must coordinate safely:

**GNC Thread** (the executive loop, 20 Hz):
- Owns all KRPC calls, state machines, and vessel control
- Runs synchronously — one tick must complete before the next starts

**API Thread** (FastAPI / asyncio event loop):
- Handles REST requests, WebSocket broadcast, serves frontend
- Must never call KRPC directly or mutate FSW state

**Coordination mechanisms:**

1. **Command Queue** — `queue.Queue` (thread-safe). API handlers enqueue command objects (e.g., `StartManeuver`, `SetThrottle`). The GNC loop drains the queue at the **start** of each tick before Navigation runs. This guarantees commands are applied at a consistent point in the loop.

2. **VesselState Snapshot** — Navigation builds a new frozen `VesselState` dataclass each tick from KRPC streams. It publishes the snapshot via atomic reference swap (`self._current_state = new_state`). API readers always see a consistent, complete frame — never a half-updated struct.

3. **Event Bus** — Dual-queue design:
   - `asyncio.Queue` for async consumers (WebSocket broadcaster). The GNC thread calls `loop.call_soon_threadsafe(queue.put_nowait, event)` to cross the thread boundary.
   - `queue.Queue` for any sync consumers (e.g., logging sinks).
   - Events: `telemetry_frame`, `state_change`, `maneuver_status`, `log_entry`, `alert`.

```
┌─────────────────────────────────────────────────────────┐
│  API Thread (asyncio)                                   │
│                                                         │
│  REST handler ──▶ command_queue.put(cmd)                │
│  WS broadcaster ◀── asyncio_event_queue.get()           │
│  GET /vessel    ◀── read current_state (atomic ref)     │
└────────────────────────────┬────────────────────────────┘
                             │ thread boundary
┌────────────────────────────┴────────────────────────────┐
│  GNC Thread (synchronous loop)                          │
│                                                         │
│  tick_start:  drain command_queue                        │
│  Navigation:  read KRPC streams → build VesselState     │
│               swap atomic ref → publish telemetry_frame │
│  Guidance:    read VesselState, compute commands         │
│  Control:     apply commands via KRPC                    │
└─────────────────────────────────────────────────────────┘
```

---

## 3. State Machine Design

### 3.1 Vehicle State Machine

Tracks the physical state of the vehicle. Transitions driven by Navigation telemetry.

```
States:
  IDLE             - No active mission, vessel on pad or in stable orbit
  PRE_LAUNCH       - Countdown: engines igniting, clamps present
  POWERED_ASCENT   - Under thrust, climbing through atmosphere
  COAST_ASCENT     - MECO to apoapsis, no thrust, sub-orbital
  ORBIT            - Stable orbit (periapsis above atmosphere)
  MANEUVERING      - Executing a maneuver (burn in progress)
  COAST_TRANSFER   - On transfer orbit between burns
  DESCENT          - Returning to surface (sub-orbital, descending)
  POWERED_DESCENT  - Retro-burn for landing
  LANDED           - On surface, engines off
  ABORT            - Emergency: zero throttle, stability assist

Transitions:
  IDLE -> PRE_LAUNCH:
      Guard: Mission.start() AND vessel.situation == pre_launch

  PRE_LAUNCH -> POWERED_ASCENT:
      Guard: throttle > 0 AND thrust > 0 AND altitude > 0
      Action: record liftoff time

  POWERED_ASCENT -> COAST_ASCENT:
      Guard: throttle == 0 AND situation == sub_orbital AND vertical_speed > 0
      Action: log MECO

  COAST_ASCENT -> ORBIT:
      Guard: periapsis_altitude > atmosphere_depth AND eccentricity < 1.0

  ORBIT -> MANEUVERING:
      Guard: active maneuver AND throttle > 0

  MANEUVERING -> ORBIT:
      Guard: maneuver complete AND periapsis > atmosphere_depth

  MANEUVERING -> COAST_TRANSFER:
      Guard: maneuver complete AND on transfer orbit

  COAST_TRANSFER -> MANEUVERING:
      Guard: next burn of transfer sequence begins

  ORBIT -> DESCENT:
      Guard: periapsis_altitude < atmosphere_depth

  DESCENT -> POWERED_DESCENT:
      Guard: throttle > 0 AND vertical_speed < 0

  POWERED_DESCENT -> LANDED:
      Guard: situation == landed

  LANDED -> PRE_LAUNCH:
      Guard: Mission.start() AND vessel.situation == pre_launch
      Note: surface relaunch scenario (e.g., Mun surface -> return)

  MANEUVERING -> COAST_TRANSFER:
      Guard: maneuver complete AND periapsis < target orbit altitude
      Clarification: only when the completed burn leaves the vessel on a
      transfer orbit (e.g., first Hohmann burn). If the burn achieves a
      stable orbit, transition to ORBIT instead.

  ANY -> ABORT:
      Guard: abort command OR critical failure
      Action: throttle = 0, SAS stability, disengage autopilot

  ANY -> IDLE:
      Guard: quickload/revert detected (scene change to non-flight then back,
             or vessel.met resets)
      Action: reset all state machines, teardown streams, re-initialize
      Note: KSP quickload/revert replaces the game state entirely.
             Detect via UT jumping backward or vessel reference invalidation.

Note: KRPC has no "escaping" situation. If eccentricity >= 1.0 AND specific
orbital energy > 0, the vessel is on an escape trajectory. The SM does not
have a dedicated ESCAPING state — this is handled by Guidance decisions
(e.g., "do not attempt circularization, alert user").
```

### 3.2 Mission State Machine

```
States: PLANNING, ACTIVE, PAUSED, COMPLETED, FAILED, ABORTED

Within ACTIVE:
  phases: List[MissionPhase]
  current_phase_index: int

Transitions:
  PLANNING -> ACTIVE: user sends "start mission"
  ACTIVE -> ACTIVE (next phase): current phase maneuver complete
  ACTIVE -> COMPLETED: last phase complete
  ACTIVE -> PAUSED: user sends "pause"
  PAUSED -> ACTIVE: user sends "resume"
  ACTIVE -> FAILED: unrecoverable error
  ACTIVE -> ABORTED: user/system abort
```

**Example mission (Launch to Mun):**

```python
Mission(
    name="Mun Expedition",
    phases=[
        MissionPhase(name="Launch", maneuver=GravityTurn(target_alt=80_000, heading=90)),
        MissionPhase(name="Circularize", maneuver=Circularization()),
        MissionPhase(name="Transfer to Mun", maneuver=HohmannTransfer(target_body="Mun")),
        MissionPhase(name="Execute Transfer", maneuver=NodeExecutor()),
        MissionPhase(name="Coast to SOI", maneuver=CoastWait(until="soi_change")),
        MissionPhase(name="Capture Burn", maneuver=Circularization()),
        MissionPhase(name="Deorbit", maneuver=Deorbit(target_periapsis=10_000)),
        MissionPhase(name="Landing", maneuver=PoweredLanding()),
    ]
)
```

### 3.3 Per-Maneuver State Machines

**Gravity Turn:**
```
INIT -> IGNITION -> VERTICAL_CLIMB -> PITCH_OVER -> GRAVITY_TURN -> THROTTLE_DOWN -> MECO -> COMPLETE

  INIT: Validate vessel on pad, compute body params
  IGNITION: throttle=1.0, activate_next_stage()
  VERTICAL_CLIMB: pitch=90, heading=target. Exit at altitude > turn_start_alt
  PITCH_OVER: Begin gravity turn ODE integration. Exit when pitch < 85
  GRAVITY_TURN: Continue ODE. Max-Q limiter + apoapsis feathering. Exit when apo > 0.95*target
  THROTTLE_DOWN: throttle=0.1 (fine control). Exit when apo > 0.98*target
  MECO: throttle=0, disengage autopilot
  COMPLETE: report maneuver result

Tuning defaults (Kerbin sea-level launch):
  turn_start_alt    = 1000 m       # begin pitch-over
  q_limit           = 20000 Pa     # Max-Q dynamic pressure ceiling
  Max-Q throttle    : if q_dyn > q_limit → throttle = 0.6 (reduce aero stress)
  Apoapsis feathering (throttle schedule as apo approaches target):
      apo < 80% target  → throttle = 1.0
      apo ≈ 95% target  → throttle = 0.4
      apo ≈ 98% target  → throttle = 0.1
  Termination guard : apo >= target * 0.98 AND q_dyn < 100 Pa
  Integration       : Forward Euler, dt = GNC tick period (50 ms at 20 Hz)
  Note: these are starting defaults. Different bodies (Duna, Eve) or vessel
  TWR ranges will need different values — expose via config (Appendix C).
```

**Node Executor (used by circularization, Hohmann burns, etc.):**
```
PLAN -> WARP -> ALIGN -> WAIT_FOR_BURN -> FULL_BURN -> PRECISION_BURN -> SHUTDOWN -> COMPLETE

  PLAN: Compute delta-v, burn time (Tsiolkovsky), burn start UT.
        burn_start_ut = node.ut - burn_time/2 - 5s  (5s warp margin)
  WARP: warp_to(burn_start_ut - margin). Cancel warp on arrival.
  ALIGN: SAS maneuver mode, wait ~6s for attitude settle
  WAIT_FOR_BURN: wait until ut >= burn_start_ut
  FULL_BURN: throttle=1.0. If thrust == 0 → stage and continue.
        Re-check staging each tick (multi-stage burns).
        Exit when remaining_dv < 5 m/s
  PRECISION_BURN: throttle=0.05 (V1-tested value for fine accuracy).
        If thrust == 0 → stage and continue.
        Exit when remaining_dv < 0.5 m/s OR dv starts increasing
        (overshoot guard: if remaining_dv at tick N > tick N-1, shut down)
  SHUTDOWN: throttle=0, remove node, SAS stability
  COMPLETE: report predicted vs actual delta-v accuracy
```

**Circularization:**
```
PLAN -> COMPUTE_DV1 -> CREATE_NODE_AP -> EXECUTE_BURN_1 -> EVALUATE -> [COMPLETE or CORRECTION]

  PLAN: Read current orbit. Determine circularization point (apoapsis for
        post-launch, periapsis for capture). Validate: orbit must not be
        escaping (e < 1.0).
  COMPUTE_DV1: dv1 = circularization_delta_v(mu, r_circ, a_current)
  CREATE_NODE_AP: Add maneuver node at the circularization point with
                  prograde = dv1
  EXECUTE_BURN_1: Delegate to NodeExecutor
  EVALUATE: Check resulting orbit circularity.
      If |dv_remaining| > 1 m/s (residual from burn inaccuracy):
          -> CORRECTION: compute dv2 at opposite apse, create node, execute
      Else:
          -> COMPLETE
  COMPLETE: Report final orbit (Ap, Pe, eccentricity)

  Threshold: circularization is "good enough" when |Ap - Pe| / target_alt < 0.02
  (2% tolerance). Beyond that, add a correction burn.
```

**Hohmann Transfer:**
```
COMPUTE -> WAIT_PHASE -> CREATE_NODE_1 -> EXECUTE_BURN_1 -> COAST -> CREATE_NODE_2 -> EXECUTE_BURN_2 -> COMPLETE

  COMPUTE: Calculate dv1, dv2, transfer time, phase angle.
        tof = hohmann_transfer_time(mu, r1, r2)
        w2  = mean_motion(mu, r2)          # target angular velocity
        lead_angle    = w2 * tof           # how far target moves during transfer
        phase_required = pi - lead_angle   # where target must be at departure
  WAIT_PHASE: Monitor current_phase_angle vs phase_required.
        Exit when |current_phase - phase_required| < phase_tolerance (default 1°).
        Use warp to speed through wait (warp_to estimated alignment UT).
  CREATE_NODE_1: Add node (prograde=dv1) at computed UT
  EXECUTE_BURN_1: Delegate to NodeExecutor
  COAST: Warp to SOI change or transfer orbit apoapsis
  CREATE_NODE_2: Add node (prograde=dv2)
  EXECUTE_BURN_2: Delegate to NodeExecutor
  COMPLETE: Report final orbit
```

---

## 4. Orbital Mechanics Module (`knav/astro/`)

**Pure math, zero KRPC dependency.** Every function takes scalar/vector inputs and returns scalar/vector outputs. Fully unit-testable.

Port existing formulas from `core/utils/formulas.py` and expand significantly.

### 4.1 `kepler.py` - Keplerian Orbit Math

```python
vis_viva(mu, r, a) -> float
    # v = sqrt(mu * (2/r - 1/a))

orbital_period(mu, a) -> float
    # T = 2*pi*sqrt(a^3/mu)

mean_motion(mu, a) -> float
    # n = sqrt(mu/a^3)

escape_velocity(mu, r) -> float
    # v_e = sqrt(2*mu/r)

specific_orbital_energy(mu, a) -> float
    # epsilon = -mu/(2*a)

specific_angular_momentum(mu, a, e) -> float
    # h = sqrt(mu * a * (1 - e^2))

radius_at_true_anomaly(a, e, nu) -> float
    # r = a(1 - e^2) / (1 + e*cos(nu))

velocity_at_true_anomaly(mu, a, e, nu) -> tuple[float, float]
    # returns (v_radial, v_transverse)

mean_anomaly_from_eccentric(E, e) -> float
    # Kepler's equation: M = E - e*sin(E)

eccentric_anomaly_from_mean(M, e, tol=1e-10) -> float
    # Solve Kepler's equation (Newton-Raphson)

true_anomaly_from_eccentric(E, e) -> float
    # nu = 2*atan(sqrt((1+e)/(1-e)) * tan(E/2))

time_since_periapsis(mu, a, e, nu) -> float
gravity_local(mu, r) -> float       # g = mu/r^2
surface_gravity(mu, R) -> float     # g0 = mu/R^2
sphere_of_influence(a, m_body, m_parent) -> float
    # r_SOI = a * (m_body/m_parent)^(2/5)
```

### 4.2 `maneuver_math.py` - Delta-V & Transfer Calculations

```python
# --- Hohmann Transfer ---
hohmann_delta_v(mu, r1, r2) -> tuple[float, float]
    # dv1 = sqrt(mu/r1) * (sqrt(2*r2/(r1+r2)) - 1)
    # dv2 = sqrt(mu/r2) * (1 - sqrt(2*r1/(r1+r2)))

hohmann_transfer_time(mu, r1, r2) -> float
    # t = pi * sqrt((r1+r2)^3 / (8*mu))

hohmann_transfer_sma(r1, r2) -> float
    # a_t = (r1 + r2) / 2

hohmann_phase_angle(r1, r2) -> float
    # alpha = pi * (1 - (1/(2*sqrt(2))) * sqrt((r1/r2 + 1)^3))

hohmann_wait_time(mu, r1, r2, current_phase) -> float
    # Uses synodic period: w1 = sqrt(mu/r1^3), w2 = sqrt(mu/r2^3)
    # wait = (required_phase - current_phase) / (w1 - w2)

# --- Bi-Elliptic Transfer ---
bielliptic_delta_v(mu, r1, r2, r_intermediate) -> tuple[float, float, float]
    # Three burns. More efficient than Hohmann when r2/r1 > 11.94

# --- Plane Change ---
plane_change_delta_v(v, delta_i) -> float
    # dv = 2 * v * sin(delta_i / 2)

combined_plane_change_delta_v(mu, r, delta_i, r_target) -> float
    # Combined plane change + orbit raise at optimal point

# --- Circularization ---
circularization_delta_v(mu, r_circ, a_current) -> float
    # dv = sqrt(mu/r_circ) - vis_viva(mu, r_circ, a_current)

# --- Deorbit ---
deorbit_delta_v(mu, r_current, r_periapsis_target) -> float

# --- Burn Time (Tsiolkovsky) ---
burn_time(delta_v, thrust, isp, g0, m0) -> float
    # m1 = m0 / exp(dv / (isp * g0))
    # m_dot = thrust / (isp * g0)
    # t = (m0 - m1) / m_dot

mass_flow_rate(thrust, isp, g0) -> float
    # m_dot = F / (Isp * g0)

# --- Phase Angle ---
current_phase_angle(vessel_pos, target_pos) -> float
    # atan2-based angle difference in common reference frame

synodic_period(mu, r1, r2) -> float
    # T_syn = 2*pi / |w1 - w2|

# --- Hohmann Phasing Helpers ---
hohmann_lead_angle(mu, r1, r2) -> float
    # How far the target moves during the transfer
    # tof = pi * sqrt((r1+r2)^3 / (8*mu))
    # w2  = sqrt(mu / r2^3)
    # lead_angle = w2 * tof

hohmann_phase_required(mu, r1, r2) -> float
    # Required phase angle at departure
    # phase_required = pi - hohmann_lead_angle(mu, r1, r2)

# --- Gravity Turn ODE ---
dgamma_dt(v, r, gamma, mu, T, m, alpha=0.0, L=0.0) -> float
    # dg/dt = (v/r)*cos(g) - (mu/(r^2*v))*cos(g) + (T/(m*v))*cos(a) + L/(m*v)

dv_dt(T, m, g_r, gamma, D=0.0) -> float
    # dv/dt = T/m - g(r)*sin(gamma) - D/m

dr_dt(v, gamma) -> float
    # dr/dt = v*sin(gamma)
```

**Atmosphere note:** The `astro` module is vacuum-only — it has no atmospheric drag
or pressure model. The gravity turn maneuver handles atmosphere **reactively** by
reading `vessel.flight().dynamic_pressure` from KRPC telemetry each tick and
throttling down when Max-Q is exceeded. KSP's internal physics engine handles
the actual aerodynamic simulation; KNAV just responds to the measured pressure.

### 4.3 `lambert.py` - Lambert Problem Solver

```python
solve_lambert(r1_vec, r2_vec, tof, mu, prograde=True) -> tuple[ndarray, ndarray]
    # Universal variable formulation with Stumpff functions
    # Returns (v1_vec, v2_vec) for departure/arrival velocities

stumpff_c2(psi) -> float
stumpff_c3(psi) -> float
```

Essential for rendezvous planning: given current position, target position, and desired transfer time, Lambert gives the required departure velocity.

### 4.4 `propagator.py` - Orbit Propagation

```python
propagate_kepler(mu, r0, v0, dt) -> tuple[ndarray, ndarray]
    # Universal variable formulation, returns (r_final, v_final)

propagate_to_true_anomaly(mu, elements, target_nu) -> tuple[ndarray, ndarray]
```

### 4.5 `constants.py` - KSP Solar System

```python
KSP_BODIES = {
    "Kerbol": {"mu": 1.1723328e18, "R": 261_600_000, "soi": inf},
    "Kerbin": {"mu": 3.5316e12,    "R": 600_000, "soi": 84_159_286, "atm": 70_000, "g0": 9.81},
    "Mun":    {"mu": 6.5138398e10, "R": 200_000, "soi": 2_429_559},
    "Minmus": {"mu": 1.7658e9,     "R": 60_000,  "soi": 2_247_428},
    "Duna":   {"mu": 3.0136321e11, "R": 320_000, "soi": 47_921_949, "atm": 50_000},
    "Eve":    {"mu": 8.1717302e12, "R": 700_000, "soi": 85_109_365, "atm": 90_000},
    "Jool":   {"mu": 2.8252800e14, "R": 6_000_000, "soi": 2_455_985_200, "atm": 200_000},
    # ... all KSP bodies
}
# These are defaults; FSW reads actual values from KRPC at runtime.
```

---

## 5. KRPC Integration Layer (`knav/krpc_interface/`)

### 5.1 Connection Manager (`connection.py`)

**Singleton.** One connection for the entire application. Replaces the 10+ independent `krpc.connect()` calls.

```python
class KRPCConnection:
    _instance = None
    _conn = None

    # Properties: conn, space_center, vessel, ut, is_connected
    # Methods: connect(), disconnect(), reconnect() (exponential backoff 1s-30s), health_check()

    # Config from knav/config.py:
    #   KRPC_ADDRESS = "192.168.1.82"  (from .env)
    #   KRPC_RPC_PORT = 50000
    #   KRPC_STREAM_PORT = 50001
```

### 5.2 Stream Manager (`streams.py`)

Creates streams once when vessel becomes active, tears down on disconnect/vessel switch.

```python
class StreamManager:
    # initialize(conn, vessel) - creates all Navigation streams
    # get(name) -> callable   - returns stream reader
    # teardown()              - removes all streams
    # refresh_vessel(vessel)  - tear down + recreate for new vessel
```

### 5.3 Scene Manager (`scene.py`)

```python
class SceneManager:
    # Scenes: FLIGHT, SPACE_CENTER, VAB, SPH, TRACKING, UNKNOWN
    # Capabilities per scene: TELEMETRY, CONTROL, MANEUVER, WARP, STAGING, PARTS, SCIENCE
    # detect_scene() -> Scene
    # can(capability) -> bool
```

### 5.4 Error Handling (`errors.py`)

```python
class KRPCError(Exception): ...
class ConnectionLostError(KRPCError): ...
class VesselNotAvailableError(KRPCError): ...
class SceneNotSupportedError(KRPCError): ...
class StreamError(KRPCError): ...
class ManeuverError(KRPCError): ...
```

**Error Recovery Strategies:**

| Scenario | Detection | Recovery |
|---|---|---|
| **Mid-burn disconnect** | `ConnectionLostError` during FULL_BURN/PRECISION_BURN | Cache the active command + remaining dv. On reconnect: read vessel state, compare orbit. If burn clearly incomplete, re-create node with residual dv and resume NodeExecutor from PLAN. If orbit looks good, mark complete. |
| **Scene change** (user exits to Space Center/VAB) | `SceneManager.detect_scene() != FLIGHT` | Teardown all streams (they become invalid). Pause mission (→ PAUSED state). Emit `scene_change` event. When FLIGHT resumes, re-initialize streams and resume mission. |
| **Vessel switch** (user switches to another vessel) | `vessel` reference changes (vessel.name or id mismatch) | Abort active maneuver (throttle=0). Reset all per-maneuver SMs. Teardown streams. Re-initialize for new vessel. Emit `vessel_switch` event. |
| **Vessel destroyed** | `vessel` reference throws `RPCError` on access | Teardown streams. Set vehicle SM → IDLE. Emit `vessel_lost` alert. Wait for user to select new vessel or revert. |
| **Stream stale / NaN** | Stream callback returns `None` or `float('nan')` | Skip tick (do not run Guidance/Control with bad data). Log warning. If stale for > 5 consecutive ticks, teardown and recreate streams. |

---

## 6. Backend Architecture (`knav/api/`)

### 6.1 REST Endpoints

**Vessel** (`/api/vessel`):
- `GET /` - Current vessel state snapshot
- `GET /systems` - All systems status (engines, comms, resources)
- `GET /resources` - Resources with amounts
- `GET /crew` - Crew manifest
- `PUT /name` - Rename vessel

**Orbit** (`/api/orbit`):
- `GET /` - Current orbital elements
- `GET /prediction` - Predicted orbit after next node
- `GET /bodies` - Celestial bodies data
- `GET /phase-angle/{target}` - Phase angle to target

**Maneuver** (`/api/maneuver`):
- `POST /gravity-turn` - `{target_alt, heading}`
- `POST /circularize` - `{target_alt?}`
- `POST /hohmann` - `{target_body}`
- `POST /bielliptic` - `{target_body, r_intermediate}`
- `POST /plane-change` - `{target_inclination}`
- `POST /rendezvous` - `{target_vessel}`
- `POST /deorbit` - `{target_periapsis}`
- `POST /land`
- `POST /execute-node`
- `GET /status` - Current maneuver status
- `POST /abort`
- `GET /plan/hohmann/{target}` - Preview without executing
- `GET /plan/circularize` - Preview

**Mission** (`/api/mission`):
- `POST /` - Create & start mission
- `GET /` - Current mission status
- `GET /phases` - All phases
- `POST /pause`, `/resume`, `/abort`
- `GET /templates` - Pre-built missions
- `POST /templates/{name}` - Start template

**Command** (`/api/command`):
- `POST /throttle` - `{value: 0.0-1.0}`
- `POST /stage` - Activate next stage
- `POST /sas` - `{enabled, mode}`
- `POST /rcs` - `{enabled}`
- `POST /warp` - `{ut}` or `{factor}`
- `POST /gear`, `/lights`, `/solar-panels`, `/antennas`, `/fairings`
- `POST /action-group/{group}`

**Scene** (`/api/scene`):
- `GET /` - Current scene + capabilities
- `GET /connection` - KRPC health

### 6.2 WebSocket Channels

**Telemetry** (`/ws/telemetry`) - 10 Hz:
```json
{
  "timestamp": 123456.789, "met": 3420.5,
  "channels": {
    "orbit": { "apoapsis_altitude": 150234.5, "periapsis_altitude": 149876.2, ... },
    "flight": { "altitude_mean": 150100.0, "speed_orbital": 2290.5, "pitch": 0.3, ... },
    "propulsion": { "thrust": 0.0, "twr": 0.0, "delta_v_remaining": 2400.5, ... },
    "resources": { "liquid_fuel": {"amount": 450.0, "max": 720.0}, ... }
  }
}
```

Client protocol:
```json
// Subscribe to channels
{"action": "subscribe", "channels": ["orbit", "flight", "propulsion"]}

// Unsubscribe from channels
{"action": "unsubscribe", "channels": ["propulsion"]}

// Server acknowledgment (sent after subscribe/unsubscribe)
{"type": "subscription_ack", "active_channels": ["orbit", "flight"]}
```

Backpressure: each WebSocket client has a bounded send queue (max 64 messages).
On overflow, drop the **oldest** telemetry frame (newest data wins). Events and
logs are never dropped — they queue separately.

Reconnect: on new WebSocket connection, the server immediately sends a full
state snapshot (current VesselState + active maneuver status + vehicle SM state)
before streaming incremental updates. This lets the frontend recover cleanly
without a separate REST fetch.

**Events** (`/ws/events`) - Push on occurrence:
```json
{"type": "state_change", "data": {"vehicle_state": "ORBIT", "previous_state": "COAST_ASCENT"}}
{"type": "maneuver_status", "data": {"maneuver": "circularization", "phase": "FULL_BURN", "remaining_dv": 42.3}}
{"type": "mission_phase", "data": {"phase": "Transfer to Mun", "index": 2, "total_phases": 8}}
{"type": "alert", "data": {"severity": "warning", "message": "Low fuel: 15%"}}
{"type": "staging", "data": {"stage": 5, "remaining_stages": 3}}
{"type": "soi_change", "data": {"from": "Kerbin", "to": "Mun"}}
```

**Logs** (`/ws/logs`):
```json
{"level": "INFO", "tag": "BURN", "message": "Node execution initiated - 245.3 m/s burn", "source": "maneuvers.node_executor"}
```

### 6.3 Logging Architecture

Uses `structlog` with bound loggers per module for structured, contextual logging.

```python
import structlog
log = structlog.get_logger("knav.fsw.guidance")  # bound per module
log.info("burn_started", maneuver="circularization", dv=245.3)
```

**Output renderers (configured at startup):**
- **Console** (dev/terminal): `structlog.dev.ConsoleRenderer` — colored, human-readable
- **JSON** (WebSocket `/ws/logs`): `structlog.processors.JSONRenderer` — machine-parseable, forwarded to event bus as `log_entry` events

**Log levels by subsystem:**
| Subsystem | INFO | DEBUG |
|---|---|---|
| State machines | Transitions (`COAST_ASCENT → ORBIT`) | Guard evaluations |
| Maneuvers | Phase changes, burn start/stop, result | Per-tick dv remaining, throttle |
| Navigation | Vessel switch, stream refresh | Per-tick VesselState values |
| KRPC | Connect, disconnect, reconnect | RPC call timing |
| API | Request handling, WS connect/disconnect | Subscription changes |

### 6.4 Event Bus (`knav/events/bus.py`)

Thread-safe in-process pub/sub. FSW publishes from its thread; API consumers await events.

Events published per tick:
- `telemetry_frame` (every tick, throttled to 10 Hz for WS)
- `state_change` (on vehicle/mission SM transition)
- `maneuver_status` (on maneuver phase change)
- `log_entry` (on every log call)
- `alert` (on warning/error conditions)

---

## 7. Frontend - Mission Control Center

### 7.1 Tech Stack

- **Framework:** React 19 + TypeScript
- **Component Library:** shadcn/ui (Radix UI primitives + Tailwind CSS)
- **Build:** Vite
- **Styling:** Tailwind CSS v4 + shadcn/ui dark theme (customized with Gruvbox-inspired palette)
- **Charts:** Recharts (React-native, works with shadcn) or uPlot for high-frequency telemetry
- **Orbital viz:** Custom Canvas2D renderer (2D orbit map)
- **WebSocket:** Native browser WebSocket with reconnection wrapper
- **State Management:** Zustand (lightweight, works well with WebSocket streams)

**Build & Serve:**
- **Dev:** Vite dev server (`npm run dev` on port 5173) with proxy config to forward `/api/*` and `/ws/*` to FastAPI (port 8000). No CORS issues in dev because all requests go through the Vite proxy.
- **Prod:** `npm run build` outputs to `knav/frontend/dist/`. FastAPI serves this directory via `StaticFiles` mount. Single origin, no proxy needed.
- **CORS:** FastAPI adds `CORSMiddleware` in dev mode only (`allow_origins=["http://localhost:5173"]`). In prod, frontend is same-origin so CORS is not needed.

### 7.2 Layout

```
┌───────────────────────────────────────────────────────────────┐
│  KNAV Mission Control         Connected *   UT: 1y 234d 12:45│
├────────┬──────────────────────────────────────────────────────┤
│  NAV   │  [Main Content Area - switches on nav selection]     │
│        │                                                      │
│ [FD]   │  Flight Display / Orbit Map / Maneuvers / etc.       │
│ [OM]   │                                                      │
│ [MN]   │  ┌──────────────────┬───────────────────────────┐   │
│ [MS]   │  │ Telemetry Panel  │  Log Panel                │   │
│ [SY]   │  │ (real-time)      │  (streaming entries)      │   │
│ [LG]   │  └──────────────────┴───────────────────────────┘   │
└────────┴──────────────────────────────────────────────────────┘

FD = Flight Display    OM = Orbit Map    MN = Maneuvers
MS = Mission           SY = Systems      LG = Logs
```

### 7.3 Views

**Flight Display (FD)** - Primary operational view:
- 4-panel grid: ORBIT (Ap/Pe/Ecc/Inc/Period), VELOCITY (orbital/surface/vert/horiz), ATTITUDE (pitch/hdg/roll/SAS), PROPULSION (thrust/TWR/Isp/dV/stage)
- Maneuver status bar
- Active alerts

**Orbit Map (OM)** - 2D top-down:
- Central body, current orbit ellipse, vessel position marker
- Target body orbit (for transfers), transfer ellipse
- Maneuver nodes, Ap/Pe markers, SOI boundary
- AN/DN indicators for plane changes

**Maneuvers (MN)** - Planning:
- Quick action buttons (Circularize, Hohmann, Plane Change, etc.)
- Detail panel with delta-v, transfer time, phase angle, wait time
- Plan (preview) vs Execute buttons

**Mission (MS)** - Timeline:
- Phase list with status icons (completed/active/pending)
- Progress timeline bar
- Template library (Launch to LKO, Mun, Minmus, Duna, custom builder)
- Pause/Abort controls

**Systems (SY)** - Vehicle monitoring:
- Propulsion (engines, thrust, ISP, gimbal)
- Power (solar panels, batteries)
- Comms (signal strength, delay, link path)
- Resources (fuel bars with percentages)
- Science (experiments, run/transmit/dump)
- Controls (staging, fairings, gear, lights, RCS)

**Logs (LG)** - Full-screen scrollable log with filter/search

### 7.4 Alert System

| Severity | Example |
|---|---|
| critical | "No thrust during burn", "Connection lost" |
| warning | "Low fuel: 15%", "High dynamic pressure" |
| info | "SOI change: entering Mun", "Stage 5 activated" |
| success | "Orbit achieved", "Maneuver complete: 99.2% accuracy" |

Toast notifications + collected in Flight Display alerts panel.

---

## 8. Data Models (`knav/models/`)

All Pydantic `BaseModel`. Used by both FSW and API.

**VesselState:** timestamp_ut, met, name, situation, body_name, mass/dry_mass, altitude (mean/surface), lat/lon, speeds (orbital/surface/vert/horiz), attitude (pitch/heading/roll), aero (dynamic_pressure/mach/g_force), propulsion (thrust/twr/isp/dv), flight_path_angle, local_gravity, orbit (embedded OrbitState)

**OrbitState:** body_name, apoapsis/periapsis (+ altitudes), semi_major_axis, eccentricity, inclination, LAN, argument_of_periapsis, true/mean_anomaly, period, time_to_apoapsis/periapsis, radius, speed

**OrbitalElements:** a, e, i, omega, Omega, nu, mu (pure math, no KRPC)

**ManeuverPlan:** type, delta_v_total, burns (list of BurnPlan), transfer_time, phase angles, wait_time, resulting_orbit

**ManeuverStatus:** type, state, phase, progress_percent, remaining_dv, elapsed_time, burns completed/total

**Mission:** id, name, status, phases (list of MissionPhase), current_phase_index, timestamps

**Enums:** VehicleState, MissionStatus, ManeuverState, SASMode, Scene

---

## 9. Information Flow - End to End

### Command Flow: "Execute Hohmann Transfer to Mun"

1. User clicks Execute in Maneuvers view
2. Browser: `POST /api/maneuver/hohmann {"target_body": "Mun"}`
3. FastAPI router calls `fsw.start_maneuver(HohmannTransfer(target="Mun"))`
4. FSW creates HohmannTransfer, maneuver SM enters COMPUTE
5. `plan()` calls `astro.maneuver_math.hohmann_delta_v(mu, r1, r2)` -> dv1, dv2
6. Computes phase angle, wait time via `astro.maneuver_math`
7. SM -> WAIT_PHASE: each tick checks current vs required phase angle
8. SM -> CREATE_NODE_1: Control adds maneuver node via KRPC
9. SM -> EXECUTE_BURN_1: delegates to NodeExecutor (WARP -> ALIGN -> BURN -> PRECISION -> SHUTDOWN)
10. SM -> COAST: warp to insertion point
11. SM -> CREATE_NODE_2 -> EXECUTE_BURN_2 (same pattern)
12. SM -> COMPLETE: event bus publishes completion
13. Throughout: telemetry streams at 10 Hz over WebSocket, UI updates live

### Telemetry Flow

```
KRPC Streams (continuous from KSP)
  -> Navigation.update() (each 50ms tick)
  -> VesselState built
  -> EventBus.publish("telemetry_frame")
  -> WebSocket Manager broadcasts (throttled to 10 Hz)
  -> Browser receives JSON, updates reactive stores
  -> UI components re-render
```

---

## 10. Testing Strategy

| Layer | What | KRPC? | Tool |
|---|---|---|---|
| astro/ | All orbital math | No | pytest |
| fsw/state_machines/ | State transitions, guards | No | pytest |
| models/ | Pydantic validation | No | pytest |
| fsw/gnc/ | Navigation/guidance/control logic | Mocked | pytest + mock |
| api/routers/ | REST endpoints | Mocked FSW | pytest + httpx |
| krpc_interface/ | Connection, streams, scenes | Yes (real KSP) | manual pytest |
| fsw/maneuvers/ | Full maneuver execution | Yes (real KSP) | manual pytest |
| E2E | Full mission from web UI | Yes (real KSP) | Manual |

Key test examples for `astro/`:
- `vis_viva` for circular orbit: v should equal sqrt(mu/r)
- Hohmann dv Kerbin->Mun: dv1 ~860 m/s, dv2 ~220 m/s
- LKO orbital period at 100km: ~1950 seconds
- Burn time via Tsiolkovsky: validate against manual calculation

---

## 11. Implementation Sequence

**Phase 1: Foundation (no KRPC needed)**
1. Create `knav/` package structure
2. Implement `knav/models/` (all Pydantic models + enums)
3. Implement `knav/astro/` (port formulas from `core/utils/formulas.py`, add kepler.py, lambert.py, propagator.py)
4. Write tests for `astro/` (validate every formula)
5. Implement `knav/events/` (event bus)

**Phase 2: KRPC Layer**
6. Implement `knav/krpc_interface/connection.py` (singleton)
7. Implement `knav/krpc_interface/streams.py` (stream manager)
8. Implement `knav/krpc_interface/scene.py` (scene detection)
9. Test with real KSP

**Phase 3: Flight Software Core**
10. `knav/fsw/gnc/navigation.py` (state estimation)
11. `knav/fsw/gnc/control.py` (actuator commands)
12. `knav/fsw/gnc/guidance.py` (command generation)
13. `knav/fsw/state_machines/` (vehicle, mission, maneuver SMs)
14. `knav/fsw/executive.py` (main GNC loop)
15. `knav/fsw/maneuvers/base.py` (abstract Maneuver)
16. `knav/fsw/maneuvers/node_executor.py` (port from `core/utils/helpers.py:execute_node`)
17. Port gravity turn from `core/launch/gt.py`
18. Port circularization from `core/orbital/circularization.py`
19. Port Hohmann from `core/orbital/hohmann_transfer.py`
20. Test each maneuver with real KSP

**Phase 4: Backend API**
21. FastAPI app factory + dependency injection
22. REST routers (vessel, orbit, maneuver, mission, command, scene)
23. WebSocket endpoints (telemetry, events, logs)
24. Test API with httpx

**Phase 5: Frontend**
25. Vite + React + TypeScript + shadcn/ui setup
26. WebSocket client with reconnection
27. Flight Display view
28. Orbit Map (Canvas2D renderer)
29. Maneuvers view
30. Mission view
31. Systems view
32. Logs view

**Phase 6: Advanced Maneuvers**
33. Plane change
34. Bi-elliptic transfer
35. Lambert solver
36. Rendezvous
37. Docking approach
38. Deorbit & landing

---

## Critical Files to Port

| Current File | Port To | Key Content |
|---|---|---|
| `core/utils/formulas.py` | `knav/astro/kepler.py` + `maneuver_math.py` | vis_viva, dgamma_dt, hohmann_delta_v, burn_time, phase_angle |
| `core/launch/gt.py` | `knav/fsw/maneuvers/gravity_turn.py` | Gravity turn with connection param, app_log logger |
| `core/orbital/hohmann_transfer.py` | `knav/fsw/maneuvers/hohmann_transfer.py` | Phase angle calc, wait time, two-burn pattern |
| `core/utils/helpers.py:execute_node` | `knav/fsw/maneuvers/node_executor.py` | Two-phase throttle (full + precision), staging detection |
| `core/orbital/circularization.py` | `knav/fsw/maneuvers/circularization.py` | Two-burn circularization at apo + peri |
| `core/parts/part_control.py` | `knav/fsw/systems/parts.py` | Fairing, antenna, solar panel control |
| `app/connection.py` | `knav/krpc_interface/connection.py` | Dual-connection pattern -> unified singleton |

## Verification

After each phase, verify:
- **Phase 1:** `pytest tests/test_astro/` passes with all formulas validated
- **Phase 2:** Connect to KSP, read telemetry streams, detect scene
- **Phase 3:** Execute gravity turn from pad to orbit via FSW loop
- **Phase 4:** `curl` endpoints return correct data, WebSocket streams telemetry
- **Phase 5:** Open browser, see live telemetry, execute maneuver from UI
- **Phase 6:** Complete Mun mission from launch to landing via Mission Control

---

## Appendix A: KSP Solar System Data

All orbital radii are from center of body. Atmosphere depth is altitude above surface.

### Kerbol (Sun)
| Property | Value |
|---|---|
| Gravitational Parameter (mu) | 1.1723328 x 10^18 m^3/s^2 |
| Equatorial Radius | 261,600,000 m |
| SOI | Infinite |

### Kerbin (Home Planet)
| Property | Value |
|---|---|
| mu | 3.5316 x 10^12 m^3/s^2 |
| Equatorial Radius | 600,000 m |
| Surface Gravity | 9.81 m/s^2 |
| SOI | 84,159,286 m |
| Atmosphere Depth | 70,000 m |
| Rotational Period | 21,549.425 s (5h 59m 9.4s) |
| Sidereal Day | 21,549.425 s |
| Orbital Radius (from Kerbol) | 13,599,840,256 m |
| Orbital Period | 9,203,545 s (1 Kerbin year = 426.09 days) |

### Mun (Kerbin Moon)
| Property | Value |
|---|---|
| mu | 6.5138398 x 10^10 m^3/s^2 |
| Equatorial Radius | 200,000 m |
| SOI | 2,429,559 m |
| Atmosphere | None |
| Orbital Radius (from Kerbin) | 12,000,000 m |
| Orbital Period | 138,984.38 s |

### Minmus (Kerbin Moon)
| Property | Value |
|---|---|
| mu | 1.7658 x 10^9 m^3/s^2 |
| Equatorial Radius | 60,000 m |
| SOI | 2,247,428 m |
| Atmosphere | None |
| Orbital Radius (from Kerbin) | 47,000,000 m |
| Orbital Inclination | 6 degrees |
| Orbital Period | 1,077,311 s |

### Other Bodies
| Body | mu (m^3/s^2) | R (m) | SOI (m) | Atm (m) | Orbital R from Parent (m) |
|---|---|---|---|---|---|
| Moho | 1.6860938e11 | 250,000 | 9,646,663 | 0 | 5,263,138,304 |
| Eve | 8.1717302e12 | 700,000 | 85,109,365 | 90,000 | 9,832,684,544 |
| Gilly | 8,289,449.8 | 13,000 | 126,123 | 0 | 31,500,000 |
| Duna | 3.0136321e11 | 320,000 | 47,921,949 | 50,000 | 20,726,155,264 |
| Ike | 1.8568369e10 | 130,000 | 1,049,599 | 0 | 3,200,000 |
| Dres | 2.1484489e10 | 138,000 | 32,832,840 | 0 | 40,839,348,203 |
| Jool | 2.8252800e14 | 6,000,000 | 2,455,985,200 | 200,000 | 68,773,560,320 |
| Laythe | 1.9620000e12 | 500,000 | 3,723,646 | 50,000 | 27,184,000 |
| Vall | 2.0748150e11 | 300,000 | 2,406,401 | 0 | 43,152,000 |
| Tylo | 2.8252800e12 | 600,000 | 10,856,518 | 0 | 68,500,000 |
| Bop | 2.4868349e9 | 65,000 | 1,221,061 | 0 | 128,500,000 |
| Pol | 7.2170208e8 | 44,000 | 1,042,139 | 0 | 179,890,000 |
| Eeloo | 7.4410815e10 | 210,000 | 119,082,942 | 0 | 90,118,820,000 |

### Common Reference Orbits
| Orbit | Altitude | Radius from Kerbin center | Orbital Velocity |
|---|---|---|---|
| Low Kerbin Orbit (LKO) | 80,000 m | 680,000 m | ~2,279 m/s |
| Standard LKO | 100,000 m | 700,000 m | ~2,246 m/s |
| Mun Transfer | 80 km -> 12,000 km | varies | dv1 ~860 m/s |
| Minmus Transfer | 80 km -> 47,000 km | varies | dv1 ~930 m/s |
| Kerbin Escape | any | any | v_e = sqrt(2*mu/r) |

---

## Appendix B: Orbital Mechanics Reference

### Fundamental Equations

**1. Vis-Viva Equation** (velocity at any point in orbit):
```
v = sqrt(mu * (2/r - 1/a))
```
Where: mu = gravitational parameter, r = current radius, a = semi-major axis

**2. Circular Orbital Velocity:**
```
v_c = sqrt(mu / r)
```

**3. Escape Velocity:**
```
v_e = sqrt(2 * mu / r)
```

**4. Orbital Period:**
```
T = 2 * pi * sqrt(a^3 / mu)
```

**5. Specific Orbital Energy:**
```
epsilon = -mu / (2 * a) = v^2/2 - mu/r
```

**6. Specific Angular Momentum:**
```
h = sqrt(mu * a * (1 - e^2))
```

**7. Radius at True Anomaly (conic equation):**
```
r = a * (1 - e^2) / (1 + e * cos(nu))
```

### Kepler's Equation

Relates mean anomaly M, eccentric anomaly E, and eccentricity e:
```
M = E - e * sin(E)
```
Solve for E given M using Newton-Raphson:
```
E_{n+1} = E_n - (E_n - e*sin(E_n) - M) / (1 - e*cos(E_n))
```

True anomaly from eccentric anomaly:
```
nu = 2 * atan(sqrt((1+e)/(1-e)) * tan(E/2))
```

### Hohmann Transfer

Minimum-energy two-impulse transfer between coplanar circular orbits.

```
Transfer semi-major axis: a_t = (r1 + r2) / 2
Transfer time: t = pi * sqrt(a_t^3 / mu)

First burn (at r1, prograde):
  dv1 = sqrt(mu/r1) * (sqrt(2*r2/(r1+r2)) - 1)

Second burn (at r2, prograde for raising, retrograde for lowering):
  dv2 = sqrt(mu/r2) * (1 - sqrt(2*r1/(r1+r2)))
```

**Phase angle for intercept:**
```
alpha = pi * (1 - (1/(2*sqrt(2))) * sqrt((r1/r2 + 1)^3))
```

**Wait time for phase alignment:**
```
w1 = sqrt(mu / r1^3)  (angular velocity of inner orbit)
w2 = sqrt(mu / r2^3)  (angular velocity of outer orbit)
T_synodic = 2*pi / |w1 - w2|
wait = (alpha_required - alpha_current) / (w1 - w2)
```

### Bi-Elliptic Transfer

Three-impulse transfer through intermediate apoapsis. More efficient than Hohmann when r2/r1 > 11.94.

```
a1 = (r1 + r_intermediate) / 2
a2 = (r2 + r_intermediate) / 2

dv1 = sqrt(2*mu/r1 - mu/a1) - sqrt(mu/r1)
dv2 = sqrt(2*mu/r_intermediate - mu/a2) - sqrt(2*mu/r_intermediate - mu/a1)
dv3 = sqrt(2*mu/r2 - mu/a2) - sqrt(mu/r2)
```

### Plane Change

Simple inclination change at constant altitude:
```
dv = 2 * v * sin(delta_i / 2)
```
Most efficient at apoapsis (lowest velocity) or at ascending/descending node.

### Circularization

Delta-v to circularize at radius r_circ from an elliptical orbit with semi-major axis a:
```
dv = sqrt(mu/r_circ) - sqrt(mu * (2/r_circ - 1/a))
```

### Deorbit

Retrograde delta-v to lower periapsis for reentry:
```
Current orbit: circular at r
Target periapsis: r_pe
New SMA: a_new = (r + r_pe) / 2
dv = sqrt(mu/r) - sqrt(mu * (2/r - 1/a_new))
```

### Burn Time (Tsiolkovsky Rocket Equation)

```
delta_v = Isp * g0 * ln(m0 / m1)

Solving for burn time:
  m1 = m0 / exp(dv / (Isp * g0))       # post-burn mass
  m_dot = F / (Isp * g0)                # mass flow rate
  t = (m0 - m1) / m_dot                 # burn duration
```

### Gravity Turn Equations

Flight-path angle rate:
```
dgamma/dt = (v/r)*cos(gamma) - (mu/(r^2*v))*cos(gamma) + (T/(m*v))*cos(alpha) + L/(m*v)
```

Speed rate:
```
dv/dt = T/m - g(r)*sin(gamma) - D/m
```

Radial velocity:
```
dr/dt = v * sin(gamma)
```

Where: gamma = flight path angle, T = thrust, m = mass, D = drag, L = lift, alpha = angle of attack

### Lambert's Problem

Given two position vectors r1, r2 and a time of flight, find the orbit connecting them. Essential for rendezvous planning.

Universal variable formulation with Stumpff functions:
```
Stumpff c2(psi): cos(sqrt(psi))-1 / -psi  (or series for psi~0)
Stumpff c3(psi): (sqrt(psi)-sin(sqrt(psi))) / sqrt(psi^3)

Iteratively solve for z:
  y(z) = r1 + r2 + A*(z*S(z) - 1) / sqrt(C(z))
  F(z) = (y(z)/C(z))^1.5 * S(z) + A*sqrt(y(z)) - sqrt(mu)*tof = 0

Then use Lagrange coefficients f, g, g_dot to get v1, v2.
```

### Sphere of Influence

Radius where a body's gravity dominates over its parent:
```
r_SOI = a * (m_body / m_parent)^(2/5)
```
Where a = semi-major axis of body's orbit around parent.

---

## Appendix C: Configuration Reference

### Environment Variables (.env)

```
KRPC_ADDRESS=192.168.1.82
KRPC_RPC_PORT=50000
KRPC_STREAM_PORT=50001
KRPC_NAME=KNAV Flight Software

# GNC Loop
GNC_RATE_HZ=20
TELEMETRY_BROADCAST_HZ=10

# API
API_HOST=0.0.0.0
API_PORT=8000

# Logging
LOG_LEVEL=INFO
```

### Pydantic Settings (`knav/config.py`)

```python
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    # KRPC
    krpc_address: str = "192.168.1.82"
    krpc_rpc_port: int = 50000
    krpc_stream_port: int = 50001
    krpc_name: str = "KNAV Flight Software"
    krpc_reconnect_max_wait: int = 30

    # GNC
    gnc_rate_hz: int = 20
    telemetry_broadcast_hz: int = 10

    # API
    api_host: str = "0.0.0.0"
    api_port: int = 8000

    # Physics
    g0: float = 9.81  # standard gravity for Isp calculations

    # Gravity Turn Defaults
    gt_turn_start_alt: float = 1000.0       # m, begin pitch-over
    gt_q_limit: float = 20000.0             # Pa, Max-Q throttle-down threshold
    gt_q_throttle: float = 0.6              # throttle when q_dyn > q_limit
    gt_feather_80: float = 1.0              # throttle when apo < 80% target
    gt_feather_95: float = 0.4              # throttle when apo ≈ 95% target
    gt_feather_98: float = 0.1              # throttle when apo ≈ 98% target
    gt_termination_apo_frac: float = 0.98   # apo/target ratio for MECO
    gt_termination_q_max: float = 100.0     # Pa, Max-Q must be below this for MECO

    # Node Executor
    ne_precision_throttle: float = 0.05     # throttle for precision burn phase
    ne_full_burn_threshold: float = 5.0     # m/s remaining → switch to precision
    ne_precision_threshold: float = 0.5     # m/s remaining → shutdown
    ne_warp_margin: float = 5.0             # seconds before burn_start_ut

    # Circularization
    circ_correction_threshold: float = 1.0  # m/s, add correction burn if above
    circ_tolerance_frac: float = 0.02       # |Ap-Pe|/target, "good enough"

    # Hohmann
    hohmann_phase_tolerance_deg: float = 1.0  # degrees, phase angle match window

    model_config = {"env_file": ".env"}
```
