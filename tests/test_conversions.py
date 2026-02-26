"""Tests for albers.conversions."""

import math

import pytest

from albers.conversions import (
    color_temperature,
    contrast_ratio,
    delta_e_76,
    hex_to_rgb,
    relative_luminance,
    rgb_to_hsl,
    rgb_to_lab,
)


class TestHexToRgb:
    def test_basic_hex(self):
        assert hex_to_rgb("#ff0000") == (255, 0, 0)

    def test_no_hash(self):
        assert hex_to_rgb("00ff00") == (0, 255, 0)

    def test_black(self):
        assert hex_to_rgb("#000000") == (0, 0, 0)

    def test_white(self):
        assert hex_to_rgb("#ffffff") == (255, 255, 255)

    def test_strips_alpha(self):
        assert hex_to_rgb("#ff0000ff") == (255, 0, 0)

    def test_patina_keyword_green(self):
        assert hex_to_rgb("#4d9375") == (77, 147, 117)

    def test_patina_teal(self):
        assert hex_to_rgb("#5da9a7") == (93, 169, 167)

    def test_invalid_returns_none(self):
        assert hex_to_rgb("zzzzzz") is None

    def test_too_short_returns_none(self):
        assert hex_to_rgb("#fff") is None

    def test_uppercase(self):
        assert hex_to_rgb("#FF0000") == (255, 0, 0)


class TestRgbToHsl:
    def test_red(self):
        h, s, l = rgb_to_hsl(255, 0, 0)
        assert abs(h - 0.0) < 1 or abs(h - 360.0) < 1
        assert abs(s - 100.0) < 1
        assert abs(l - 50.0) < 1

    def test_black(self):
        h, s, l = rgb_to_hsl(0, 0, 0)
        assert abs(l - 0.0) < 1

    def test_white(self):
        h, s, l = rgb_to_hsl(255, 255, 255)
        assert abs(l - 100.0) < 1

    def test_patina_keyword_green(self):
        h, s, l = rgb_to_hsl(77, 147, 117)
        assert 140 < h < 165
        assert s > 20
        assert 35 < l < 55

    def test_returns_tuple_of_three(self):
        result = rgb_to_hsl(128, 128, 128)
        assert len(result) == 3


class TestRgbToLab:
    def test_black(self):
        l, a, b = rgb_to_lab(0, 0, 0)
        assert abs(l) < 1

    def test_white(self):
        l, a, b = rgb_to_lab(255, 255, 255)
        assert abs(l - 100) < 1

    def test_returns_tuple_of_three(self):
        result = rgb_to_lab(128, 64, 200)
        assert len(result) == 3

    def test_values_are_finite(self):
        l, a, b = rgb_to_lab(77, 147, 117)
        assert math.isfinite(l)
        assert math.isfinite(a)
        assert math.isfinite(b)


class TestDeltaE76:
    def test_identical_colors_zero(self):
        lab = (50.0, 10.0, -5.0)
        assert delta_e_76(lab, lab) == pytest.approx(0.0)

    def test_black_vs_white(self):
        black = rgb_to_lab(0, 0, 0)
        white = rgb_to_lab(255, 255, 255)
        de = delta_e_76(black, white)
        assert de > 90

    def test_similar_colors_small(self):
        lab1 = rgb_to_lab(100, 100, 100)
        lab2 = rgb_to_lab(101, 101, 101)
        assert delta_e_76(lab1, lab2) < 2

    def test_symmetric(self):
        lab1 = rgb_to_lab(255, 0, 0)
        lab2 = rgb_to_lab(0, 0, 255)
        assert delta_e_76(lab1, lab2) == pytest.approx(delta_e_76(lab2, lab1))


class TestRelativeLuminance:
    def test_black_is_zero(self):
        assert relative_luminance(0, 0, 0) == pytest.approx(0.0)

    def test_white_is_one(self):
        assert relative_luminance(255, 255, 255) == pytest.approx(1.0, abs=1e-3)

    def test_range(self):
        val = relative_luminance(77, 147, 117)
        assert 0.0 <= val <= 1.0


class TestContrastRatio:
    def test_black_on_white(self):
        cr = contrast_ratio((0, 0, 0), (255, 255, 255))
        assert cr == pytest.approx(21.0, abs=0.1)

    def test_same_color_is_one(self):
        cr = contrast_ratio((128, 128, 128), (128, 128, 128))
        assert cr == pytest.approx(1.0)

    def test_symmetric(self):
        rgb1 = (77, 147, 117)
        rgb2 = (18, 18, 18)
        assert contrast_ratio(rgb1, rgb2) == pytest.approx(
            contrast_ratio(rgb2, rgb1), abs=1e-6
        )

    def test_patina_dark_bg_foreground(self):
        # #4d9375 on #121212 — should pass WCAG AA (>= 4.5)
        cr = contrast_ratio((77, 147, 117), (18, 18, 18))
        assert cr >= 4.5


class TestColorTemperature:
    def test_warm_red(self):
        assert color_temperature(10, 80) == "warm"

    def test_cool_blue(self):
        assert color_temperature(200, 60) == "cool"

    def test_neutral_low_saturation(self):
        assert color_temperature(200, 2) == "neutral"

    def test_transitional(self):
        result = color_temperature(80, 50)
        assert result == "transitional"

    def test_warm_near_360(self):
        assert color_temperature(350, 70) == "warm"
