# SpecsFocus Spatial (`specslens_forge`) — Learn AR with SPECS Hackathon

**SpecsFocus Spatial** is an augmented reality spatial timer and surface-anchored task assistant designed for **Snap Spectacles ('24)** and **Lens Studio 5.15+ (Spectacles Interaction Kit / SIK)**, accompanied by a deterministic Python 3.11 verification and bundle-generation toolkit.

- **Public GitHub Repository (Target)**: `https://github.com/cal29292929/specslens-forge`
- **Author**: Kazutoshi Hayashi (`cal29292929 <cal29292929@users.noreply.github.com>`)
- **License**: MIT

## Multi-Model Pipeline Provenance
1. **Stage 1 — Architecture Design (`claude-opus-5-5`)**: [`DESIGN_OPUS55.md`](DESIGN_OPUS55.md) (Session `294629e6-ccc5-424f-a219-daa29285c2b9`)
2. **Stage 2 — Adversarial Architecture Review (`gpt-6-luna`)**: [`REVIEW_LUNA56.md`](REVIEW_LUNA56.md) (Codex Session `01a17dc3-2f8b-7933-a6df-9cc2ada33153`)
3. **Stage 3 — Core Implementation (`preview/Kimi-K2.7-Code` @ Sakura AI Engine)**: `pipeline_logs/03_impl_sakura_kimi.json` (`chatcmpl-b0863f4f6fc43ea7`) + [`specslens_forge/`](specslens_forge/)
4. **Stage 4 — Post-Implementation Code Review (`gpt-6-luna`)**: [`CODE_REVIEW_LUNA56.md`](CODE_REVIEW_LUNA56.md)

## Quickstart
```bash
PYTHONPATH=. pytest -v
PYTHONPATH=. python3 -m specslens_forge.cli simulate --base-dir .
```
