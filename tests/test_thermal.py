"""
tests/test_thermal.py
---------------------
Pytest tests for transformer.thermal (IEC 60076-7 thermal model).

All expected values are derived analytically from the IEC 60076-7 formulae
so that the tests verify correct implementation rather than empirical data.
"""

import math
import pytest

from transformer.thermal import ThermalModel


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture
def onan_model():
    """Standard ONAN model matching a typical 10 MVA distribution transformer."""
    return ThermalModel(
        rated_top_oil_rise_K       = 55.0,
        rated_winding_gradient_K   = 23.0,
        ratio_load_to_no_load_loss = 6.07,   # 85 kW / 14 kW ≈ 6.07
        cooling_mode               = "ONAN",
        hot_spot_factor            = 1.3,
    )


@pytest.fixture
def ofaf_model():
    """OFAF model with different thermal exponents."""
    return ThermalModel(
        rated_top_oil_rise_K       = 45.0,
        rated_winding_gradient_K   = 18.0,
        ratio_load_to_no_load_loss = 8.0,
        cooling_mode               = "OFAF",
        hot_spot_factor            = 1.1,
    )


# ---------------------------------------------------------------------------
# ThermalModel construction
# ---------------------------------------------------------------------------

class TestThermalModelInit:
    def test_defaults_populated(self, onan_model):
        assert onan_model.delta_theta_or == 55.0
        assert onan_model.delta_theta_hr == 23.0
        assert onan_model.cooling_mode   == "ONAN"
        assert onan_model.x == pytest.approx(0.8)
        assert onan_model.y == pytest.approx(1.6)
        assert onan_model.H == pytest.approx(1.3)

    def test_invalid_cooling_mode_raises(self):
        with pytest.raises(ValueError, match="cooling_mode"):
            ThermalModel(cooling_mode="XYZW")

    def test_ofaf_exponents(self, ofaf_model):
        assert ofaf_model.x == pytest.approx(1.0)
        assert ofaf_model.y == pytest.approx(1.6)


# ---------------------------------------------------------------------------
# top_oil_rise – IEC 60076-7 Eq. (2)
# ---------------------------------------------------------------------------

class TestTopOilRise:
    def test_rated_load_equals_rated_rise(self, onan_model):
        """At K=1 the top-oil rise must equal the rated rise (Δθ_or)."""
        rise = onan_model.top_oil_rise(load_factor=1.0)
        assert rise == pytest.approx(onan_model.delta_theta_or, rel=1e-6)

    def test_no_load_lower_than_rated(self, onan_model):
        """No-load top-oil rise must be below the rated rise."""
        rise_nl = onan_model.top_oil_rise(load_factor=0.0)
        # At K=0: Δθ = Δθ_or * (1/(1+R))^x
        expected = onan_model.delta_theta_or * (1 / (1 + onan_model.R)) ** onan_model.x
        assert rise_nl == pytest.approx(expected, rel=1e-6)

    def test_rise_increases_with_load(self, onan_model):
        """Top-oil rise must be monotonically increasing with load factor."""
        rises = [onan_model.top_oil_rise(k) for k in [0.0, 0.5, 1.0, 1.2]]
        assert rises == sorted(rises)

    def test_formula_explicit_k075(self, onan_model):
        """Verify against manually computed value at K=0.75."""
        k = 0.75
        R = onan_model.R
        x = onan_model.x
        expected = onan_model.delta_theta_or * ((1 + R * k**2) / (1 + R)) ** x
        assert onan_model.top_oil_rise(k) == pytest.approx(expected, rel=1e-9)

    def test_rise_does_not_depend_on_ambient(self, onan_model):
        """The rise (not absolute temperature) is independent of ambient."""
        rise_a = onan_model.top_oil_rise(1.0, ambient_C=10.0)
        rise_b = onan_model.top_oil_rise(1.0, ambient_C=40.0)
        assert rise_a == pytest.approx(rise_b, rel=1e-9)


# ---------------------------------------------------------------------------
# hot_spot_temp – IEC 60076-7 Eq. (3)
# ---------------------------------------------------------------------------

class TestHotSpotTemp:
    def test_increases_with_ambient(self, onan_model):
        """Higher ambient must give higher hot-spot temperature."""
        hs_cool = onan_model.hot_spot_temp(1.0, ambient_C=20.0)
        hs_hot  = onan_model.hot_spot_temp(1.0, ambient_C=40.0)
        assert hs_hot > hs_cool

    def test_ambient_offset_is_linear(self, onan_model):
        """A 10 K increase in ambient shifts hot-spot by exactly 10 K."""
        hs_a = onan_model.hot_spot_temp(0.8, ambient_C=25.0)
        hs_b = onan_model.hot_spot_temp(0.8, ambient_C=35.0)
        assert (hs_b - hs_a) == pytest.approx(10.0, abs=1e-9)

    def test_rated_load_20c_ambient(self, onan_model):
        """
        At K=1.0 and 20 °C ambient, hot-spot = 20 + Δθ_or + H·Δθ_hr.
        """
        expected = 20.0 + onan_model.delta_theta_or + onan_model.H * onan_model.delta_theta_hr
        assert onan_model.hot_spot_temp(1.0, 20.0) == pytest.approx(expected, rel=1e-6)

    def test_zero_load_returns_ambient_plus_no_load_gradients(self, onan_model):
        """At K=0 the winding gradient vanishes (K^y = 0)."""
        amb = 25.0
        rise_nl = onan_model.top_oil_rise(0.0, amb)
        expected = amb + rise_nl  # H·Δθ_hr·0^y = 0
        assert onan_model.hot_spot_temp(0.0, amb) == pytest.approx(expected, rel=1e-9)

    def test_increases_with_load(self, onan_model):
        """Hot-spot must increase monotonically with load."""
        temps = [onan_model.hot_spot_temp(k, 30.0) for k in [0.0, 0.5, 1.0, 1.3]]
        assert temps == sorted(temps)


# ---------------------------------------------------------------------------
# aging_acceleration_factor – IEC 60076-7 Annex B Eq. (B.1)
# ---------------------------------------------------------------------------

class TestAgingAccelerationFactor:
    def test_unity_at_reference_temperature(self, onan_model):
        """AAF must equal 1.0 at the 98 °C reference hot-spot."""
        aaf = onan_model.aging_acceleration_factor(98.0)
        assert aaf == pytest.approx(1.0, rel=1e-4)

    def test_greater_than_one_above_reference(self, onan_model):
        """Temperatures above 98 °C must give AAF > 1 (accelerated ageing)."""
        aaf = onan_model.aging_acceleration_factor(110.0)
        assert aaf > 1.0

    def test_less_than_one_below_reference(self, onan_model):
        """Temperatures below 98 °C must give AAF < 1 (retarded ageing)."""
        aaf = onan_model.aging_acceleration_factor(80.0)
        assert aaf < 1.0

    def test_exponential_formula(self, onan_model):
        """Verify against the raw Arrhenius formula."""
        B = 15_000.0
        theta_ref = 98.0 + 273.15
        theta_h   = 120.0 + 273.15
        expected = math.exp(B / theta_ref - B / theta_h)
        assert onan_model.aging_acceleration_factor(120.0) == pytest.approx(expected, rel=1e-9)

    def test_doubling_roughly_every_6K(self, onan_model):
        """
        Rule of thumb: AAF roughly doubles for each ~6 K rise near 98 °C.
        Not a hard IEC requirement but a useful sanity check.
        """
        aaf_98  = onan_model.aging_acceleration_factor(98.0)
        aaf_104 = onan_model.aging_acceleration_factor(104.0)
        ratio = aaf_104 / aaf_98
        assert 1.5 < ratio < 2.5, f"AAF ratio {ratio:.3f} outside expected 1.5–2.5 range"


# ---------------------------------------------------------------------------
# loss_of_life_pct_per_hour
# ---------------------------------------------------------------------------

class TestLossOfLife:
    def test_normal_life_at_reference(self, onan_model):
        """At 98 °C the loss of life per hour equals 1/200 000 × 100 %."""
        expected = (1.0 / 200_000.0) * 100.0
        assert onan_model.loss_of_life_pct_per_hour(98.0) == pytest.approx(expected, rel=1e-6)

    def test_higher_temperature_higher_lol(self, onan_model):
        """LOL/h must increase with temperature."""
        lol_98  = onan_model.loss_of_life_pct_per_hour(98.0)
        lol_120 = onan_model.loss_of_life_pct_per_hour(120.0)
        assert lol_120 > lol_98

    def test_total_life_at_reference_is_200k_hours(self, onan_model):
        """
        Integrating LOL/h at 98 °C over the full normal life must give 100%.
        """
        lol_per_h = onan_model.loss_of_life_pct_per_hour(98.0)
        total = lol_per_h * 200_000
        assert total == pytest.approx(100.0, rel=1e-6)

    def test_positive_for_any_temperature(self, onan_model):
        """LOL/h must always be positive."""
        for theta in [20.0, 60.0, 98.0, 140.0]:
            assert onan_model.loss_of_life_pct_per_hour(theta) > 0


# ---------------------------------------------------------------------------
# Cooling-mode variations
# ---------------------------------------------------------------------------

class TestCoolingModes:
    @pytest.mark.parametrize("mode,expected_x,expected_y", [
        ("ONAN", 0.8, 1.6),
        ("ONAF", 0.9, 1.6),
        ("OFAF", 1.0, 1.6),
        ("ODAF", 1.0, 2.0),
    ])
    def test_exponents_per_mode(self, mode, expected_x, expected_y):
        tm = ThermalModel(cooling_mode=mode)
        assert tm.x == pytest.approx(expected_x)
        assert tm.y == pytest.approx(expected_y)

    def test_ofaf_rated_rise_equals_rated(self, ofaf_model):
        """At K=1 the OFAF model must also return its rated rise."""
        rise = ofaf_model.top_oil_rise(1.0)
        assert rise == pytest.approx(ofaf_model.delta_theta_or, rel=1e-6)


# ---------------------------------------------------------------------------
# repr
# ---------------------------------------------------------------------------

def test_repr(onan_model):
    r = repr(onan_model)
    assert "ONAN" in r
    assert "55" in r
