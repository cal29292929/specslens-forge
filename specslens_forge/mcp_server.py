"""JSON-RPC 2.0 MCP Server for SpecsFocus Spatial (`specslens_forge`)."""

from __future__ import annotations

import json
import sys
from typing import Any

from .core import PinchGestureStateMachine, SpecsHardwareEnvelopeValidator
from .engine import generate_lens_bundle_and_simulation

TOOLS: list[dict[str, Any]] = [
    {
        "name": "validate_spectacles_envelope",
        "description": "Validate Snap Spectacles ('24) bundle size, triangles, frame time, HFOV, and focal depth.",
        "inputSchema": {
            "type": "object",
            "required": ["bundle_bytes", "triangle_count", "frame_time_ms", "hfov_deg", "depth_m"],
            "properties": {
                "bundle_bytes": {"type": "integer"},
                "triangle_count": {"type": "integer"},
                "frame_time_ms": {"type": "number"},
                "hfov_deg": {"type": "number"},
                "depth_m": {"type": "number"},
            },
        },
    },
    {
        "name": "simulate_spatial_timers",
        "description": "Run a deterministic SpecsFocus Spatial timer & SIK pinch hysteresis simulation.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "workflow_title": {"type": "string"},
                "seed": {"type": "integer"},
            },
        },
    },
]


def handle_jsonrpc_request(req: dict[str, Any]) -> dict[str, Any] | None:
    if not isinstance(req, dict) or req.get("jsonrpc") != "2.0":
        return {"jsonrpc": "2.0", "id": None, "error": {"code": -32600, "message": "Invalid Request"}}
    req_id = req.get("id")
    method = req.get("method")
    params = req.get("params") if isinstance(req.get("params"), dict) else {}
    if method == "notifications/initialized":
        return None
    if method == "initialize":
        return {
            "jsonrpc": "2.0",
            "id": req_id,
            "result": {
                "protocolVersion": "2024-11-05",
                "capabilities": {"tools": {}},
                "serverInfo": {"name": "specslens-forge-mcp", "version": "1.0.0"},
            },
        }
    if method == "tools/list":
        return {"jsonrpc": "2.0", "id": req_id, "result": {"tools": TOOLS}}
    if method == "tools/call":
        name = params.get("name")
        args = params.get("arguments")
        if not isinstance(args, dict):
            return {"jsonrpc": "2.0", "id": req_id, "error": {"code": -32602, "message": "arguments must be an object"}}
        try:
            if name == "validate_spectacles_envelope":
                res = SpecsHardwareEnvelopeValidator.validate_all(
                    bundle_bytes=args.get("bundle_bytes"),
                    triangle_count=args.get("triangle_count"),
                    frame_time_ms=args.get("frame_time_ms"),
                    hfov_deg=args.get("hfov_deg"),
                    depth_m=args.get("depth_m"),
                )
                payload = {"ok": res.ok, "violations": res.violations}
            elif name == "simulate_spatial_timers":
                payload = generate_lens_bundle_and_simulation(
                    workflow_title=args.get("workflow_title", "Pour-Over Station"),
                    seed=args.get("seed", 42),
                )
            else:
                return {"jsonrpc": "2.0", "id": req_id, "error": {"code": -32602, "message": f"Unknown tool: {name}"}}
            return {
                "jsonrpc": "2.0",
                "id": req_id,
                "result": {"content": [{"type": "text", "text": json.dumps(payload)}], "isError": False},
            }
        except (ValueError, TypeError):
            return {"jsonrpc": "2.0", "id": req_id, "error": {"code": -32602, "message": "Invalid Tool Parameters"}}
    return {"jsonrpc": "2.0", "id": req_id, "error": {"code": -32601, "message": "Method not found"}}
