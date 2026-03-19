"""Scene detection and capability gating."""

from __future__ import annotations

from typing import TYPE_CHECKING

import structlog

from knav.krpc_interface.errors import SceneNotSupportedError
from knav.models.enums import Capability, Scene

if TYPE_CHECKING:
    import krpc

log = structlog.get_logger()

# Maps KRPC GameScene enum member names to our Scene enum.
_KRPC_SCENE_MAP: dict[str, Scene] = {
    "flight": Scene.FLIGHT,
    "space_center": Scene.SPACE_CENTER,
    "vehicle_assembly_building": Scene.VAB,
    "space_plane_hangar": Scene.SPH,
    "tracking_station": Scene.TRACKING,
}

# What each scene is capable of.
_SCENE_CAPABILITIES: dict[Scene, frozenset[Capability]] = {
    Scene.FLIGHT: frozenset(Capability),  # all capabilities
    Scene.SPACE_CENTER: frozenset({Capability.WARP}),
    Scene.VAB: frozenset(),
    Scene.SPH: frozenset(),
    Scene.TRACKING: frozenset({Capability.WARP}),
    Scene.UNKNOWN: frozenset(),
}


class SceneManager:
    """Detects the current KSP scene and gates operations by capability."""

    def __init__(self) -> None:
        self._current_scene: Scene = Scene.UNKNOWN

    @property
    def current_scene(self) -> Scene:
        return self._current_scene

    def detect_scene(self, conn: krpc.Client) -> Scene:
        """Read the current game scene from KRPC and update internal state."""
        raw = conn.krpc.current_game_scene
        scene = _KRPC_SCENE_MAP.get(raw.name, Scene.UNKNOWN)
        if scene != self._current_scene:
            log.info(
                "scene.changed",
                previous=self._current_scene.value,
                current=scene.value,
            )
            self._current_scene = scene
        return scene

    def can(self, capability: Capability) -> bool:
        """Return True if the current scene supports *capability*."""
        return capability in _SCENE_CAPABILITIES.get(self._current_scene, frozenset())

    def require(self, capability: Capability) -> None:
        """Raise ``SceneNotSupportedError`` if *capability* is not available."""
        if not self.can(capability):
            raise SceneNotSupportedError(
                f"Scene {self._current_scene.value!r} does not support {capability.value!r}"
            )
