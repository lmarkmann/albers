"""Color psychology and emotional response mapping.

"One and the same color evokes innumerable readings." — Josef Albers
"""

from .conversions import color_temperature

EMOTIONAL_MAP = {
    # (hue_min, hue_max): (emotion, arousal_level, valence)
    (0, 30): ("energy, urgency, passion", "high", "mixed"),
    (30, 60): ("warmth, comfort, optimism", "medium", "positive"),
    (60, 90): ("clarity, attention, caution", "medium-high", "mixed"),
    (90, 150): ("growth, balance, freshness", "low-medium", "positive"),
    (150, 210): ("calm, trust, stability", "low", "positive"),
    (210, 270): ("depth, introspection, focus", "low-medium", "neutral"),
    (270, 330): ("creativity, luxury, mystery", "medium", "mixed"),
    (330, 360): ("energy, urgency, passion", "high", "mixed"),
}

LIGHTNESS_RESPONSE = {
    "very_dark": (0, 15, "immersion, focus, reduced eye strain in dim environments"),
    "dark": (15, 30, "concentration, professionalism, modern aesthetic"),
    "medium_dark": (30, 45, "balance, readability, moderate contrast"),
    "medium": (45, 60, "neutrality, versatility, comfortable extended use"),
    "medium_light": (60, 75, "openness, approachability, paper-like comfort"),
    "light": (75, 90, "clarity, spaciousness, traditional document feel"),
    "very_light": (90, 100, "airiness, minimalism, clean aesthetic"),
}

SATURATION_RESPONSE = {
    "desaturated": (0, 15, "calm, professional, reduces visual fatigue over time"),
    "muted": (
        15,
        35,
        "sophisticated, natural, non-distracting — ideal for long coding sessions",
    ),
    "moderate": (35, 55, "balanced, engaging without overwhelming"),
    "saturated": (55, 75, "vibrant, attention-grabbing — best reserved for accents"),
    "vivid": (75, 100, "intense, energetic — may cause fatigue if overused"),
}


def classify_emotion(h: float, s: float, lightness: float) -> dict:
    """Return emotional/psychological associations for an HSL color."""
    result = {}

    # Hue-based
    if s >= 5:
        for (hmin, hmax), (emotion, arousal, valence) in EMOTIONAL_MAP.items():
            if hmin <= h < hmax:
                result["hue_emotion"] = emotion
                result["arousal"] = arousal
                result["valence"] = valence
                break

    # Temperature
    result["temperature"] = color_temperature(h, s)

    # Lightness
    for name, (lmin, lmax, desc) in LIGHTNESS_RESPONSE.items():
        if lmin <= lightness < lmax:
            result["lightness_class"] = name
            result["lightness_response"] = desc
            break

    # Saturation
    for name, (smin, smax, desc) in SATURATION_RESPONSE.items():
        if smin <= s < smax:
            result["saturation_class"] = name
            result["saturation_response"] = desc
            break

    return result
