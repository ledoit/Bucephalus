from dataclasses import dataclass

from bucephalus.hydrogen import estimate_range_km, storage_balance
from bucephalus.mass_budget import build_mass_budget
from bucephalus.models import VehicleSpec
from bucephalus.packaging import check_transverse_fit


@dataclass(frozen=True)
class GateResult:
    id: str
    passed: bool
    detail: str


@dataclass(frozen=True)
class FeasibilityReport:
    vehicle: str
    gates: list[GateResult]

    @property
    def passed(self) -> bool:
        return all(g.passed for g in self.gates)


def run_gates(spec: VehicleSpec) -> FeasibilityReport:
    fit = check_transverse_fit(spec.engine, spec.bay)
    storage = storage_balance(spec.storage)
    mass = build_mass_budget(spec)
    rng = estimate_range_km(
        storage.total_h2_kg,
        spec.ice_efficiency,
        spec.consumption_lge_100km,
    )

    gates = [
        GateResult(
            "transverse_bay_lateral",
            fit.lateral_ok,
            f"need {fit.lateral_need_mm:.0f} mm, bay {fit.bay.max_lateral_mm:.0f} mm",
        ),
        GateResult(
            "transverse_bay_fore_aft",
            fit.fore_aft_ok,
            f"need {fit.fore_aft_need_mm:.0f} mm, bay {fit.bay.max_fore_aft_mm:.0f} mm",
        ),
        GateResult(
            "transverse_bay_height",
            fit.height_ok,
            f"need {fit.height_need_mm:.0f} mm, bay {fit.bay.max_height_mm:.0f} mm",
        ),
        GateResult(
            "no_trunk_storage_volume",
            storage.packaging_ok,
            f"tanks {sum(t.geometric_l for t in storage.tanks):.1f} L in "
            f"{storage.declared_packaging_l:.1f} L packaging "
            f"(slack {storage.packaging_slack_l:.1f} L)",
        ),
        GateResult(
            "mass_budget_complete",
            mass.total_kg >= 0.92 * mass.target_kg,
            f"budget {mass.total_kg:.1f} kg covers >=92% of target {mass.target_kg:.1f} kg "
            "(add missing subsystems before trusting curb gate)",
        ),
        GateResult(
            "curb_mass_target",
            mass.delta_kg <= 0 and mass.total_kg >= 0.92 * mass.target_kg,
            f"budget {mass.total_kg:.1f} kg vs target {mass.target_kg:.1f} kg "
            f"(delta {mass.delta_kg:+.1f} kg)",
        ),
        GateResult(
            "range_target",
            rng.range_km >= spec.target_range_km,
            f"est. {rng.range_km:.0f} km vs target {spec.target_range_km:.0f} km "
            f"on {storage.total_h2_kg:.2f} kg H2",
        ),
    ]
    return FeasibilityReport(vehicle=spec.name, gates=gates)
