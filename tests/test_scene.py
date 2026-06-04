import json
from pathlib import Path

from bucephalus.load_spec import load_vehicle_spec
from bucephalus.scene import build_scene, scene_to_json


def test_build_scene_has_engine_and_tanks():
    path = Path(__file__).resolve().parents[1] / "config" / "bucephalus_v0.yaml"
    spec = load_vehicle_spec(path)
    scene = build_scene(spec)

    assert scene["vehicle"] == "bucephalus_v0"
    assert scene["version"] == 3
    assert scene["layout_source"] == "derived_from_spec"
    assert scene["vehicle_shell"]["url"] == "/models/sports_shell.glb"
    ids = {p["id"] for p in scene["primitives"]}
    assert "engine_block" in ids
    assert "engine_crankcase" not in ids
    assert "bay_envelope" in ids
    assert any(p["kind"] == "cylinder" and p["group"] == "tanks" for p in scene["primitives"])
    assert scene["summary"]["engine_source"] == "lamborghini_5.2_v10_reference"
    assert len(scene["gates"]) >= 6


def test_scene_json_roundtrip():
    path = Path(__file__).resolve().parents[1] / "config" / "bucephalus_v0.yaml"
    spec = load_vehicle_spec(path)
    data = json.loads(scene_to_json(spec))
    assert data["markers"][0]["id"] == "cg_total"
