from pathlib import Path

from bucephalus.gates import run_gates
from bucephalus.load_spec import load_vehicle_spec


def test_default_spec_loads():
    path = Path(__file__).resolve().parents[1] / "config" / "bucephalus_v0.yaml"
    spec = load_vehicle_spec(path)
    report = run_gates(spec)
    assert report.vehicle == "bucephalus_v0"
    assert len(report.gates) == 7
