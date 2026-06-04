"""Tentative layout from VehicleSpec — derived positions, not CAD."""

from __future__ import annotations

import json
import math
from dataclasses import asdict, dataclass
from typing import Any, Literal

from bucephalus.gates import run_gates
from bucephalus.hydrogen import storage_balance
from bucephalus.mass_budget import build_mass_budget
from bucephalus.models import VehicleSpec
from bucephalus.packaging import check_transverse_fit, resolve_engine

Axis = Literal["x", "y", "z"]


@dataclass(frozen=True)
class VehicleLayout:
    """Positions derived from wheelbase / track / packaging volumes."""
    body_length_mm: float
    body_width_mm: float
    body_height_mm: float
    wheel_radius_mm: float
    engine_bay_center: tuple[float, float, float]
    tunnel_center: tuple[float, float, float]
    underfloor_center: tuple[float, float, float]
    seat_back_center: tuple[float, float, float]


@dataclass(frozen=True)
class BoxPrimitive:
    id: str
    label: str
    group: str
    center_mm: tuple[float, float, float]
    size_mm: tuple[float, float, float]
    color: str
    opacity: float = 0.55
    wireframe: bool = False
    kind: Literal["box"] = "box"


@dataclass(frozen=True)
class CylinderPrimitive:
    id: str
    label: str
    group: str
    center_mm: tuple[float, float, float]
    radius_mm: float
    length_mm: float
    axis: Axis
    color: str
    opacity: float = 0.65
    wireframe: bool = False
    kind: Literal["cylinder"] = "cylinder"


@dataclass(frozen=True)
class Marker:
    id: str
    label: str
    position_mm: tuple[float, float, float]
    color: str
    radius_mm: float = 45.0


def layout_from_spec(spec: VehicleSpec) -> VehicleLayout:
    wb = spec.wheelbase_mm
    track = max(spec.track_front_mm, spec.track_rear_mm)
    wheel_r = max(280.0, wb * 0.133)
    body_len = wb * 1.72
    body_h = max(1050.0, wb * 0.46)
    bay_x = -0.12 * body_len
    bay_z = wheel_r + 220.0
    return VehicleLayout(
        body_length_mm=body_len,
        body_width_mm=track + 100.0,
        body_height_mm=body_h,
        wheel_radius_mm=wheel_r,
        engine_bay_center=(bay_x, 0.0, bay_z),
        tunnel_center=(-0.22 * wb, 0.0, wheel_r * 0.55),
        underfloor_center=(0.12 * wb, 0.0, wheel_r * 0.32),
        seat_back_center=(0.38 * wb, 0.0, wheel_r + body_h * 0.38),
    )


def _volume_l_to_box_mm(volume_l: float, aspect: tuple[float, float, float]) -> tuple[float, float, float]:
    ax, ay, az = aspect
    norm = (ax * ay * az) ** (1 / 3)
    scale = (volume_l * 1e6) ** (1 / 3) / norm
    return ax * scale, ay * scale, az * scale


def _volume_l_to_cylinder_mm(
    volume_l: float,
    height_over_diameter: float,
) -> tuple[float, float]:
    """Return (radius_mm, length_mm) for cylinder volume along its length axis."""
    vol = volume_l * 1e6
    # V = π r² h, h = (h/d) · 2r
    ratio = max(height_over_diameter, 0.5)
    r = (vol / (2 * math.pi * ratio)) ** (1 / 3)
    length = ratio * 2 * r
    return r, length


def build_scene(spec: VehicleSpec) -> dict[str, Any]:
    fit = check_transverse_fit(spec.engine, spec.bay)
    env = fit.engine
    storage = storage_balance(spec.storage)
    mass = build_mass_budget(spec)
    gates = run_gates(spec)
    lay = layout_from_spec(spec)
    ex, ey, ez = lay.engine_bay_center
    half_wb = spec.wheelbase_mm / 2
    engine_color = "#e8a838" if fit.fits else "#e85d5d"

    vehicle_shell = {
        "url": "/models/sports_shell.glb",
        "name": "Sports coupe reference shell (458-class)",
        "license": "three.js examples — packaging reference only",
        "target_length_mm": lay.body_length_mm,
        "offset_mm": [0, 0, 0],
        "opacity": 0.9,
        "replace_hint": "Upload your CAD glB in the viewer or set url to /models/custom_shell.glb",
    }

    boxes: list[BoxPrimitive] = [
        BoxPrimitive(
            "bay_envelope",
            "Engine bay IML (YAML)",
            "bay",
            (ex, ey, ez + spec.bay.max_height_mm / 2),
            (spec.bay.max_fore_aft_mm, spec.bay.max_lateral_mm, spec.bay.max_height_mm),
            "#5b8def",
            opacity=0.35,
            wireframe=True,
        ),
        BoxPrimitive(
            "engine_block",
            f"V10 + clearance ({env.source})",
            "powertrain",
            (ex, ey, ez + fit.height_need_mm / 2),
            (fit.fore_aft_need_mm, fit.lateral_need_mm, fit.height_need_mm),
            engine_color,
            opacity=0.25,
            wireframe=True,
        ),
    ]

    cylinders: list[CylinderPrimitive] = []

    for i, cap in enumerate(storage.tanks):
        label = cap.tank.label
        if "tunnel" in label:
            center, axis, aspect = lay.tunnel_center, "x", 5.0
        elif "underfloor" in label:
            center, axis, aspect = lay.underfloor_center, "x", 3.5
        else:
            center, axis, aspect = lay.seat_back_center, "z", 2.0
        r, length = _volume_l_to_cylinder_mm(cap.geometric_l, aspect)
        cylinders.append(
            CylinderPrimitive(
                f"tank_{i}",
                f"{label} ({cap.geometric_l:.0f} L → {cap.mass_kg:.1f} kg H₂)",
                "tanks",
                center,
                r * 0.85,
                length * 0.9,
                axis,  # type: ignore[arg-type]
                "#2dd4bf",
                opacity=0.45,
                wireframe=True,
            )
        )

    markers = [
        Marker("cg_total", "Mass CG", (mass.cg_x_mm, mass.cg_y_mm, mass.cg_z_mm), "#fbbf24", 22.0),
        Marker("rear_axle", "Rear axle", (-half_wb, 0.0, lay.wheel_radius_mm), "#8b95a8", 16.0),
        Marker("front_axle", "Front axle", (half_wb, 0.0, lay.wheel_radius_mm), "#8b95a8", 16.0),
    ]

    primitives: list[dict[str, Any]] = [asdict(p) for p in boxes] + [asdict(p) for p in cylinders]

    return {
        "version": 3,
        "vehicle": spec.name,
        "units": "mm",
        "axes": {"x": "fore_aft", "y": "lateral", "z": "up"},
        "overlay_mode": "minimal",
        "note": (
            "Default view: car shell only. Toggle packaging layers to see bay, engine fit, and tanks. "
            "Overlays snap to the shell when loaded."
        ),
        "layout_source": "derived_from_spec",
        "vehicle_shell": vehicle_shell,
        "wheelbase_mm": spec.wheelbase_mm,
        "track_front_mm": spec.track_front_mm,
        "track_rear_mm": spec.track_rear_mm,
        "primitives": primitives,
        "markers": [asdict(m) for m in markers],
        "summary": {
            "engine_source": env.source,
            "transverse_fits": fit.fits,
            "h2_kg": round(storage.total_h2_kg, 2),
            "curb_kg": round(mass.total_kg, 1),
            "curb_delta_kg": round(mass.delta_kg, 1),
            "gates_passed": gates.passed,
        },
        "gates": [
            {"id": g.id, "passed": g.passed, "detail": g.detail} for g in gates.gates
        ],
    }


def scene_to_json(spec: VehicleSpec, *, indent: int = 2) -> str:
    return json.dumps(build_scene(spec), indent=indent)


def write_scene_json(spec: VehicleSpec, path: str) -> None:
    from pathlib import Path

    out = Path(path)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(scene_to_json(spec), encoding="utf-8")
