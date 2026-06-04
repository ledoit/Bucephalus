import argparse
import sys
from pathlib import Path

from bucephalus.gates import run_gates
from bucephalus.load_spec import load_vehicle_spec
from bucephalus.report import format_report
from bucephalus.scene import write_scene_json


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Bucephalus — transverse V10 H2 ICE packaging and feasibility gates",
    )
    parser.add_argument(
        "spec",
        type=Path,
        nargs="?",
        default=Path(__file__).resolve().parents[1] / "config" / "bucephalus_v0.yaml",
        help="Vehicle YAML spec (default: config/bucephalus_v0.yaml)",
    )
    parser.add_argument(
        "--export-scene",
        type=Path,
        metavar="PATH",
        help="Write tentative 3D block layout JSON for viewer/",
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="Reserved; markdown report is default",
    )
    args = parser.parse_args(argv)

    spec = load_vehicle_spec(args.spec)
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except (AttributeError, OSError):
        pass

    if args.export_scene:
        write_scene_json(spec, args.export_scene)
        print(f"Wrote scene JSON → {args.export_scene.resolve()}", file=sys.stderr)

    print(format_report(spec))
    return 0 if run_gates(spec).passed else 1


if __name__ == "__main__":
    sys.exit(main())
