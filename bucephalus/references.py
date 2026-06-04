"""Published-ish anchors for sanity checks. Not your final BOM."""

from dataclasses import dataclass


@dataclass(frozen=True)
class EnginePreset:
    name: str
    mass_kg: float
    """Length along crank axis (becomes vehicle lateral width when transverse)."""
    length_mm: float
    """Width across cylinder banks (becomes vehicle fore-aft depth when transverse)."""
    width_mm: float
    height_mm: float
    displacement_l: float
    cylinders: int
    note: str


# Huracán / R8 5.2 FSI family — order-of-magnitude service manual / press kit sizes.
LAMBORGHINI_52_V10 = EnginePreset(
    name="lamborghini_5.2_v10_reference",
    mass_kg=235.0,
    length_mm=720.0,
    width_mm=640.0,
    height_mm=720.0,
    displacement_l=5.2,
    cylinders=10,
    note="LP610-4 class dry mass; envelope approximated from public teardown dimensions.",
)

# Truck V10 — included as a hard fail example for transverse sports packaging.
FORD_68_V10_TRUCK = EnginePreset(
    name="ford_6.8_v10_truck_reference",
    mass_kg=274.0,
    length_mm=691.0,
    width_mm=422.0,
    height_mm=748.0,
    displacement_l=6.8,
    cylinders=10,
    note="Modular V10; too tall/long for typical transverse mid-engine bay.",
)

PRESETS: dict[str, EnginePreset] = {
    p.name: p
    for p in (LAMBORGHINI_52_V10, FORD_68_V10_TRUCK)
}
