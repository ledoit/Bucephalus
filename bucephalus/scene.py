"""Tentative block layout for packaging review — not CAD, not crash-certified."""

from __future__ import annotations

import json
from dataclasses import asdict, dataclass
from typing import Any

from bucephalus.gates import run_gates
from bucephalus.hydrogen import storage_balance
from bucephalus.mass_budget import build_mass_budget
from bucephalus.models import VehicleSpec
from bucephalus.packaging import check_transverse_fit, resolve_engine

# Scene origin: vehicle center on ground (x fore-aft, y lateral, z up).
_BODY_LENGTH_MM = 4180.0
_BODY_HEIGHT_MM = 1180.0
_WHEEL_RADIUS_MM = 330.0
_ENGINE_BAY_X_MM = -180.0
_ENGINE_BAY_Z_MM = 520.0


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


@dataclass(frozen=True)
class Marker:
    id: str
    label: str
    position_mm: tuple[float, float, float]
    color: str
    radius_mm: float = 45.0


def _volume_l_to_box_mm(volume_l: float, aspect: tuple[float, float, float]) -> tuple[float, float, float]:
    """Scale a unit aspect box so volume matches liters (1 L = 1e6 mm³)."""
    ax, ay, az = aspect
    norm = (ax * ay * az) ** (1 / 3)
    if norm <= 0:
        raise ValueError("aspect ratios must be positive")
    scale = (volume_l * 1e6) ** (1 / 3) / norm
    return ax * scale, ay * scale, az * scale


def build_scene(spec: VehicleSpec) -> dict[str, Any]:
    fit = check_transverse_fit(spec.engine, spec.bay)
    env = fit.engine
    storage = storage_balance(spec.storage)
    mass = build_mass_budget(spec)
    gates = run_gates(spec)

    half_wb = spec.wheelbase_mm / 2
    body_w = max(spec.track_front_mm, spec.track_rear_mm) + 120.0

    primitives: list[BoxPrimitive] = [
        BoxPrimitive(
            "body_shell",
            "Body shell (tentative)",
            "body",
            (0.0, 0.0, _BODY_HEIGHT_MM / 2 + _WHEEL_RADIUS_MM),
            (_BODY_LENGTH_MM, body_w, _BODY_HEIGHT_MM),
            "#4a5568",
            opacity=0.22,
        ),
        BoxPrimitive(
            "bay_envelope",
            "Engine bay IML limit",
            "bay",
            (_ENGINE_BAY_X_MM, 0.0, _ENGINE_BAY_Z_MM + spec.bay.max_height_mm / 2),
            (spec.bay.max_fore_aft_mm, spec.bay.max_lateral_mm, spec.bay.max_height_mm),
            "#5b8def",
            opacity=0.18,
            wireframe=True,
        ),
        BoxPrimitive(
            "engine_block",
            f"Engine ({env.source})",
            "powertrain",
            (
                _ENGINE_BAY_X_MM,
                0.0,
                _ENGINE_BAY_Z_MM + env.height_mm / 2,
            ),
            # Transverse: crank along Y, banks along X, height Z.
            (env.width_mm, env.length_mm, env.height_mm),
            "#e8a838" if fit.fits else "#e85d5d",
            opacity=0.72,
        ),
        BoxPrimitive(
            "engine_required",
            "Engine + clearances",
            "powertrain",
            (
                _ENGINE_BAY_X_MM,
                0.0,
                _ENGINE_BAY_Z_MM + fit.height_need_mm / 2,
            ),
            (fit.fore_aft_need_mm, fit.lateral_need_mm, fit.height_need_mm),
            "#e8a838",
            opacity=0.12,
            wireframe=True,
        ),
    ]

    # Packaging voids (declared envelope, not filled tanks).
    tunnel_center = (-420.0, 0.0, 180.0)
    underfloor_center = (320.0, 0.0, 95.0)
    seat_back_center = (680.0, 0.0, 520.0)

    if spec.storage.tunnel_volume_l > 0:
        sz = _volume_l_to_box_mm(spec.storage.tunnel_volume_l, (3.2, 1.0, 0.55))
        primitives.append(
            BoxPrimitive(
                "packaging_tunnel",
                f"Tunnel packaging ({spec.storage.tunnel_volume_l:.0f} L)",
                "storage_void",
                tunnel_center,
                sz,
                "#3ecf8e",
                opacity=0.14,
                wireframe=True,
            )
        )
    if spec.storage.underfloor_volume_l > 0:
        sz = _volume_l_to_box_mm(spec.storage.underfloor_volume_l, (2.4, 1.6, 0.35))
        primitives.append(
            BoxPrimitive(
                "packaging_underfloor",
                f"Underfloor packaging ({spec.storage.underfloor_volume_l:.0f} L)",
                "storage_void",
                underfloor_center,
                sz,
                "#3ecf8e",
                opacity=0.14,
                wireframe=True,
            )
        )
    if spec.storage.seat_back_volume_l > 0:
        sz = _volume_l_to_box_mm(spec.storage.seat_back_volume_l, (0.5, 1.4, 1.2))
        primitives.append(
            BoxPrimitive(
                "packaging_seat_back",
                f"Seat-back packaging ({spec.storage.seat_back_volume_l:.0f} L)",
                "storage_void",
                seat_back_center,
                sz,
                "#3ecf8e",
                opacity=0.14,
                wireframe=True,
            )
        )

    for i, cap in enumerate(storage.tanks):
        aspect = (2.8, 0.9, 0.5) if "tunnel" in cap.tank.label else (2.2, 1.2, 0.4)
        sz = _volume_l_to_box_mm(cap.geometric_l, aspect)
        if "tunnel" in cap.tank.label:
            center = tunnel_center
        elif "underfloor" in cap.tank.label:
            center = underfloor_center
        else:
            center = seat_back_center
        primitives.append(
            BoxPrimitive(
                f"tank_{i}",
                f"{cap.tank.label} ({cap.geometric_l:.0f} L → {cap.mass_kg:.1f} kg H₂)",
                "tanks",
                center,
                sz,
                "#2dd4bf",
                opacity=0.65,
            )
        )

    markers = [
        Marker("cg_total", "Mass CG (budget)", (mass.cg_x_mm, mass.cg_y_mm, mass.cg_z_mm), "#fbbf24"),
        Marker("rear_axle", "Rear axle", (-half_wb, 0.0, _WHEEL_RADIUS_MM), "#8b95a8", 28.0),
        Marker("front_axle", "Front axle", (half_wb, 0.0, _WHEEL_RADIUS_MM), "#8b95a8", 28.0),
    ]

    return {
        "version": 1,
        "vehicle": spec.name,
        "units": "mm",
        "axes": {"x": "fore_aft", "y": "lateral", "z": "up"},
        "note": "Tentative block model for packaging review. Replace with CAD/glTF when measured.",
        "wheelbase_mm": spec.wheelbase_mm,
        "track_front_mm": spec.track_front_mm,
        "track_rear_mm": spec.track_rear_mm,
        "primitives": [asdict(p) for p in primitives],
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
