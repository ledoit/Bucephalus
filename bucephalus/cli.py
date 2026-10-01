import argparse
import sys
from pathlib import Path

from bucephalus.gates import run_gates
from bucephalus.load_spec import load_vehicle_spec
from bucephalus.report import format_report


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
    print(format_report(spec))
    return 0 if run_gates(spec).passed else 1


if __name__ == "__main__":
    sys.exit(main())
