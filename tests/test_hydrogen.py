from bucephalus.hydrogen import estimate_range_km, tank_h2_mass_kg
from bucephalus.models import StorageLayout, TankSpec
from bucephalus.hydrogen import storage_balance


def test_tank_mass_scales_with_volume():
    small = tank_h2_mass_kg(TankSpec("a", volume_l=20))
    large = tank_h2_mass_kg(TankSpec("b", volume_l=40))
    assert large.mass_kg > small.mass_kg * 1.9


def test_storage_slack():
    layout = StorageLayout(
        tanks=[TankSpec("t", volume_l=30)],
        tunnel_volume_l=35,
    )
    bal = storage_balance(layout)
    assert bal.packaging_ok
    assert bal.packaging_slack_l == 5.0


def test_range_scales_with_h2_mass():
    r = estimate_range_km(4.0, 0.38, 12.0)
    assert 40 < r.range_km < 55
