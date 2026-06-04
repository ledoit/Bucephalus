from dataclasses import dataclass

from bucephalus.models import MassLine, VehicleSpec
from bucephalus.packaging import resolve_engine


@dataclass(frozen=True)
class MassBudget:
    lines: list[MassLine]
    engine_mass_kg: float
    total_kg: float
    target_kg: float
    delta_kg: float
    cg_x_mm: float
    cg_y_mm: float
    cg_z_mm: float


def build_mass_budget(spec: VehicleSpec) -> MassBudget:
    engine = resolve_engine(spec.engine)
    lines = list(spec.mass_lines)
    engine_line = MassLine("powertrain_engine", engine.mass_kg)
    all_lines = lines + [engine_line]
    total = sum(l.mass_kg for l in all_lines)
    if total <= 0:
        raise ValueError("mass budget is empty")
    cg_x = sum(l.mass_kg * l.cg_x_mm for l in all_lines) / total
    cg_y = sum(l.mass_kg * l.cg_y_mm for l in all_lines) / total
    cg_z = sum(l.mass_kg * l.cg_z_mm for l in all_lines) / total
    return MassBudget(
        lines=all_lines,
        engine_mass_kg=engine.mass_kg,
        total_kg=total,
        target_kg=spec.target_curb_mass_kg,
        delta_kg=total - spec.target_curb_mass_kg,
        cg_x_mm=cg_x,
        cg_y_mm=cg_y,
        cg_z_mm=cg_z,
    )
