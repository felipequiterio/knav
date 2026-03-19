from pydantic import BaseModel

from knav.models.enums import ManeuverType, MissionStatus


class MissionPhase(BaseModel):
    name: str
    maneuver_type: ManeuverType
    maneuver_params: dict = {}
    status: MissionStatus = MissionStatus.PLANNING
    result_message: str = ""


class Mission(BaseModel):
    id: str
    name: str
    status: MissionStatus = MissionStatus.PLANNING
    phases: list[MissionPhase] = []
    current_phase_index: int = 0
    created_ut: float | None = None
    started_ut: float | None = None
    completed_ut: float | None = None


class MissionTemplate(BaseModel):
    name: str
    description: str
    phases: list[MissionPhase]
