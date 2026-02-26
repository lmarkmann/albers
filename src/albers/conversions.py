"""Color conversion utilities and perceptual metrics.

CIELAB is used for perceptual distance because it approximates how the
eye actually weighs differences — closer to Albers' lived experience of
color than the raw numbers of RGB.
"""

import colorsys
import math


def hex_to_rgb(hex_color: str) -> tuple[int, int, int] | None:
    """Parse hex color string to (r, g, b). Returns None for invalid input."""
    if not hex_color or not isinstance(hex_color, str):
        return None
    h = hex_color.lstrip("#")
    if len(h) == 8:
        h = h[:6]  # strip alpha
    if len(h) != 6:
        return None
    try:
        return (int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16))
    except ValueError:
        return None


def rgb_to_hex(r: int, g: int, b: int) -> str:
    """Convert RGB to a lowercase hex string like #ff5500."""
    return f"#{r:02x}{g:02x}{b:02x}"


def rgb_to_hsl(r: int, g: int, b: int) -> tuple[float, float, float]:
    """Convert RGB (0-255) to HSL (H: 0-360, S: 0-100, L: 0-100)."""
    h, lightness, s = colorsys.rgb_to_hls(r / 255, g / 255, b / 255)
    return (h * 360, s * 100, lightness * 100)


def hsl_to_rgb(h: float, s: float, l: float) -> tuple[int, int, int]:
    """Convert HSL (H: 0-360, S: 0-100, L: 0-100) to RGB (0-255)."""
    h_norm = h / 360
    s_norm = s / 100
    l_norm = l / 100
    r, g, b = colorsys.hls_to_rgb(h_norm, l_norm, s_norm)
    return (int(round(r * 255)), int(round(g * 255)), int(round(b * 255)))


def rgb_to_lab(r: int, g: int, b: int) -> tuple[float, float, float]:
    """Convert RGB to CIELAB for perceptual distance calculations."""

    # sRGB -> linear
    def linearize(c):
        c = c / 255
        return c / 12.92 if c <= 0.04045 else ((c + 0.055) / 1.055) ** 2.4

    rl, gl, bl = linearize(r), linearize(g), linearize(b)

    # linear RGB -> XYZ (D65)
    x = rl * 0.4124564 + gl * 0.3575761 + bl * 0.1804375
    y = rl * 0.2126729 + gl * 0.7151522 + bl * 0.0721750
    z = rl * 0.0193339 + gl * 0.1191920 + bl * 0.9503041

    # XYZ -> Lab
    xn, yn, zn = 0.95047, 1.0, 1.08883

    def f(t):
        return t ** (1 / 3) if t > 0.008856 else 7.787 * t + 16 / 116

    fx, fy, fz = f(x / xn), f(y / yn), f(z / zn)
    lab_l = 116 * fy - 16
    a = 500 * (fx - fy)
    b_val = 200 * (fy - fz)
    return (lab_l, a, b_val)


def delta_e_76(lab1, lab2) -> float:
    """CIE76 color difference (simple Euclidean in Lab space)."""
    return math.sqrt(sum((a - b) ** 2 for a, b in zip(lab1, lab2, strict=True)))


def delta_e_2000(
    lab1,
    lab2,
    k_L: float = 1.0,
    k_C: float = 1.0,
    k_H: float = 1.0,
) -> float:
    """CIEDE2000 color difference (Sharma, Wu & Dalal 2005)."""
    L1, a1, b1 = lab1
    L2, a2, b2 = lab2

    # Step 1: compute C'ab and h'ab
    C1 = math.sqrt(a1**2 + b1**2)
    C2 = math.sqrt(a2**2 + b2**2)
    C_avg = (C1 + C2) / 2.0
    C_avg7 = C_avg**7
    G = 0.5 * (1.0 - math.sqrt(C_avg7 / (C_avg7 + 25.0**7)))

    a1p = a1 * (1.0 + G)
    a2p = a2 * (1.0 + G)

    C1p = math.sqrt(a1p**2 + b1**2)
    C2p = math.sqrt(a2p**2 + b2**2)

    h1p = math.degrees(math.atan2(b1, a1p)) % 360
    h2p = math.degrees(math.atan2(b2, a2p)) % 360

    # Step 2: compute delta values
    dLp = L2 - L1
    dCp = C2p - C1p

    if C1p * C2p == 0:
        dhp = 0.0
    elif abs(h2p - h1p) <= 180:
        dhp = h2p - h1p
    elif h2p - h1p > 180:
        dhp = h2p - h1p - 360
    else:
        dhp = h2p - h1p + 360

    dHp = 2.0 * math.sqrt(C1p * C2p) * math.sin(math.radians(dhp / 2.0))

    # Step 3: weighting functions
    Lp_avg = (L1 + L2) / 2.0
    Cp_avg = (C1p + C2p) / 2.0

    if C1p * C2p == 0:
        hp_avg = h1p + h2p
    elif abs(h1p - h2p) <= 180:
        hp_avg = (h1p + h2p) / 2.0
    elif h1p + h2p < 360:
        hp_avg = (h1p + h2p + 360) / 2.0
    else:
        hp_avg = (h1p + h2p - 360) / 2.0

    T = (
        1.0
        - 0.17 * math.cos(math.radians(hp_avg - 30))
        + 0.24 * math.cos(math.radians(2 * hp_avg))
        + 0.32 * math.cos(math.radians(3 * hp_avg + 6))
        - 0.20 * math.cos(math.radians(4 * hp_avg - 63))
    )

    S_L = 1.0 + 0.015 * (Lp_avg - 50) ** 2 / math.sqrt(
        20 + (Lp_avg - 50) ** 2
    )
    S_C = 1.0 + 0.045 * Cp_avg
    S_H = 1.0 + 0.015 * Cp_avg * T

    Cp_avg7 = Cp_avg**7
    R_C = 2.0 * math.sqrt(Cp_avg7 / (Cp_avg7 + 25.0**7))
    d_theta = 30 * math.exp(-(((hp_avg - 275) / 25) ** 2))
    R_T = -math.sin(math.radians(2 * d_theta)) * R_C

    return math.sqrt(
        (dLp / (k_L * S_L)) ** 2
        + (dCp / (k_C * S_C)) ** 2
        + (dHp / (k_H * S_H)) ** 2
        + R_T * (dCp / (k_C * S_C)) * (dHp / (k_H * S_H))
    )


def relative_luminance(r: int, g: int, b: int) -> float:
    """WCAG relative luminance."""

    def lin(c):
        c = c / 255
        return c / 12.92 if c <= 0.04045 else ((c + 0.055) / 1.055) ** 2.4

    return 0.2126 * lin(r) + 0.7151 * lin(g) + 0.0722 * lin(b)


def contrast_ratio(rgb1, rgb2) -> float:
    """WCAG contrast ratio between two RGB tuples."""
    l1 = relative_luminance(*rgb1)
    l2 = relative_luminance(*rgb2)
    lighter = max(l1, l2)
    darker = min(l1, l2)
    return (lighter + 0.05) / (darker + 0.05)


def color_temperature(h: float, s: float) -> str:
    """Classify color temperature from HSL hue."""
    if s < 5:
        return "neutral"
    if 0 <= h < 60 or 300 <= h <= 360:
        return "warm"
    if 150 <= h < 270:
        return "cool"
    return "transitional"


def get_contrast_category(ratio: float) -> str:
    """Get WCAG compliance category for contrast ratio."""
    if ratio >= 7.0:
        return "AAA"
    elif ratio >= 4.5:
        return "AA"
    elif ratio >= 3.0:
        return "AA Large"
    else:
        return "Fail"


def is_color_dark(hex_color: str) -> bool:
    """Determine if a color is dark based on luminance."""
    rgb = hex_to_rgb(hex_color)
    if rgb is None:
        return False
    luminance = relative_luminance(*rgb)
    return luminance < 0.5


def get_text_color_for_background(bg_hex: str) -> str:
    """Get appropriate text color (black or white) for a background."""
    if is_color_dark(bg_hex):
        return "#ffffff"
    return "#000000"


def swatch_text_color(hex_color: str) -> str:
    """Return black or white for readable text on the given background color."""
    h = hex_color.lstrip("#")[:6]
    luminance = (
        0.2126 * int(h[0:2], 16)
        + 0.7151 * int(h[2:4], 16)
        + 0.0722 * int(h[4:6], 16)
    ) / 255
    return "#000000" if luminance > 0.5 else "#ffffff"


def rotate_hue(h: float, degrees: float) -> float:
    """Rotate hue by given degrees, wrapping around 360."""
    return (h + degrees) % 360


def generate_harmony_colors(h: float, s: float, l: float, harmony_type: str) -> list[tuple[float, float, float]]:
    """Generate harmony colors based on type."""
    harmonies = []

    if harmony_type in ("complementary", "all"):
        harmonies.append((rotate_hue(h, 180), s, l))

    if harmony_type in ("analogous", "all"):
        harmonies.append((rotate_hue(h, -30), s, l))
        harmonies.append((rotate_hue(h, 30), s, l))

    if harmony_type in ("triadic", "all"):
        harmonies.append((rotate_hue(h, 120), s, l))
        harmonies.append((rotate_hue(h, 240), s, l))

    if harmony_type in ("split", "all"):
        harmonies.append((rotate_hue(h, 150), s, l))
        harmonies.append((rotate_hue(h, 210), s, l))

    if harmony_type in ("tetradic", "all"):
        harmonies.append((rotate_hue(h, 90), s, l))
        harmonies.append((rotate_hue(h, 180), s, l))
        harmonies.append((rotate_hue(h, 270), s, l))

    return harmonies
