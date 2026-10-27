# Devpost Submission Draft — Learn AR with SPECS (`06-learn-specs`)

- **Devpost URL**: https://learn-ar-with-specs.devpost.com/
- **Submission Deadline (JST)**: `2026-11-10T07:00:00+09:00`
- **Project Name**: SpecsFocus Spatial: Gaze-Aware See-Through AR Task & Timer Assistant
- **Elevator Pitch**: Snap Spectacles (Lens Studio 5.15+ / Spectacles Interaction Kit) see-through optical AR companion with additive luminance validation, hysteresis pinch state machine, and peripheral clutter guards.
- **Target GitHub Repository URL**: `https://github.com/cal29292929/specslens-forge`
- **Target GitHub Release URL**: `https://github.com/cal29292929/specslens-forge/releases/tag/v1.0.0`
- **Demo Video**: `/workspace/hackathons/06-learn-specs/submission_assets/demo_video.mp4` (1920x1080, 150s, H.264/AAC)
- **Unit Test Suite**: `5 passed`

## Built With Tags
- `snap-spectacles`
- `lens-studio`
- `spectacles-interaction-kit`
- `typescript`
- `model-context-protocol`
- `python`

## Try It Out URLs
- https://github.com/cal29292929/specslens-forge
- https://github.com/cal29292929/specslens-forge/releases/tag/v1.0.0

## About the Project (Copy-Paste Ready for Devpost)

## Inspiration
See-through optical waveguide glasses (Snap Spectacles, 46° diagonal FOV) behave fundamentally differently from video-passthrough headsets: pure black (`#000000`) renders completely transparent, and central-reticle overlays cause dangerous visual accommodation rivalry during hands-busy tasks like pour-over brewing or electronics soldering.

## What it does
**SpecsFocus Spatial** (`specslens_forge` + `lens_project/SpecsFocusSpatial.esproj`) provides a gaze-aware multi-step spatial timer and checklist assistant:
1. **Additive Waveguide Palette Validator**: Rejects low-luminance dark fills (`Y < 0.35`) and enforces high-contrast cyan/amber/mint additive strokes.
2. **FOV Clutter & Central Cone Guard**: Rejects anchors within `8.0°` of center gaze unless user dwell >= `600 ms`, keeping total FOV occupancy `<= 15.0%`.
3. **Hysteresis Pinch State Machine**: Prevents accidental timer triggers using `18 mm` enter / `26 mm` exit thresholds, `120 ms` hold, and `250 ms` cooldown.

## Verification & Testing
- **Unit Tests**: `5 passed` (`pytest -q`)
- **Design Brief**: `devpost/design-brief.md` + `lens_project/SpecsFocusController.ts`
- **Demo Video**: `submission_assets/demo_video.mp4` (1920x1080, 150s, H.264/AAC)


## Multi-Model Pipeline Provenance & Custom Questions
```json
{
  "opus55_session_id": "294629e6-ccc5-424f-a219-daa29285c2b9",
  "luna56_review_session_id": "01a17dc3-2f8b-7933-a6df-9cc2ada33153",
  "luna56_codereview_session_id": "01a17dd2-3e3a-7411-96d9-11b73f658c98",
  "sakura_completion_id": "chatcmpl-b0863f4f6fc43ea7"
}
```

## Screenshots (1920x1080 PNG)
- `/workspace/hackathons/06-learn-specs/submission_assets/00_thumbnail.png`
- `/workspace/hackathons/06-learn-specs/submission_assets/01_hardware_envelope.png`
- `/workspace/hackathons/06-learn-specs/submission_assets/02_sik_pinch_hysteresis.png`
- `/workspace/hackathons/06-learn-specs/submission_assets/03_gaze_aware_escalation.png`
- `/workspace/hackathons/06-learn-specs/submission_assets/04_design_brief_and_esproj.png`
- `/workspace/hackathons/06-learn-specs/submission_assets/05_multi_model_review.png`
- `/workspace/hackathons/06-learn-specs/submission_assets/06_tests_and_quickstart.png`
