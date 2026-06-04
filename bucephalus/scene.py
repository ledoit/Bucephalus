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
    # Mid-rear: bay sits aft of cabin center, above tunnel.
    bay_x = -0.14 * wb
    bay_z = wheel_r + spec.bay.max_height_mm * 0.42
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


def _v10_detail_primitives(
    env_source: str,
    env_w: float,
    env_l: float,
    env_h: float,
    center: tuple[float, float, float],
    fits: bool,
) -> list[BoxPrimitive]:
    """Crankcase + two bank slivers + valve cover on top of transverse block."""
    cx, cy, cz = center
    base = "#e8a838" if fits else "#e85d5d"
    bank_w = env_w * 0.38
    bank_l = env_l * 0.88
    bank_h = env_h * 0.62
    offset_y = env_l * 0.22
    vc_h = env_h * 0.22
    return [
        BoxPrimitive(
            "engine_crankcase",
            f"Crankcase ({env_source})",
            "powertrain",
            (cx, cy, cz - env_h * 0.08),
            (env_w * 0.92, env_l * 0.55, env_h * 0.55),
            base,
            opacity=0.5,
        ),
        BoxPrimitive(
            "engine_bank_front",
            "Cylinder bank (fore)",
            "powertrain",
            (cx, cy + offset_y, cz + env_h * 0.06),
            (bank_w, bank_l, bank_h),
            base,
            opacity=0.78,
        ),
        BoxPrimitive(
            "engine_bank_rear",
            "Cylinder bank (aft)",
            "powertrain",
            (cx, cy - offset_y, cz + env_h * 0.06),
            (bank_w, bank_l, bank_h),
            base,
            opacity=0.78,
        ),
        BoxPrimitive(
            "engine_valve_cover",
            "Valve cover / intake plenum",
            "powertrain",
            (cx, cy, cz + env_h * 0.38),
            (env_w * 0.7, env_l * 0.45, vc_h),
            "#d4a017",
            opacity=0.85,
        ),
    ]


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

    boxes: list[BoxPrimitive] = [
        BoxPrimitive(
            "body_shell",
            "Body shell (from wheelbase × 1.72)",
            "body",
            (0.0, 0.0, lay.body_height_mm / 2 + lay.wheel_radius_mm),
            (lay.body_length_mm, lay.body_width_mm, lay.body_height_mm),
            "#4a5568",
            opacity=0.2,
        ),
        BoxPrimitive(
            "bay_envelope",
            "Engine bay IML (YAML)",
            "bay",
            (ex, ey, ez + spec.bay.max_height_mm / 2),
            (spec.bay.max_fore_aft_mm, spec.bay.max_lateral_mm, spec.bay.max_height_mm),
            "#5b8def",
            opacity=0.15,
            wireframe=True,
        ),
        BoxPrimitive(
            "engine_envelope",
            f"Engine envelope ({env.source})",
            "powertrain",
            (ex, ey, ez + env.height_mm / 2),
            (env.width_mm, env.length_mm, env.height_mm),
            engine_color,
            opacity=0.2,
            wireframe=True,
        ),
        BoxPrimitive(
            "engine_required",
            "Engine + clearances",
            "powertrain",
            (ex, ey, ez + fit.height_need_mm / 2),
            (fit.fore_aft_need_mm, fit.lateral_need_mm, fit.height_need_mm),
            engine_color,
            opacity=0.1,
            wireframe=True,
        ),
    ]
    boxes.extend(
        _v10_detail_primitives(
            env.source, env.width_mm, env.length_mm, env.height_mm,
            (ex, ey, ez + env.height_mm / 2), fit.fits,
        )
    )

    cylinders: list[CylinderPrimitive] = []

    if spec.storage.tunnel_volume_l > 0:
        r, length = _volume_l_to_cylinder_mm(spec.storage.tunnel_volume_l, 4.5)
        length = min(length, lay.body_length_mm * 0.42)
        cylinders.append(
            CylinderPrimitive(
                "packaging_tunnel",
                f"Tunnel void ({spec.storage.tunnel_volume_l:.0f} L)",
                "storage_void",
                lay.tunnel_center,
                r * 1.05,
                length,
                "x",
                "#3ecf8e",
                opacity=0.12,
                wireframe=True,
            )
        )

    if spec.storage.underfloor_volume_l > 0:
        r, length = _volume_l_to_cylinder_mm(spec.storage.underfloor_volume_l, 3.2)
        cylinders.append(
            CylinderPrimitive(
                "packaging_underfloor",
                f"Underfloor void ({spec.storage.underfloor_volume_l:.0f} L)",
                "storage_void",
                lay.underfloor_center,
                r * 1.1,
                length * 0.85,
                "x",
                "#3ecf8e",
                opacity=0.12,
                wireframe=True,
            )
        )

    if spec.storage.seat_back_volume_l > 0:
        sz = _volume_l_to_box_mm(spec.storage.seat_back_volume_l, (0.45, 1.3, 1.1))
        boxes.append(
            BoxPrimitive(
                "packaging_seat_back",
                f"Seat-back void ({spec.storage.seat_back_volume_l:.0f} L)",
                "storage_void",
                lay.seat_back_center,
                sz,
                "#3ecf8e",
                opacity=0.12,
                wireframe=True,
            )
        )

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
                r,
                length,
                axis,  # type: ignore[arg-type]
                "#2dd4bf",
                opacity=0.7,
            )
        )

    markers = [
        Marker("cg_total", "Mass CG (budget)", (mass.cg_x_mm, mass.cg_y_mm, mass.cg_z_mm), "#fbbf24"),
        Marker("rear_axle", "Rear axle", (-half_wb, 0.0, lay.wheel_radius_mm), "#8b95a8", 28.0),
        Marker("front_axle", "Front axle", (half_wb, 0.0, lay.wheel_radius_mm), "#8b95a8", 28.0),
    ]

    primitives: list[dict[str, Any]] = [asdict(p) for p in boxes] + [asdict(p) for p in cylinders]

    return {
        "version": 2,
        "vehicle": spec.name,
        "units": "mm",
        "axes": {"x": "fore_aft", "y": "lateral", "z": "up"},
        "note": (
            "Layout positions scale from wheelbase/track/volumes in YAML. "
            "V10 banks are schematic. Drop in glTF when CAD exists."
        ),
        "layout_source": "derived_from_spec",
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
