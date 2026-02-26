"""Tests for albers.harmony."""

import pytest

from albers.harmony import analyze_harmony


class TestAnalyzeHarmony:
    def test_single_hue_monochromatic(self):
        result = analyze_harmony([120.0])
        assert result == {"type": "monochromatic"}

    def test_empty_monochromatic(self):
        result = analyze_harmony([])
        assert result == {"type": "monochromatic"}

    def test_returns_expected_keys(self):
        result = analyze_harmony([0.0, 180.0])
        assert "distinct_hues" in result
        assert "hue_values" in result
        assert "hue_range" in result
        assert "relationships" in result

    def test_complementary_detected(self):
        # 0 and 180 are complementary (diff = 180)
        result = analyze_harmony([0.0, 180.0])
        types = [r[0] for r in result["relationships"]]
        assert "complementary" in types

    def test_analogous_detected(self):
        # 30-degree separation is analogous
        result = analyze_harmony([100.0, 130.0])
        types = [r[0] for r in result["relationships"]]
        assert "analogous" in types

    def test_distinct_hues_count(self):
        result = analyze_harmony([0.0, 120.0, 240.0])
        assert result["distinct_hues"] == 3

    def test_deduplicates_hues(self):
        # 100.0 and 100.5 both round to 100 → single hue → monochromatic
        result = analyze_harmony([100.0, 100.0, 100.5])
        assert result == {"type": "monochromatic"}

    def test_hue_range_correct(self):
        result = analyze_harmony([50.0, 200.0])
        assert result["hue_range"] == pytest.approx(150.0, abs=1)

    def test_patina_palette_hues(self):
        # Representative Patina hues: green, olive, teal, amber, salmon
        patina_hues = [155.0, 94.0, 181.0, 36.0, 11.0]
        result = analyze_harmony(patina_hues)
        assert result["distinct_hues"] >= 4
        assert len(result["relationships"]) > 0

    def test_no_relationship_for_far_apart_non_complementary(self):
        # 0 and 90 — no standard harmony label
        result = analyze_harmony([0.0, 90.0])
        types = [r[0] for r in result["relationships"]]
        assert "complementary" not in types
        assert "analogous" not in types
