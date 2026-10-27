"""Unit tests for SpecsFocus Spatial (`specslens_forge`)."""

from __future__ import annotations

from pathlib import Path
import pytest

from specslens_forge.core import (
    PinchGestureStateMachine,
    PinchState,
    SpatialTimerNode,
    SpecsHardwareEnvelopeValidator,
    scrub_pii,
)
from specslens_forge.engine import generate_lens_bundle_and_simulation, write_design_brief_and_project
from specslens_forge.mcp_server import handle_jsonrpc_request


def test_hardware_envelope_validator_and_strict_bool() -> None:
    ok_res = SpecsHardwareEnvelopeValidator.validate_all(
        bundle_bytes=1_500_000,
        triangle_count=20_000,
        frame_time_ms=12.0,
        hfov_deg=22.0,
        depth_m=1.2,
    )
    assert ok_res.ok is True
    assert ok_res.violations == []

    bad_res = SpecsHardwareEnvelopeValidator.validate_all(
        bundle_bytes=5_000_000,
        triangle_count=120_000,
        frame_time_ms=20.0,
        hfov_deg=35.0,
        depth_m=0.3,
    )
    assert bad_res.ok is False
    assert len(bad_res.violations) == 5

    with pytest.raises(ValueError, match="strict int"):
        SpecsHardwareEnvelopeValidator.validate_all(
            bundle_bytes=True,  # type: ignore[arg-type]
            triangle_count=100,
            frame_time_ms=10.0,
            hfov_deg=20.0,
            depth_m=1.0,
        )


def test_pinch_hysteresis_and_debounce() -> None:
    fsm = PinchGestureStateMachine()
    st, ch = fsm.update(16.0, 100)
    assert st == PinchState.PINCHED and ch is True
    # Within debounce window (60ms) -> ignored
    st, ch = fsm.update(30.0, 120)
    assert st == PinchState.PINCHED and ch is False
    # Intermediate hysteresis zone (22mm < 26mm release) -> stays pinched
    st, ch = fsm.update(22.0, 200)
    assert st == PinchState.PINCHED and ch is False
    # Release above 26mm after debounce -> IDLE
    st, ch = fsm.update(28.0, 300)
    assert st == PinchState.IDLE and ch is True


def test_visible_timer_never_triggers_head_locked_clutter() -> None:
    node = SpatialTimerNode("t1", "Kettle", 10, 10, depth_m=1.2, azimuth_deg=0.0)
    st1 = node.step(10, in_frustum=True)
    assert st1["status"] == "DUE"
    assert st1["escalation_level"] == 1
    assert st1["modality"] == "world_anchor_visual_pulse_silent"
    # Even after 60s overdue, if the user is looking directly at the timer, keep it Level 1 silent pulse
    st2 = node.step(60, in_frustum=True)
    assert st2["escalation_level"] == 1
    # When user looks away, escalates to Level 3
    st3 = node.step(10, in_frustum=False)
    assert st3["escalation_level"] == 3


def test_pii_scrubber_and_simulation_bundle(tmp_path: Path) -> None:
    assert "[REDACTED_EMAIL]" in scrub_pii("Contact alice@example.com or 090-1234-5678")
    paths = write_design_brief_and_project(tmp_path)
    assert Path(paths["design_brief"]).exists()
    assert Path(paths["esproj"]).exists()
    sim = generate_lens_bundle_and_simulation()
    assert sim["invariants"]["head_locked_violations"] == 0
    assert sim["invariants"]["sik_pinch_hysteresis_verified"] is True


def test_mcp_server_jsonrpc() -> None:
    res = handle_jsonrpc_request(
        {
            "jsonrpc": "2.0",
            "id": 1,
            "method": "tools/call",
            "params": {
                "name": "validate_spectacles_envelope",
                "arguments": {
                    "bundle_bytes": 1000000,
                    "triangle_count": 10000,
                    "frame_time_ms": 12.0,
                    "hfov_deg": 20.0,
                    "depth_m": 1.2,
                },
            },
        }
    )
    assert res is not None and res["result"]["isError"] is False
