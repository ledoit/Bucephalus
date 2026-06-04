from dataclasses import dataclass, field


@dataclass
class EngineSpec:
    preset: str | None = None
    mass_kg: float | None = None
    length_mm: float | None = None
    width_mm: float | None = None
    height_mm: float | None = None
    displacement_l: float | None = None
    cylinders: int = 10
    target_power_kw: float | None = None


@dataclass
class BaySpec:
    """Engine bay usable envelope (inner mold line), transverse mount."""
    lateral_clearance_mm: float = 40.0
    fore_aft_clearance_mm: float = 50.0
    vertical_clearance_mm: float = 30.0
    max_lateral_mm: float = 780.0
    max_fore_aft_mm: float = 700.0
    max_height_mm: float = 750.0


@dataclass
class TankSpec:
    label: str
    volume_l: float
    pressure_bar: float = 700.0
    """Usable fraction of geometric volume (valves, boss, liner)."""
    fill_factor: float = 0.92


@dataclass
class StorageLayout:
    """Where H2 lives when trunk and frunk are zero."""
    tanks: list[TankSpec] = field(default_factory=list)
    tunnel_volume_l: float = 0.0
    underfloor_volume_l: float = 0.0
    seat_back_volume_l: float = 0.0


@dataclass
class MassLine:
    label: str
    mass_kg: float
    cg_x_mm: float = 0.0
    cg_y_mm: float = 0.0
    cg_z_mm: float = 0.0


@dataclass
class VehicleSpec:
    name: str
    wheelbase_mm: float
    track_front_mm: float
    track_rear_mm: float
    target_curb_mass_kg: float
    engine: EngineSpec
    bay: BaySpec
    storage: StorageLayout
    mass_lines: list[MassLine] = field(default_factory=list)
    target_range_km: float = 300.0
    """Assumed ICE brake thermal efficiency on H2 LHV."""
    ice_efficiency: float = 0.38
    """Liters gasoline-equivalent per 100 km for sanity (derived, not input)."""
    consumption_lge_100km: float = 12.0
