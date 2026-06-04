from dataclasses import dataclass

from bucephalus.models import BaySpec, EngineSpec
from bucephalus.references import PRESETS


@dataclass(frozen=True)
class EngineEnvelope:
    mass_kg: float
    length_mm: float
    width_mm: float
    height_mm: float
    source: str


def resolve_engine(spec: EngineSpec) -> EngineEnvelope:
    if spec.preset:
        preset = PRESETS.get(spec.preset)
        if preset is None:
            raise ValueError(f"unknown engine preset: {spec.preset}")
        return EngineEnvelope(
            mass_kg=spec.mass_kg or preset.mass_kg,
            length_mm=spec.length_mm or preset.length_mm,
            width_mm=spec.width_mm or preset.width_mm,
            height_mm=spec.height_mm or preset.height_mm,
            source=preset.name,
        )
    required = (spec.mass_kg, spec.length_mm, spec.width_mm, spec.height_mm)
    if any(v is None for v in required):
        raise ValueError("custom engine requires mass_kg, length_mm, width_mm, height_mm")
    return EngineEnvelope(
        mass_kg=spec.mass_kg,  # type: ignore[arg-type]
        length_mm=spec.length_mm,  # type: ignore[arg-type]
        width_mm=spec.width_mm,  # type: ignore[arg-type]
        height_mm=spec.height_mm,  # type: ignore[arg-type]
        source="custom",
    )


@dataclass(frozen=True)
class TransverseFit:
    """Transverse: crank length spans vehicle lateral (Y), bank width is fore-aft (X)."""
    engine: EngineEnvelope
    bay: BaySpec
    lateral_need_mm: float
    fore_aft_need_mm: float
    height_need_mm: float
    lateral_ok: bool
    fore_aft_ok: bool
    height_ok: bool

    @property
    def fits(self) -> bool:
        return self.lateral_ok and self.fore_aft_ok and self.height_ok


def check_transverse_fit(engine: EngineSpec, bay: BaySpec) -> TransverseFit:
    env = resolve_engine(engine)
    lateral_need = env.length_mm + bay.lateral_clearance_mm
    fore_aft_need = env.width_mm + bay.fore_aft_clearance_mm
    height_need = env.height_mm + bay.vertical_clearance_mm
    return TransverseFit(
        engine=env,
        bay=bay,
        lateral_need_mm=lateral_need,
        fore_aft_need_mm=fore_aft_need,
        height_need_mm=height_need,
        lateral_ok=lateral_need <= bay.max_lateral_mm,
        fore_aft_ok=fore_aft_need <= bay.max_fore_aft_mm,
        height_ok=height_need <= bay.max_height_mm,
    )
