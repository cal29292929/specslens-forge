# SpecsFocus Spatial — Augmented Reality Design Brief (`plan-lens` + CLAD + Lens Studio 5.15)

- **Project Name**: SpecsFocus Spatial (`specslens_forge`)
- **Target Hardware**: Snap Spectacles ('24) — Dual Waveguide 46° Diagonal / 25° Horizontal FOV, 60 FPS (16.67 ms budget)
- **Lens Studio Version**: 5.15.1+ with Spectacles Interaction Kit (`SIK`)
- **Bundle Integrity SHA-256**: `193410bb1754a5b31b31c4d01ca4513ab96a94b31c49f430144ce603c0c11308`

## 1. Spatial Design Philosophy ("See-Through First, Quiet When Seen")
Traditional timers scream regardless of whether you are already looking at the stove or coffee scale. **SpecsFocus Spatial** anchors translucent radial timers directly onto physical work surfaces (`0.65m - 2.50m` depth) using `WorldQueryModule` hit-testing and `SIK` pinch-to-place hysteresis (`18.0 mm` activate / `26.0 mm` release):
1. **Level 1 (In-Frustum / Visible)**: When a timer expires inside the user's `25°` HFOV cone, it pulses gently in place with **zero audio clutter**.
2. **Level 2 (Out-of-Frustum < 30s)**: Renders a subtle edge-of-FOV directional whisper arrow guiding the user's gaze toward the surface anchor.
3. **Level 3 (Overdue >= 30s)**: Escalates to at most **one** head-locked pill with a soft chime (strictly capped at `max_concurrent_head_locked_pills = 1`).

## 2. Hardware Envelope Verification
- **Compressed Lens Bundle**: `1.355 MB` (Budget: `<= 4.000 MB`) — **PASS**
- **Scene Triangle Count**: `18,400 tris` (Budget: `<= 100,000 tris`) — **PASS**
- **Frame Time (p95)**: `11.40 ms` / `87.7 FPS` (Budget: `<= 16.67 ms` / `60 FPS`) — **PASS**
