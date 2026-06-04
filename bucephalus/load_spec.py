from pathlib import Path

import yaml

from bucephalus.models import (
    BaySpec,
    EngineSpec,
    MassLine,
    StorageLayout,
    TankSpec,
    VehicleSpec,
)


def _mass_lines(raw: list[dict]) -> list[MassLine]:
    return [
        MassLine(
            label=item["label"],
            mass_kg=float(item["mass_kg"]),
            cg_x_mm=float(item.get("cg_x_mm", 0)),
            cg_y_mm=float(item.get("cg_y_mm", 0)),
            cg_z_mm=float(item.get("cg_z_mm", 0)),
        )
        for item in raw
    ]


def _tanks(raw: list[dict]) -> list[TankSpec]:
    return [
        TankSpec(
            label=item["label"],
            volume_l=float(item["volume_l"]),
            pressure_bar=float(item.get("pressure_bar", 700)),
            fill_factor=float(item.get("fill_factor", 0.92)),
        )
        for item in raw
    ]


def load_vehicle_spec(path: Path) -> VehicleSpec:
    data = yaml.safe_load(path.read_text(encoding="utf-8"))
    eng = data["engine"]
    bay = data["bay"]
    st = data["storage"]
    return VehicleSpec(
        name=data["name"],
        wheelbase_mm=float(data["wheelbase_mm"]),
        track_front_mm=float(data["track_front_mm"]),
        track_rear_mm=float(data["track_rear_mm"]),
        target_curb_mass_kg=float(data["target_curb_mass_kg"]),
        target_range_km=float(data.get("target_range_km", 300)),
        ice_efficiency=float(data.get("ice_efficiency", 0.38)),
        consumption_lge_100km=float(data.get("consumption_lge_100km", 12)),
        engine=EngineSpec(
            preset=eng.get("preset"),
            mass_kg=eng.get("mass_kg"),
            length_mm=eng.get("length_mm"),
            width_mm=eng.get("width_mm"),
            height_mm=eng.get("height_mm"),
            displacement_l=eng.get("displacement_l"),
            cylinders=int(eng.get("cylinders", 10)),
            target_power_kw=eng.get("target_power_kw"),
        ),
        bay=BaySpec(
            lateral_clearance_mm=float(bay.get("lateral_clearance_mm", 40)),
            fore_aft_clearance_mm=float(bay.get("fore_aft_clearance_mm", 50)),
            vertical_clearance_mm=float(bay.get("vertical_clearance_mm", 30)),
            max_lateral_mm=float(bay["max_lateral_mm"]),
            max_fore_aft_mm=float(bay["max_fore_aft_mm"]),
            max_height_mm=float(bay["max_height_mm"]),
        ),
        storage=StorageLayout(
            tanks=_tanks(st.get("tanks", [])),
            tunnel_volume_l=float(st.get("tunnel_volume_l", 0)),
            underfloor_volume_l=float(st.get("underfloor_volume_l", 0)),
            seat_back_volume_l=float(st.get("seat_back_volume_l", 0)),
        ),
        mass_lines=_mass_lines(data.get("mass_lines", [])),
    )
