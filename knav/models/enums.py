from enum import Enum, auto


class VehicleState(str, Enum):
    IDLE = "idle"
    PRE_LAUNCH = "pre_launch"
    POWERED_ASCENT = "powered_ascent"
    COAST_ASCENT = "coast_ascent"
    ORBIT = "orbit"
    MANEUVERING = "maneuvering"
    COAST_TRANSFER = "coast_transfer"
    DESCENT = "descent"
    POWERED_DESCENT = "powered_descent"
    LANDED = "landed"
    ABORT = "abort"


class MissionStatus(str, Enum):
    PLANNING = "planning"
    ACTIVE = "active"
    PAUSED = "paused"
    COMPLETED = "completed"
    FAILED = "failed"
    ABORTED = "aborted"


class ManeuverState(str, Enum):
    IDLE = "idle"
    PLANNING = "planning"
    EXECUTING = "executing"
    COMPLETE = "complete"
    FAILED = "failed"
    ABORTED = "aborted"


class ManeuverType(str, Enum):
    GRAVITY_TURN = "gravity_turn"
    CIRCULARIZATION = "circularization"
    HOHMANN_TRANSFER = "hohmann_transfer"
    BIELLIPTIC_TRANSFER = "bielliptic_transfer"
    PLANE_CHANGE = "plane_change"
    RENDEZVOUS = "rendezvous"
    DOCKING = "docking"
    DEORBIT = "deorbit"
    LANDING = "landing"
    NODE_EXECUTOR = "node_executor"


class GravityTurnPhase(str, Enum):
    INIT = "init"
    IGNITION = "ignition"
    VERTICAL_CLIMB = "vertical_climb"
    PITCH_OVER = "pitch_over"
    GRAVITY_TURN = "gravity_turn"
    THROTTLE_DOWN = "throttle_down"
    MECO = "meco"
    COMPLETE = "complete"


class NodeExecutorPhase(str, Enum):
    PLAN = "plan"
    WARP = "warp"
    ALIGN = "align"
    WAIT_FOR_BURN = "wait_for_burn"
    FULL_BURN = "full_burn"
    PRECISION_BURN = "precision_burn"
    SHUTDOWN = "shutdown"
    COMPLETE = "complete"


class CircularizationPhase(str, Enum):
    PLAN = "plan"
    COMPUTE_DV = "compute_dv"
    CREATE_NODE = "create_node"
    EXECUTE_BURN = "execute_burn"
    EVALUATE = "evaluate"
    CORRECTION = "correction"
    COMPLETE = "complete"


class HohmannPhase(str, Enum):
    COMPUTE = "compute"
    WAIT_PHASE = "wait_phase"
    CREATE_NODE_1 = "create_node_1"
    EXECUTE_BURN_1 = "execute_burn_1"
    COAST = "coast"
    CREATE_NODE_2 = "create_node_2"
    EXECUTE_BURN_2 = "execute_burn_2"
    COMPLETE = "complete"


class SASMode(str, Enum):
    STABILITY_ASSIST = "stability_assist"
    MANEUVER = "maneuver"
    PROGRADE = "prograde"
    RETROGRADE = "retrograde"
    NORMAL = "normal"
    ANTI_NORMAL = "anti_normal"
    RADIAL = "radial"
    ANTI_RADIAL = "anti_radial"
    TARGET = "target"
    ANTI_TARGET = "anti_target"


class Scene(str, Enum):
    FLIGHT = "flight"
    SPACE_CENTER = "space_center"
    VAB = "vab"
    SPH = "sph"
    TRACKING = "tracking"
    UNKNOWN = "unknown"


class Capability(str, Enum):
    TELEMETRY = "telemetry"
    CONTROL = "control"
    MANEUVER = "maneuver"
    WARP = "warp"
    STAGING = "staging"
    PARTS = "parts"
    SCIENCE = "science"


class VesselSituation(str, Enum):
    PRE_LAUNCH = "pre_launch"
    FLYING = "flying"
    SUB_ORBITAL = "sub_orbital"
    ORBITING = "orbiting"
    ESCAPING = "escaping"
    LANDED = "landed"
    SPLASHED = "splashed"
    DOCKED = "docked"


class AlertSeverity(str, Enum):
    CRITICAL = "critical"
    WARNING = "warning"
    INFO = "info"
    SUCCESS = "success"


class EventType(str, Enum):
    TELEMETRY_FRAME = "telemetry_frame"
    STATE_CHANGE = "state_change"
    MANEUVER_STATUS = "maneuver_status"
    MISSION_PHASE = "mission_phase"
    ALERT = "alert"
    STAGING = "staging"
    SOI_CHANGE = "soi_change"
    LOG_ENTRY = "log_entry"
