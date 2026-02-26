"""Color harmony relationship analysis.

Albers observed that colors placed next to each other create relationships
the eye cannot ignore. This module names those relationships.
"""


def analyze_harmony(hues: list[float]) -> dict:
    """Detect color harmony relationships among a set of hues."""
    hues = sorted(set(round(h) for h in hues if h is not None))
    if len(hues) < 2:
        return {"type": "monochromatic"}

    relationships = []
    for i, h1 in enumerate(hues):
        for h2 in hues[i + 1 :]:
            diff = abs(h1 - h2)
            if diff > 180:
                diff = 360 - diff
            if 165 <= diff <= 195:
                relationships.append(("complementary", h1, h2, diff))
            elif 25 <= diff <= 45:
                relationships.append(("analogous", h1, h2, diff))
            elif 115 <= diff <= 135:
                relationships.append(("triadic-ish", h1, h2, diff))
            elif 55 <= diff <= 75:
                relationships.append(("split-complementary element", h1, h2, diff))
            elif 85 <= diff <= 95:
                relationships.append(("square/tetradic element", h1, h2, diff))

    return {
        "distinct_hues": len(hues),
        "hue_values": hues,
        "hue_range": max(hues) - min(hues) if hues else 0,
        "relationships": relationships,
    }
