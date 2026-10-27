"""CLI entrypoint for SpecsFocus Spatial (`specslens_forge`)."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from .engine import generate_lens_bundle_and_simulation, write_design_brief_and_project


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="specslens-forge")
    sub = parser.add_subparsers(dest="cmd", required=True)
    p_sim = sub.add_parser("simulate")
    p_sim.add_argument("--base-dir", default=".")
    args = parser.parse_args(argv)
    if args.cmd == "simulate":
        paths = write_design_brief_and_project(Path(args.base_dir))
        sim = generate_lens_bundle_and_simulation()
        print(json.dumps({"paths": paths, "hardware_envelope": sim["hardware_envelope"], "invariants": sim["invariants"]}, indent=2))
        return 0
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
