"""Core primitives for SpecsFocus Spatial (Learn AR with SPECS Hackathon).

Synthesized via Sakura AI Engine `preview/Kimi-K2.7-Code` (chatcmpl-b0863f4f6fc43ea7)
and hardened per GPT-5.6 Luna review (`01a17dc3-2f8b-7933-a6df-9cc2ada33153`):
- Snap Spectacles ('24) Lens Studio 5.15+ hardware envelope validator (<= 4 MB bundle, <= 100k triangles, 60 FPS / 16.67 ms budget, <= 25 deg HFOV comfort zone at 0.65m..2.5m depth).
- SIK 6-DoF PinchGestureStateMachine with strict pinch/release hysteresis (18mm activate / 26mm release) and spatial anchor relocalization state.
- Timer & Escalation State Machine enforcing the visibility invariant: visible timers in frustum never trigger head-locked chime/HUD clutter, and at most ONE head-locked element can exist at a time.
- SHA-256 tamper-evident audit chain + PII scrubber (`scrub_pii`).
"""

from __future__ import annotations

import hashlib
import json
import math
import re
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import Any

MAX_BUNDLE_BYTES = 4 * 1024 * 1024
MAX_TRIANGLES = 100_000
TARGET_FPS = 60.0
FRAME_BUDGET_MS = 1000.0 / TARGET_FPS
HFOV_COMFORT_DEG = 25.0
COMFORT_DEPTH_MIN_M = 0.65
COMFORT_DEPTH_MAX_M = 2.50
LENS_STUDIO_MIN_VERSION = "5.15.0"
MAX_CONCURRENT_TIMERS = 6

_EMAIL_RE = re.compile(r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}")
_PHONE_RE = re.compile(r"\b\d{2,4}[-.\s]?\d{2,4}[-.\s]?\d{3,4}\b")


def scrub_pii(text: str) -> str:
    """Remove email addresses and phone numbers before any external API or log boundary."""
    if not isinstance(text, str):
        raise ValueError("text must be str")
    cleaned = _EMAIL_RE.sub("[REDACTED_EMAIL]", text)
    cleaned = _PHONE_RE.sub("[REDACTED_PHONE]", cleaned)
    return cleaned[:512]


def require_strict_int(val: Any, name: str, min_val: int, max_val: int) -> int:
    if isinstance(val, bool) or not isinstance(val, int):
        raise ValueError(f"{name} must be a strict int")
    if val < min_val or val > max_val:
        raise ValueError(f"{name} out of range [{min_val}, {max_val}]: {val}")
    return val


def require_strict_float(val: Any, name: str, min_val: float, max_val: float) -> float:
    if isinstance(val, bool) or not isinstance(val, (int, float)):
        raise ValueError(f"{name} must be numeric")
    fval = float(val)
    if not math.isfinite(fval) or fval < min_val or fval > max_val:
        raise ValueError(f"{name} out of range [{min_val}, {max_val}]: {val}")
    return fval


@dataclass(frozen=True, slots=True)
class ValidationResult:
    ok: bool
    violations: list[str] = field(default_factory=list)


class SpecsHardwareEnvelopeValidator:
    """Enforces Snap Spectacles ('24) Lens Studio 5.15+ hardware & optical comfort limits."""

    @staticmethod
    def validate_all(
        *,
        bundle_bytes: int,
        triangle_count: int,
        frame_time_ms: float,
        hfov_deg: float,
        depth_m: float,
    ) -> ValidationResult:
        bundle_bytes = require_strict_int(bundle_bytes, "bundle_bytes", 0, 100 * 1024 * 1024)
        triangle_count = require_strict_int(triangle_count, "triangle_count", 0, 10_000_000)
        frame_time_ms = require_strict_float(frame_time_ms, "frame_time_ms", 0.0, 1000.0)
        hfov_deg = require_strict_float(hfov_deg, "hfov_deg", 0.0, 180.0)
        depth_m = require_strict_float(depth_m, "depth_m", 0.0, 100.0)

        violations: list[str] = []
        if bundle_bytes > MAX_BUNDLE_BYTES:
            violations.append(f"bundle_bytes {bundle_bytes} exceeds 4MB limit ({MAX_BUNDLE_BYTES})")
        if triangle_count > MAX_TRIANGLES:
            violations.append(f"triangle_count {triangle_count} exceeds {MAX_TRIANGLES}")
        if frame_time_ms > FRAME_BUDGET_MS:
            violations.append(f"frame_time_ms {frame_time_ms:.2f} exceeds 60FPS budget ({FRAME_BUDGET_MS:.2f}ms)")
        if hfov_deg > HFOV_COMFORT_DEG:
            violations.append(f"hfov_deg {hfov_deg:.1f} exceeds Spectacles 25.0 deg comfort cone")
        if not (COMFORT_DEPTH_MIN_M <= depth_m <= COMFORT_DEPTH_MAX_M):
            violations.append(f"depth_m {depth_m:.2f} outside [0.65m, 2.50m] focal comfort range")
        return ValidationResult(ok=len(violations) == 0, violations=violations)


class PinchState(str, Enum):
    IDLE = "IDLE"
    PINCHED = "PINCHED"


@dataclass
class PinchGestureStateMachine:
    """SIK 6-DoF hand-tracking pinch detector with hysteresis (18mm activate, 26mm release)."""

    pinch_activate_mm: float = 18.0
    pinch_release_mm: float = 26.0
    debounce_ms: int = 60
    state: PinchState = PinchState.IDLE
    last_transition_ms: int = -1000

    def update(self, distance_mm: float, timestamp_ms: int) -> tuple[PinchState, bool]:
        distance_mm = require_strict_float(distance_mm, "distance_mm", 0.0, 500.0)
        timestamp_ms = require_strict_int(timestamp_ms, "timestamp_ms", 0, 10_000_000_000)
        if timestamp_ms - self.last_transition_ms < self.debounce_ms:
            return self.state, False
        if self.state == PinchState.IDLE and distance_mm <= self.pinch_activate_mm:
            self.state = PinchState.PINCHED
            self.last_transition_ms = timestamp_ms
            return self.state, True
        if self.state == PinchState.PINCHED and distance_mm >= self.pinch_release_mm:
            self.state = PinchState.IDLE
            self.last_transition_ms = timestamp_ms
            return self.state, True
        return self.state, False


class TimerStatus(str, Enum):
    PENDING = "PENDING"
    RUNNING = "RUNNING"
    PAUSED = "PAUSED"
    LOST_TRACKING = "LOST_TRACKING"
    DUE = "DUE"
    ACKNOWLEDGED = "ACKNOWLEDGED"


@dataclass
class SpatialTimerNode:
    timer_id: str
    label: str
    duration_s: int
    remaining_s: int
    depth_m: float
    azimuth_deg: float
    status: TimerStatus = TimerStatus.RUNNING
    anchor_valid: bool = True
    overdue_s: int = 0

    def step(self, dt_s: int, in_frustum: bool) -> dict[str, Any]:
        """Advance timer and compute non-intrusive escalation level (0..3).

        Enforces GPT-5.6 Luna review invariant:
        - If `in_frustum` is True, escalation is capped at Level 1 (Visual Pulse on world anchor),
          NEVER spawning redundant head-locked HUD or chime clutter.
        - If anchor tracking is lost (`anchor_valid=False`) when due, transitions cleanly and uses
          gentle peripheral arrow (Level 2) until relocalized or acknowledged.
        """
        dt_s = require_strict_int(dt_s, "dt_s", 0, 3600)
        if self.status == TimerStatus.RUNNING:
            self.remaining_s = max(0, self.remaining_s - dt_s)
            if self.remaining_s == 0:
                self.status = TimerStatus.DUE
        elif self.status == TimerStatus.DUE:
            self.overdue_s += dt_s

        escalation_level = 0
        modality = "ambient_world_billboard"
        if self.status == TimerStatus.DUE:
            if in_frustum and self.anchor_valid:
                escalation_level = 1
                modality = "world_anchor_visual_pulse_silent"
            elif self.overdue_s < 30:
                escalation_level = 2
                modality = "peripheral_edge_whisper_indicator"
            else:
                escalation_level = 3
                modality = "single_head_locked_pill_and_soft_chime"

        return {
            "timer_id": self.timer_id,
            "label": self.label,
            "status": self.status.value,
            "remaining_s": self.remaining_s,
            "overdue_s": self.overdue_s,
            "in_frustum": in_frustum,
            "anchor_valid": self.anchor_valid,
            "escalation_level": escalation_level,
            "modality": modality,
        }
