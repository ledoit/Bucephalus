from bucephalus.models import BaySpec, EngineSpec
from bucephalus.packaging import check_transverse_fit


def test_lambo_v10_fits_generous_bay():
    fit = check_transverse_fit(
        EngineSpec(preset="lamborghini_5.2_v10_reference"),
        BaySpec(max_lateral_mm=800, max_fore_aft_mm=720, max_height_mm=780),
    )
    assert fit.fits


def test_truck_v10_fails_tight_mid_engine_bay():
    fit = check_transverse_fit(
        EngineSpec(preset="ford_6.8_v10_truck_reference"),
        BaySpec(max_lateral_mm=760, max_fore_aft_mm=680, max_height_mm=720),
    )
    assert not fit.fits
