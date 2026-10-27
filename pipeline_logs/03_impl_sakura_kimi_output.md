 ```python
# specslens_forge/core.py
"""
Self-contained Python 3.11 standard-library module for the
Learn AR with SPECS Hackathon (06-learn-specs).

Provides:

* ``SpecsHardwareEnvelopeValidator`` – Snap Spectacles ('24) / Lens Studio 5.15+
  hardware budgets.
* ``PinchGestureStateMachine`` – SIK 6-DoF pinch/release hysteresis with
  persistent spatial anchors.
* ``DesignBriefGenerator`` – validated ``devpost/design-brief.md`` and
  ``.esproj`` manifest with SHA-256 integrity digests.
"""

from __future__ import annotations

import hashlib
import json
import time
import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum, auto
from pathlib import Path
from typing import Any

__all__ = [
    "Anchor",
    "DesignBriefError",
    "DesignBriefGenerator",
    "PinchGestureStateMachine",
    "PinchState",
    "SpecsHardwareEnvelopeValidator",
    "ValidationResult",
]

# --------------------------------------------------------------------------- #
# Hardware envelope constants – Snap Spectacles ('24) / Lens Studio 5.15+
# --------------------------------------------------------------------------- #
MAX_BUNDLE_BYTES = 4 * 1024 * 1024
MAX_TRIANGLES = 100_000
TARGET_FPS = 60.0
FRAME_BUDGET_MS = 1000.0 / TARGET_FPS  # ~16.6667 ms
HFOV_COMFORT_DEG = 25.0
COMFORT_DEPTH_MIN_M = 0.65
COMFORT_DEPTH_MAX_M = 2.5
LENS_STUDIO_MIN_VERSION = "5.15.0"


# --------------------------------------------------------------------------- #
# Validation primitives
# --------------------------------------------------------------------------- #
@dataclass(frozen=True, slots=True)
class ValidationResult:
    """Result of a hardware-envelope validation pass."""

    ok: bool
    violations: list[str] = field(default_factory=list)


class SpecsHardwareEnvelopeValidator:
    """
    Enforce Snap Spectacles ('24) Lens Studio 5.15+ performance budgets:

    * compressed bundle <= 4 MB
    * mesh <= 100,000 triangles
    * frame budget <= 60 FPS / ~16.67 ms
    * HFOV comfort zone <= 25° between 0.65 m and 2.5 m depth
    """

    @staticmethod
    def validate_bundle_size(size: int | Path) -> ValidationResult:
        """Validate a compressed bundle size."""
        if isinstance(size, Path):
            if not size.exists():
                return ValidationResult(False, [f"Bundle path not found: {size}"])
            size = size.stat().st_size

        if size <= MAX_BUNDLE_BYTES:
            return ValidationResult(True)
        return ValidationResult(
            False,
            [
                f"Bundle size {size} bytes ({size / 1024 / 1024:.2f} MB) "
                f"exceeds {MAX_BUNDLE_BYTES} bytes (4 MB)"
            ],
        )

    @staticmethod
    def validate_mesh(triangle_count: int) -> ValidationResult:
        """Validate a mesh triangle budget."""
        if triangle_count <= MAX_TRIANGLES:
            return ValidationResult(True)
        return ValidationResult(
            False,
            [f"Triangle count {triangle_count:,} exceeds {MAX_TRIANGLES:,}"],
        )

    @staticmethod
    def validate_frame_budget(
        fps: float | None = None,
        frame_time_ms: float | None = None,
    ) -> ValidationResult:
        """Validate the 60 FPS / 16.67 ms frame budget."""
        violations: list[str] = []

        if fps is not None and fps < TARGET_FPS:
            violations.append(f"FPS {fps} below target {TARGET_FPS}")

        if frame_time_ms is not None and frame_time_ms > FRAME_BUDGET_MS:
            violations.append(
                f"Frame time {frame_time_ms:.3f} ms exceeds budget "
                f"{FRAME_BUDGET_MS:.3f} ms"
            )

        if fps is None and frame_time_ms is None:
            violations.append("Either fps or frame_time_ms must be provided")

        return ValidationResult(not violations, violations)

    @staticmethod
    def validate_hfov(hfov_deg: float, depth_m: float) -> ValidationResult:
        """Validate the HFOV comfort zone at a given depth."""
        violations: list[str] = []

        if not (COMFORT_DEPTH_MIN_M <= depth_m <= COMFORT_DEPTH_MAX_M):
            violations.append(
                f"Depth {depth_m} m outside comfort range "
                f"[{COMFORT_DEPTH_MIN_M}, {COMFORT_DEPTH_MAX_M}] m"
            )

        if hfov_deg > HFOV_COMFORT_DEG:
            violations.append(
                f"HFOV {hfov_deg}° exceeds comfort zone {HFOV_COMFORT_DEG}°"
            )

        return ValidationResult(not violations, violations)

    def validate_project(self, project: dict[str, Any]) -> ValidationResult:
        """
        Validate an aggregate project specification dictionary.

        Recognised keys:
        ``bundle_size_bytes``, ``bundle_path``, ``total_triangles``,
        ``target_fps``, ``frame_time_ms``, ``hfov_deg``, ``comfort_depth_m``.
        """
        results: list[ValidationResult] = []

        bundle_size = project.get("bundle_size_bytes")
        bundle_path = project.get("bundle_path")
        if bundle_size is not None:
            results.append(self.validate_bundle_size(bundle_size))
        elif bundle_path is not None:
            results.append(self.validate_bundle_size(Path(bundle_path)))

        triangles = project.get("total_triangles")
        if triangles is not None:
            results.append(self.validate_mesh(triangles))

        fps = project.get("target_fps")
        frame_time = project.get("frame_time_ms")
        if fps is not None or frame_time is not None:
            results.append(self.validate_frame_budget(fps, frame_time))

        hfov = project.get("hfov_deg")
        depth = project.get("comfort_depth_m")
        if hfov is not None and depth is not None:
            results.append(self.validate_hfov(hfov, depth))

        violations = [v for r in results for v in r.violations]
        return ValidationResult(not violations, violations)


# --------------------------------------------------------------------------- #
# SIK pinch gesture state machine
# --------------------------------------------------------------------------- #
class PinchState(Enum):
    RELEASED = auto()
    PINCHED = auto()


@dataclass(slots=True)
class Anchor:
    """A persisted spatial anchor created during a pinch gesture."""

    id: str
    pose: dict[str, Any]
    created_at: float
    updated_at: float
    active: bool = True


class PinchGestureStateMachine:
    """
    SIK (Spectacles Interaction Kit) 6-DoF pinch/release state machine.

    Uses hysteresis with configurable activate/release thresholds and a
    time-based debounce. Spatial anchors created on pinch activation persist
    after release.
    """

    def __init__(
        self,
        pinch_activate_mm: float = 18.0,
        pinch_release_mm: float = 26.0,
        debounce_window_s: float = 0.05,
    ) -> None:
        if pinch_release_mm <= pinch_activate_mm:
            raise ValueError("release threshold must exceed activate threshold")

        self.pinch_activate_mm = pinch_activate_mm
        self.pinch_release_mm = pinch_release_mm
        self.debounce_window_s = debounce_window_s

        self.state = PinchState.RELEASED
        self._candidate_state: PinchState | None = None
        self._candidate_start: float | None = None
        self._anchors: list[Anchor] = []
        self._current_anchor: Anchor | None = None

    @property
    def anchors(self) -> list[Anchor]:
        """Return all persisted anchors (active and inactive)."""
        return list(self._anchors)

    @property
    def current_anchor(self) -> Anchor | None:
        """Return the anchor currently driving the active pinch, if any."""
        return self._current_anchor

    def reset(self) -> None:
        """Reset gesture state and clear all persisted anchors."""
        self.state = PinchState.RELEASED
        self._candidate_state = None
        self._candidate_start = None
        self._anchors.clear()
        self._current_anchor = None

    def update(
        self,
        distance_mm: float,
        timestamp: float | None = None,
        pose: dict[str, Any] | None = None,
    ) -> list[str]:
        """
        Feed a new hand-tracking sample into the state machine.

        Parameters
        ----------
        distance_mm:
            Distance between thumb and index fingertips in millimetres.
        timestamp:
            Monotonic time in seconds. Defaults to ``time.monotonic()``.
        pose:
            Optional 6-DoF pose dict to attach to the anchor.

        Returns
        -------
        list[str]
            Events emitted this frame, e.g. ``"pinch_activated"``,
            ``"anchor_created"``, ``"pinch_released"``, ``"anchor_persisted"``.
        """
        if timestamp is None:
            timestamp = time.monotonic()

        events: list[str] = []

        if self.state is PinchState.RELEASED:
            events.extend(self._evaluate_release_to_pinch(distance_mm, timestamp, pose))
        else:
            events.extend(self._evaluate_pinch_to_release(distance_mm, timestamp))

        return events

    def _evaluate_release_to_pinch(
        self,
        distance_mm: float,
        timestamp: float,
        pose: dict[str, Any] | None,
    ) -> list[str]:
        events: list[str] = []

        if distance_mm <= self.pinch_activate_mm:
            if self._candidate_state is PinchState.PINCHED:
                if timestamp - self._candidate_start >= self.debounce_window_s:
                    self.state = PinchState.PINCHED
                    anchor = Anchor(
                        id=str(uuid.uuid4()),
                        pose=pose or {},
                        created_at=timestamp,
                        updated_at=timestamp,
                        active=True,
                    )
                    self._anchors.append(anchor)
                    self._current_anchor = anchor
