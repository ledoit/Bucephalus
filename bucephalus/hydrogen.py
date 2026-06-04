"""H2 storage and range — ideal-gas order of magnitude, not crash or permeation certified."""

from dataclasses import dataclass

from bucephalus.models import StorageLayout, TankSpec

# Lower heating value, MJ/kg (ISO 14687 context).
H2_LHV_MJ_PER_KG = 120.0
# NIST-ish: H2 density at 700 bar, 15 °C ~ 39.4 kg/m³ → ~39.4 g/L.
H2_DENSITY_700BAR_15C_KG_PER_L = 0.0394
# Gasoline LHV ~ 44 MJ/kg, density ~ 0.74 kg/L → ~32.6 MJ/L.
GASOLINE_MJ_PER_L = 32.6


@dataclass(frozen=True)
class TankCapacity:
    tank: TankSpec
    geometric_l: float
    effective_l: float
    mass_kg: float


@dataclass(frozen=True)
class StorageBalance:
    tanks: list[TankCapacity]
    total_h2_kg: float
    declared_packaging_l: float
    packaging_slack_l: float
    packaging_ok: bool


def tank_h2_mass_kg(tank: TankSpec) -> TankCapacity:
    effective_l = tank.volume_l * tank.fill_factor
    mass = effective_l * H2_DENSITY_700BAR_15C_KG_PER_L
    return TankCapacity(
        tank=tank,
        geometric_l=tank.volume_l,
        effective_l=effective_l,
        mass_kg=mass,
    )


def storage_balance(layout: StorageLayout) -> StorageBalance:
    tanks = [tank_h2_mass_kg(t) for t in layout.tanks]
    total_kg = sum(t.mass_kg for t in tanks)
    tank_geom_l = sum(t.geometric_l for t in tanks)
    declared = (
        layout.tunnel_volume_l
        + layout.underfloor_volume_l
        + layout.seat_back_volume_l
    )
    slack = declared - tank_geom_l
    return StorageBalance(
        tanks=tanks,
        total_h2_kg=total_kg,
        declared_packaging_l=declared,
        packaging_slack_l=slack,
        packaging_ok=slack >= 0 and tank_geom_l > 0,
    )


@dataclass(frozen=True)
class RangeEstimate:
    h2_kg: float
    ice_efficiency: float
    consumption_lge_100km: float
    range_km: float
    energy_mj: float


def estimate_range_km(
    h2_kg: float,
    ice_efficiency: float,
    consumption_lge_100km: float,
) -> RangeEstimate:
    energy_mj = h2_kg * H2_LHV_MJ_PER_KG * ice_efficiency
    mj_per_100km = consumption_lge_100km * GASOLINE_MJ_PER_L
    if mj_per_100km <= 0:
        raise ValueError("consumption_lge_100km must be positive")
    range_km = (energy_mj / mj_per_100km) * 100.0
    return RangeEstimate(
        h2_kg=h2_kg,
        ice_efficiency=ice_efficiency,
        consumption_lge_100km=consumption_lge_100km,
        range_km=range_km,
        energy_mj=energy_mj,
    )
