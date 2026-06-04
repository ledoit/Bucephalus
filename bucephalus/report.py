from bucephalus.gates import FeasibilityReport, run_gates
from bucephalus.hydrogen import estimate_range_km, storage_balance
from bucephalus.mass_budget import build_mass_budget
from bucephalus.models import VehicleSpec
from bucephalus.packaging import check_transverse_fit


def format_report(spec: VehicleSpec) -> str:
    fit = check_transverse_fit(spec.engine, spec.bay)
    storage = storage_balance(spec.storage)
    mass = build_mass_budget(spec)
    rng = estimate_range_km(
        storage.total_h2_kg,
        spec.ice_efficiency,
        spec.consumption_lge_100km,
    )
    feasibility = run_gates(spec)

    lines = [
        f"# Bucephalus feasibility — {spec.name}",
        "",
        "## Transverse V10 packaging",
        f"- Engine source: `{fit.engine.source}`",
        f"- Envelope (L×W×H): {fit.engine.length_mm:.0f} × {fit.engine.width_mm:.0f} × {fit.engine.height_mm:.0f} mm",
        f"- Bay limits (lat × fore-aft × H): {fit.bay.max_lateral_mm:.0f} × {fit.bay.max_fore_aft_mm:.0f} × {fit.bay.max_height_mm:.0f} mm",
        f"- Lateral: {'PASS' if fit.lateral_ok else 'FAIL'} ({fit.lateral_need_mm:.0f} mm required)",
        f"- Fore-aft: {'PASS' if fit.fore_aft_ok else 'FAIL'} ({fit.fore_aft_need_mm:.0f} mm required)",
        f"- Height: {'PASS' if fit.height_ok else 'FAIL'} ({fit.height_need_mm:.0f} mm required)",
        "",
        "## H2 storage (no trunk / no frunk)",
    ]
    for t in storage.tanks:
        lines.append(
            f"- {t.tank.label}: {t.geometric_l:.1f} L geom -> {t.mass_kg:.2f} kg @ {t.tank.pressure_bar:.0f} bar"
        )
    lines.extend(
        [
            f"- Packaging envelope: {storage.declared_packaging_l:.1f} L "
            f"(tunnel + underfloor + seat-back)",
            f"- Slack: {storage.packaging_slack_l:.1f} L",
            f"- Total H2: {storage.total_h2_kg:.2f} kg",
            "",
            "## Mass budget",
            f"- Target curb: {mass.target_kg:.1f} kg",
            f"- Sum (incl. engine): {mass.total_kg:.1f} kg (delta {mass.delta_kg:+.1f} kg)",
            f"- CG estimate (x,y,z): {mass.cg_x_mm:.0f}, {mass.cg_y_mm:.0f}, {mass.cg_z_mm:.0f} mm",
            "",
            "## Range (LHV model, not homologation)",
            f"- ICE efficiency on H2 LHV: {spec.ice_efficiency:.0%}",
            f"- Assumed {spec.consumption_lge_100km:.1f} Lge/100 km",
            f"- Estimated range: {rng.range_km:.0f} km (target {spec.target_range_km:.0f} km)",
            "",
            "## Gates",
        ]
    )
    for g in feasibility.gates:
        status = "PASS" if g.passed else "FAIL"
        lines.append(f"- [{status}] `{g.id}` — {g.detail}")
    lines.append("")
    lines.append(
        f"**Overall:** {'GO' if feasibility.passed else 'NO-GO'} "
        "(fix failing gates before metal or tanks)"
    )
    return "\n".join(lines)
