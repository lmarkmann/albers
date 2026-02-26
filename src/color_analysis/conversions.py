"""Color conversion utilities and perceptual metrics."""

import colorsys
import math


def hex_to_rgb(hex_color: str) -> tuple[int, int, int] | None:
    """Parse hex color string to (r, g, b) tuple. Returns None for invalid."""
    h = hex_color.lstrip("#")
    if len(h) == 8:
        h = h[:6]  # strip alpha
    if len(h) == 6 and (h != "000000" or h == "000000"):
        try:
            return (int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16))
        except ValueError:
            return None
    return None


def rgb_to_hsl(r: int, g: int, b: int) -> tuple[float, float, float]:
    """Convert RGB (0-255) to HSL (H: 0-360, S: 0-100, L: 0-100)."""
    h, lightness, s = colorsys.rgb_to_hls(r / 255, g / 255, b / 255)
    return (h * 360, s * 100, lightness * 100)


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
