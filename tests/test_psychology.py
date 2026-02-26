"""Tests for albers.psychology."""

from albers.psychology import classify_emotion


class TestClassifyEmotion:
    def test_returns_dict(self):
        result = classify_emotion(155.0, 30.0, 45.0)
        assert isinstance(result, dict)

    def test_temperature_always_present(self):
        result = classify_emotion(0.0, 0.0, 50.0)
        assert "temperature" in result

    def test_cool_blue_temperature(self):
        result = classify_emotion(210.0, 60.0, 50.0)
        assert result["temperature"] == "cool"

    def test_warm_red_temperature(self):
        result = classify_emotion(10.0, 80.0, 50.0)
        assert result["temperature"] == "warm"

    def test_neutral_low_saturation(self):
        result = classify_emotion(200.0, 2.0, 50.0)
        assert result["temperature"] == "neutral"

    def test_hue_emotion_present_for_saturated(self):
        result = classify_emotion(30.0, 50.0, 50.0)
        assert "hue_emotion" in result

    def test_hue_emotion_absent_for_desaturated(self):
        # saturation < 5 skips hue emotion
        result = classify_emotion(30.0, 3.0, 50.0)
        assert "hue_emotion" not in result

    def test_lightness_class_very_dark(self):
        result = classify_emotion(155.0, 30.0, 5.0)
        assert result.get("lightness_class") == "very_dark"

    def test_lightness_class_light(self):
        result = classify_emotion(155.0, 30.0, 80.0)
        assert result.get("lightness_class") == "light"

    def test_saturation_class_muted(self):
        # Patina uses muted colors (s ~20-35)
        result = classify_emotion(155.0, 25.0, 45.0)
        assert result.get("saturation_class") == "muted"

    def test_saturation_class_desaturated(self):
        result = classify_emotion(155.0, 5.0, 45.0)
        assert result.get("saturation_class") == "desaturated"

    def test_patina_keyword_green(self):
        # #4d9375 → HSL approx (155, 31, 44)
        result = classify_emotion(155.0, 31.0, 44.0)
        assert result["temperature"] == "cool"
        assert "lightness_class" in result

    def test_arousal_present_for_saturated(self):
        result = classify_emotion(10.0, 80.0, 50.0)
        assert "arousal" in result

    def test_valence_present_for_saturated(self):
        result = classify_emotion(10.0, 80.0, 50.0)
        assert "valence" in result
