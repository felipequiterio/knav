from pydantic import BaseModel

from knav.models.enums import ManeuverState, ManeuverType
from knav.models.orbit import OrbitState


class BurnPlan(BaseModel):
    delta_v: float  # m/s
    burn_time: float  # seconds
    ut: float  # burn start UT
    prograde: float = 0.0
    normal: float = 0.0
    radial: float = 0.0


class ManeuverPlan(BaseModel):
    type: ManeuverType
    delta_v_total: float
    burns: list[BurnPlan]
    transfer_time: float | None = None
    phase_angle_required: float | None = None
    phase_angle_current: float | None = None
    wait_time: float | None = None
    resulting_orbit: OrbitState | None = None


class ManeuverStatus(BaseModel):
    type: ManeuverType
    state: ManeuverState
    phase: str
    progress_percent: float = 0.0
    remaining_dv: float = 0.0
    elapsed_time: float = 0.0
    burns_completed: int = 0
    burns_total: int = 0


class ManeuverResult(BaseModel):
    type: ManeuverType
    success: bool
    planned_dv: float
    actual_dv: float
    accuracy_percent: float
    final_orbit: OrbitState | None = None
    elapsed_time: float = 0.0
    message: str = ""
